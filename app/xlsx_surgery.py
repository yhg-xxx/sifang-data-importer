"""xlsx XML 手术 —— 去重输出的全格式保真引擎

原理：输出 = 源 zip 的逐条目复制；唯独参与去重的 worksheet XML 走行级重写：
删除命中删除集的 <row>，其余行整体保留并把 r 属性（连同行内所有 <c r="XN">）
重排为紧凑行号。styles / sharedStrings / theme / 条件格式（「重复值标红」等）/
列宽 / 自动筛选 / 超链接 / 工作表保护 / customXml 等其余部分一律原样搬运，
源文件的一切格式在输出中分毫不差。

行号对齐（均已实测验证）：python-calamine 产出「第 1 行 ~ 最后一个含值行」
区间的所有行号——按 <row> 的 r 属性对齐，缺失的行号补空值行，含样式单元格
但无值的行产出空值行，最后一个含 <v>/<is> 值的行之后的尾部行一律截断不产出。
因此删除集中的行号（calamine 口径）就是 r 属性值，可直接查表删行；每 sheet
预扫描结束时校验「最后含值行号 == calamine 行数」，不一致立即报错作废输出，
绝不带错删行。

三遍结构（勾选去重的 sheet 两读一写，未勾选的一读 + 字节泵复制）：
  1. MODE_SCAN    预扫描：统计行数、校验对齐、拒止共享公式（不写任何输出；
                  全部 sheet 校验通过后才创建输出文件，失败则零副作用）。
                  未勾选 sheet 也走本模式取行数（不做对齐校验、不查公式）
  2. MODE_SURGERY 重写：此时重排后总行数已知，先改好 head 里的 dimension
                  再流式写行；tail 里 autoFilter 结束行 / 合并单元格 / 数据
                  验证 sqref / 超链接行号均按「原始 r → 新行号」精确映射修正，
                  范围内含被删行的合并单元格直接剔除
  3. 未勾选 sheet：预扫描已计数，写出阶段退化为纯字节泵（shutil.copyfileobj）

取消：单一公开 Cancelled 异常贯穿预扫描 / 条目 / 行三层检查点，统一携带
已完成条目的 stats 重新抛出；调用方捕获后自行作废输出文件（半去重的文件
比没有文件更危险）。

已知边界（本工具数据源不涉及）：sheet 含共享公式（下拉填充）时预扫描直接
拒止——删主行会留下悬空从行、输出被 Excel 判定损坏；普通公式行号重排不会
同步改写公式引用；表格（xl/tables）与工作簿级定义名称（打印区域等）原样
搬运不随行号平移；数据验证 sqref 中的整列/整行/$ 绝对引用不重映射。零散
单元格/带范围的条件格式规则原样保留——去重后判重列已无重复值，规则自然
休眠，整列规则（如 D$1:D$1048576）不受行号平移影响、后续新增重复仍会标红。
"""

import posixpath
import re
import shutil
import zipfile
from bisect import bisect_left

from app.excel_reader import read_sheet_entries

CHUNK = 1 << 20

MODE_SCAN = "scan"        # 预扫描：统计 + 校验，不写输出
MODE_SURGERY = "surgery"  # 删行 + 行号重排 + 尾部引用修正


class SurgeryError(Exception):
    """XML 手术无法安全进行（结构超出预期），应中止并作废输出。"""


class Cancelled(Exception):
    """用户取消：携带已完成条目的 stats（仅供展示），调用方负责作废输出文件。"""

    def __init__(self, stats: dict = None):
        super().__init__("已取消")
        self.stats = stats or {}


# ── workbook 结构解析：sheet 名 -> zip 内 worksheet XML 条目路径 ──
# sheet 名与 rId 的解析复用 excel_reader.read_sheet_entries（ElementTree，
# 正确处理属性引号与实体），避免与主窗口的 sheet 名列表各解析一套而漂移；
# 本函数只负责 rels Target → zip 条目路径的解析。
_RE_REL = re.compile(r'<Relationship\b[^>]*>')
_RE_REL_ID = re.compile(r'\bId="(rId\d+)"')
_RE_REL_TARGET = re.compile(r'\bTarget="([^"]*)"')


def sheet_xml_entries(path: str) -> dict:
    """返回 {sheet名: 'xl/worksheets/sheetN.xml'}（仅可定位 XML 的可见 sheet）。"""
    with zipfile.ZipFile(path) as z:
        rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    target = {}
    for m in _RE_REL.finditer(rels):
        tag = m.group(0)
        rid = _RE_REL_ID.search(tag)
        tg = _RE_REL_TARGET.search(tag)
        if rid and tg:
            target[rid.group(1)] = tg.group(1)
    out = {}
    for name, rid in read_sheet_entries(path):
        if not rid or rid not in target:
            continue
        t = target[rid].lstrip("/")
        if not t.startswith("xl/"):
            t = posixpath.normpath(posixpath.join("xl", t))
        out[name] = t
    return out


# ── 行级重排 ──

_ROW_R_ATTR = re.compile(rb'\br="(\d+)"')
# 预编译单正则：所有 r="X数字" 引用共用，替换回调比对行号，杜绝每行重编译
_CELL_R_REF = re.compile(rb'r="([A-Z]{0,3})(\d+)"')
_DIM_END = re.compile(rb'(<dimension\b[^>]*?\bref="[A-Za-z]{1,3}\d+:[A-Za-z]{1,3})(\d+)"')
_FILTER_END = re.compile(rb'(<autoFilter\b[^>]*?\bref="[A-Za-z]{1,3}\d+:[A-Za-z]{1,3})(\d+)"')
_RE_MERGECELL = re.compile(rb'<mergeCell\b[^>]*>')
_MERGE_REF = re.compile(rb'\bref="([A-Z]{1,3})(\d+):([A-Z]{1,3})(\d+)"')
_RE_DATAVAL_ELEM = re.compile(rb'<dataValidation\b[^>]*(?:/>|>.*?</dataValidation>)', re.S)
_SQREF_ATTR = re.compile(rb'(\bsqref=")([^"]*)(")')
_REF_TOKEN = re.compile(rb'([A-Z]{1,3})(\d+)(?::([A-Z]{1,3})(\d+))?')
_HL_ELEM = re.compile(rb'<hyperlink\b[^>]*/>|<hyperlink\b[^>]*>.*?</hyperlink>', re.S)
_HL_REF = re.compile(rb'\bref="([A-Z]{1,3})(\d+)"')
# 共享公式（<f t="shared" ...>）：先廉价子串探测，命中后再正则确认，避免误伤
_RE_SHARED_F = re.compile(rb'<f\b[^>]*\bt="shared"')


def _renumber_row(row: bytes, old: int, new: int) -> bytes:
    """把行内所有 r="X{old}"（含 <row r> 与 <c r>）的行号部分替换为 new。"""
    new_digits = str(new).encode()

    def _sub(m):
        if int(m.group(2)) == old:
            return b'r="' + m.group(1) + new_digits + b'"'
        return m.group(0)

    return _CELL_R_REF.sub(_sub, row)


def _rewrite_tail(tail: bytes, exact_map: dict, deleted: set,
                  deleted_sorted: list, written: int) -> tuple:
    """修正 </sheetData> 之后的部分：autoFilter 结束行、合并单元格（范围内含
    被删行的合并剔除）、数据验证 sqref、超链接行号；返回 (新tail, 剔除超链接数)。

    exact_map 为全部写出行的「原始 r → 新行号」精确映射，无需假设行稠密。
    """
    dropped = [0]
    max_orig = max(exact_map) if exact_map else 0

    def _new_row(orig: int) -> int:
        """旧行号 → 新行号：写出行精确映射；被删/未写出行取上方最近写出行，越界取末行。"""
        if orig in exact_map:
            return exact_map[orig]
        if not exact_map or orig > max_orig:
            return max(1, written)
        while orig not in exact_map:
            orig -= 1
        return exact_map[orig]

    def _span_deleted(r1: int, r2: int) -> bool:
        i = bisect_left(deleted_sorted, r1)
        return i < len(deleted_sorted) and deleted_sorted[i] <= r2

    def _filter_end(m):
        new_end = min(_new_row(int(m.group(2))), written)
        return m.group(1) + str(new_end).encode() + b'"'

    tail = _FILTER_END.sub(_filter_end, tail)

    def _merge(m):
        elem = m.group(0)
        rm = _MERGE_REF.search(elem)
        if not rm:
            return elem
        r1, r2 = int(rm.group(2)), int(rm.group(4))
        if _span_deleted(r1, r2):
            return b""  # 合并范围内有被删行：平移会盖住错误数据，直接剔除
        new_ref = (rm.group(1) + str(_new_row(r1)).encode() + b":"
                   + rm.group(3) + str(_new_row(r2)).encode())
        return elem[:rm.start(1)] + new_ref + elem[rm.end(4):]

    tail = _RE_MERGECELL.sub(_merge, tail)

    def _dataval(m):
        elem = m.group(0)
        sm = _SQREF_ATTR.search(elem)
        if not sm:
            return elem
        out_tokens = []
        for tok in sm.group(2).split():
            tm = _REF_TOKEN.fullmatch(tok)
            if not tm:
                out_tokens.append(tok)  # 整列/整行/$ 绝对引用等：不受行号平移影响，原样
                continue
            r1 = int(tm.group(2))
            if tm.group(4) is None:
                if r1 in deleted:
                    continue  # 单元格引用指向被删行：该引用随删行失效
                out_tokens.append(tm.group(1) + str(_new_row(r1)).encode())
            else:
                out_tokens.append(tm.group(1) + str(_new_row(r1)).encode() + b":"
                                  + tm.group(3) + str(_new_row(int(tm.group(4)))).encode())
        if not out_tokens:
            return b""  # 全部引用都指向被删行：整条验证规则随删行失效
        return elem[:sm.start(2)] + b" ".join(out_tokens) + elem[sm.end(2):]

    tail = _RE_DATAVAL_ELEM.sub(_dataval, tail)

    def _hyperlink(m):
        elem = m.group(0)
        rm = _HL_REF.search(elem)
        if not rm:
            return elem
        row = int(rm.group(2))
        if row in exact_map:
            new_digits = str(exact_map[row]).encode()
            return elem[:rm.start(2)] + new_digits + elem[rm.end(2):]
        if row in deleted:
            dropped[0] += 1
            return b""
        return elem  # 不在数据区（如指向样式空行），保留原样

    tail = _HL_ELEM.sub(_hyperlink, tail)
    return tail, dropped[0]


# ── 流式行扫描器 ──

_WS = b" \t\r\n"


class _RowScanner:
    """按 <row> 元素流式扫描 worksheet XML。

    next_row() 返回 (gap, row, old_r, has_value)：
      gap  —— 上一元素与该行之间的原文（通常为空）
      row  —— 整个 <row ...>...</row>（或自闭合 <row .../>）的原始字节
      old_r—— r 属性行号；缺失时为 None
      has_value —— 行内是否含 <v>/<is> 值（决定 calamine 的产出范围）
    sheetData 结束时返回 (gap, None, None, False)，随后用 read_tail() 取剩余。
    """

    def __init__(self, stream):
        self._s = stream
        self.buf = b""
        self.pos = 0

    def _fill(self) -> bool:
        chunk = self._s.read(CHUNK)
        if not chunk:
            return False
        self.buf = self.buf[self.pos:] + chunk
        self.pos = 0
        return True

    def read_head(self) -> tuple:
        """读到 <sheetData> 开标签为止；返回 (head字节, sheetData是否为空<sheetData/>)。"""
        while True:
            i = self.buf.find(b"<sheetData", self.pos)
            if i < 0:
                if self._fill():
                    continue
                raise SurgeryError("worksheet XML 中找不到 <sheetData>")
            gt = self.buf.find(b">", i)
            if gt < 0 or len(self.buf) - i < 32:
                if self._fill():
                    continue
                raise SurgeryError("<sheetData> 标签不完整")
            empty = self.buf[gt - 1:gt] == b"/"
            head = self.buf[:gt + 1]
            self.pos = gt + 1
            return head, empty

    def next_row(self):
        while True:
            b = self.buf
            p = self.pos
            q = p
            n = len(b)
            while q < n and b[q] in _WS:
                q += 1
            # 剩余不足一个完整标记时先补块再重试（防止半截标签误判）
            if q >= n or n - q < 16:
                if self._fill():
                    continue
                if q >= n:
                    raise SurgeryError("流在 sheetData 内意外结束")
            tag = b[q:q + 12]
            if tag.startswith(b"</sheetData"):
                gt = b.find(b">", q)
                if gt < 0:
                    if self._fill():
                        continue
                    raise SurgeryError("</sheetData> 不完整")
                gap = b[p:q]
                # pos 回退到闭合标签起点，让 </sheetData> 成为 tail 的一部分被写出
                self.pos = q
                return gap, None, None, False
            t4 = tag[4:5] if tag.startswith(b"<row") else b""
            # <row 后允许任意 XML 空白（换行/制表符分隔属性的第三方导出器合法）
            if not t4 or not (t4 in (b">", b"/", b"") or t4.isspace()):
                raise SurgeryError(f"sheetData 内出现未知元素: {b[q:q + 40]!r}")
            gt = b.find(b">", q)
            if gt < 0:
                if self._fill():
                    continue
                raise SurgeryError("<row> 开标签不完整")
            if b[gt - 1:gt] == b"/":
                end = gt + 1
            else:
                et = b.find(b"</row>", gt)
                if et < 0:
                    if self._fill():
                        continue
                    raise SurgeryError("<row> 元素未闭合")
                end = et + 6
            gap = b[p:q]
            row = b[q:end]
            m = _ROW_R_ATTR.search(row, 0, row.find(b">") + 1)
            has_value = b"<v>" in row or b"<is>" in row
            self.pos = end
            return gap, row, (int(m.group(1)) if m else None), has_value

    def read_tail(self) -> bytes:
        """</sheetData> 之后的全部剩余字节（hyperlinks/pageMargins 等，通常很小）。

        直接按块读取拼接（线性），不经 _fill 的「余量 + 新块」缓冲拼接。
        """
        parts = [self.buf[self.pos:]]
        while True:
            chunk = self._s.read(CHUNK)
            if not chunk:
                break
            parts.append(chunk)
        self.buf = b""
        self.pos = 0
        return b"".join(parts)


# ── 单 sheet 处理 ──

def _process_sheet(stream, out, mode, *, deleted=None, expected=None,
                   total_written=None, refuse_shared=False,
                   cancel_check=None) -> dict:
    """按 mode 扫描/重写一个 worksheet XML。

    MODE_SCAN:    out 必须为 None；返回 {calamine_rows, physical}，并在
                  calamine_rows != expected（expected 非 None 时）抛 SurgeryError
                  （对齐校验）；refuse_shared 时检出共享公式即抛 SurgeryError。
    MODE_SURGERY: out 为输出流；按 deleted（r 属性行号集 = calamine 口径）删行并重排。
    """
    sc = _RowScanner(stream)
    head, empty = sc.read_head()
    if out is not None and mode == MODE_SURGERY:
        if total_written is None:
            raise SurgeryError("内部错误：surgery 模式缺少 total_written")
        head = _DIM_END.sub(
            lambda m: m.group(1) + str(total_written).encode() + b'"', head)
    if out is not None:
        out.write(head)

    last_value_row = 0  # 最后一个含值行的 r（= calamine 产出行数，含表头）
    physical = 0        # 物理行元素总数（含纯样式空行）
    written = 0         # 写出的物理行数
    deleted_count = 0
    deleted_orig = []   # 被删行的原始 r（升序）
    exact_map = {}      # 全部写出行：原始 r -> 新行号（尾部引用统一精确重映射）

    while not empty:
        if cancel_check and physical % 4096 == 0 and cancel_check():
            raise Cancelled()
        gap, row, old_r, has_value = sc.next_row()
        if row is None:
            break
        physical += 1
        if has_value and old_r is not None and old_r > last_value_row:
            last_value_row = old_r
        if mode == MODE_SCAN:
            if refuse_shared and b't="shared"' in row and _RE_SHARED_F.search(row):
                raise SurgeryError(
                    "sheet 含共享公式（下拉填充），删行会使输出文件被 Excel 判定损坏，"
                    "已中止；请先去除公式或不对该 Sheet 去重")
            continue
        drop = deleted is not None and old_r in deleted
        if drop:
            deleted_count += 1
            if old_r is not None:
                deleted_orig.append(old_r)
            continue
        written += 1
        if old_r is None:
            raise SurgeryError("行缺少 r 属性，无法重排行号")
        exact_map[old_r] = written
        if written != old_r:
            row = _renumber_row(row, old_r, written)
        out.write(row)

    tail = sc.read_tail()

    if mode == MODE_SCAN:
        if expected is not None and last_value_row != expected:
            raise SurgeryError(
                f"XML 最后含值行号（{last_value_row}）与数据读取行数（{expected}）不一致，"
                f"为避免错删行已中止")
        return {"calamine_rows": last_value_row, "physical": physical}

    # MODE_SURGERY
    tail, hl_dropped = _rewrite_tail(tail, exact_map, set(deleted_orig),
                                     deleted_orig, written)
    out.write(tail)
    return {"calamine_rows": last_value_row, "physical": physical, "written": written,
            "deleted": deleted_count, "hyperlinks_dropped": hl_dropped}


# ── 整簿重写 ──

def _copy_zinfo(info: zipfile.ZipInfo) -> zipfile.ZipInfo:
    """基于源条目建可写的 ZipInfo（压缩方式统一 DEFLATED，展示性字段沿用）。"""
    zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = info.external_attr
    zi.internal_attr = info.internal_attr
    zi.create_system = info.create_system
    return zi


def rewrite_workbook(src_path: str, out_path: str, surgery_targets: dict,
                     count_entries=(), entry_names=None,
                     progress_callback=None, cancel_check=None) -> dict:
    """把 src_path 重写为 out_path：勾选去重的 sheet 行级手术，其余条目原样复制。

    参数:
        surgery_targets: {entry: (删除行号集合, calamine有值行数)}
        count_entries:   需要统计行数的原样复制条目（未勾选去重的 sheet）
        entry_names:     {entry: sheet显示名}（进度消息与报错定位用）
    返回:
        stats: {entry: _process_sheet 的返回 dict}
    用户取消时抛 Cancelled（stats 携带已完成条目，仅供展示）；输出文件为不完整
    半成品，调用方负责删除（作废语义）。
    """
    stats = {}
    entry_names = entry_names or {}
    with zipfile.ZipFile(src_path) as zin:
        names = set(zin.namelist())
        for entry in surgery_targets:
            if entry not in names:
                raise SurgeryError(f"zip 中找不到条目 {entry}")
        count_set = set(count_entries) - set(surgery_targets)

        report_total = len(surgery_targets) + len(count_set)
        # 进度前半为预扫描、后半为写出；调用方在此基础上叠加 Pass 1 扫描段偏移，
        # 使全程进度单调不回跳
        try:
            # ── 预扫描：全部校验通过后才创建输出文件（失败/取消零副作用）──
            pre = {}
            pre_list = list(surgery_targets) + sorted(count_set)
            for j, entry in enumerate(pre_list):
                if cancel_check and cancel_check():
                    raise Cancelled(stats)
                name = entry_names.get(entry, entry)
                if progress_callback:
                    progress_callback(j, report_total * 2, f"正在校验: {name}")
                with zin.open(entry) as s:
                    try:
                        pre[entry] = _process_sheet(
                            s, None, MODE_SCAN,
                            expected=(surgery_targets[entry][1]
                                      if entry in surgery_targets else None),
                            refuse_shared=entry in surgery_targets,
                            cancel_check=cancel_check)
                    except SurgeryError as e:
                        raise SurgeryError(f"{name}: {e}") from None

            # ── 写出：手术条目行级重写；计数条目纯字节泵；其余条目原样搬运 ──
            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
                report_i = 0
                for info in zin.infolist():
                    if cancel_check and cancel_check():
                        raise Cancelled(stats)
                    zi = _copy_zinfo(info)
                    if info.filename in surgery_targets:
                        deleted, _expected = surgery_targets[info.filename]
                        scan = pre[info.filename]
                        name = entry_names.get(info.filename, info.filename)
                        if progress_callback:
                            progress_callback(report_total + report_i, report_total * 2,
                                              f"正在去重: {name}")
                        with zin.open(info) as s, zout.open(zi, "w") as d:
                            st = _process_sheet(
                                s, d, MODE_SURGERY, deleted=deleted,
                                total_written=scan["physical"] - len(deleted),
                                cancel_check=cancel_check)
                        stats[info.filename] = st
                        report_i += 1
                        if progress_callback:
                            rows = max(0, st["calamine_rows"] - 1)
                            progress_callback(
                                report_total + report_i, report_total * 2,
                                f"{name}: 共 {rows} 行，删除 {st['deleted']} 行，"
                                f"保留 {rows - st['deleted']} 行")
                    elif info.filename in count_set:
                        name = entry_names.get(info.filename, info.filename)
                        if progress_callback:
                            progress_callback(report_total + report_i, report_total * 2,
                                              f"正在复制: {name}")
                        with zin.open(info) as s, zout.open(zi, "w") as d:
                            shutil.copyfileobj(s, d, CHUNK)
                        stats[info.filename] = pre[info.filename]
                        report_i += 1
                        if progress_callback:
                            progress_callback(
                                report_total + report_i, report_total * 2,
                                f"{name}: 原样复制 "
                                f"{max(0, pre[info.filename]['calamine_rows'] - 1)} 行")
                    elif info.is_dir():
                        zout.writestr(zi, b"")
                    else:
                        with zin.open(info) as s, zout.open(zi, "w") as d:
                            shutil.copyfileobj(s, d, CHUNK)
        except Cancelled:
            raise Cancelled(stats) from None
    return stats
