# 四方信息源入库

> 将 Excel 文件中 40+ 个 Sheet（当前 46 个）的数据批量导入 SQL Server 的桌面工具。

---

## 项目概述

### 产品定位

将 Excel 文件中 40+ 个 Sheet 的数据批量导入 SQL Server 的桌面工具。每个 Sheet 映射为一张表，每次导入全量覆盖（先删后插）。面向内部少量用户：启动时后台自动尝试上次使用的连接（失败则打开连接管理），连接成功后选择文件、去重、导入。

### 项目文件说明

| 文件 | 说明 |
|---|---|
| `信息源*.xlsx` | 数据源 Excel 文件，当前 46 个 Sheet，每个 Sheet 对应一个行业分类的企业数据（运行时由用户选择，不打包进 exe） |
| `数据规范.png` | 数据规范参考图（人工查看用，程序不引用） |
| `每周入库流程.html` | 每周例行操作说明（人工查看用，程序不引用） |
| `sheet_names.txt` | 初始 Sheet 名称列表，共 46 个（首次启动播种到 SQLite） |
| `local.db` | 本地 SQLite（首次启动自动生成），含 `db_connections`（多连接配置 / 登录）、`sheet_names`（Sheet→表名映射 + 导入时间 + 失败状态）、`column_mapping`（Excel 列→DB 字段）、`dedup_settings`（去重模式与判重列）四张表 |
| `create_all_tables.sql` | 46 张表的建表 DDL（GB2312 编码），表名 `enterprise_info_001~046` |
| `import_log.txt` | 运行时生成的导入 / 去重日志（超过 1MB 自动轮转为 `.bak`） |
| `assets/icon.png` | 托盘 / 窗口图标源文件（运行时居中裁方 + 圆角遮罩，多尺寸 16~256） |
| `assets/icon.ico` | exe 文件图标（圆角多尺寸） |
| `assets/icon_rounded_256.png` | 圆角图标预览图 |
| `requirements.txt` | Python 依赖（PySide6 / python-calamine / pyodbc / PyInstaller / xlsxwriter） |
| `build.spec` | PyInstaller 打包配置 |

---

## 核心功能

### 功能清单

- 启动后自动尝试上次使用的数据库连接（后台线程 + 「正在连接…」遮罩，不阻塞 GUI）；失败则打开连接管理对话框，可保存多条连接、新增 / 删除、测试连接，连接成功后方可进入主窗口
- 用户手动选择 `.xlsx` 文件，程序后台线程秒级读取全部 Sheet 名称（zipfile 解析 `xl/workbook.xml`），概览显示序号、名称与最后导入时间；读取期间显示已用时
- Sheet 概览默认全选，支持逐行勾选、先点起始行再 Shift 点击结束行批量勾选、底部「全选」一键切换，并显示「已选 X/Y」
- 导出 / 验证前拦截两类映射问题：Sheet 在本地映射中缺失；多个 Sheet 映射到同一张表（同时导入会被后导入的覆盖）
- 导入前检查本次勾选的表是否全部存在，任一缺失则终止并提示执行 `create_all_tables.sql`
- 按 Sheet 名称匹配数据库表，批量写入 SQL Server（每批 5000 行，`fast_executemany`）
- 每次导入逐表独立事务：先清空目标表（DELETE，兼容无 TRUNCATE 权限环境），再重新插入全部数据
- 导入失败不中断：某 Sheet 导入失败时仅回滚该表、自动跳过并继续导入后续表，全部表处理完后汇总「成功 X / 失败 Y」；仅连接断开等基础设施错误（`SELECT 1` 探活判定）中止整个流程
- 导入内建逐批预检：NOT NULL（`company_name`、`industry`）、日期格式、字段长度；坏行在整个 Sheet 扫描完后判失败，批量插入失败时自动降级逐行诊断，定位到 Sheet、Excel 行号、列名与当前值
- 有失败表时自动在源文件同目录生成「源文件名__导入错误名单_时间戳.xlsx」（永不覆盖）：「汇总」页按负责人统计错误行数与出错行区间（可直接复制进群催办），「明细」页列出 Sheet、Excel 行号、列名、当前值、问题描述、负责人，可筛选
- 失败表按表名持久化记忆（`sheet_names.last_import_status`）：主窗口概览标红提示；加载新文件（如业务修正后的定稿文件）时自动提示「只勾选上次失败的 Sheet」一键补录
- 每周例行流程使用内置去重（默认全局模式、判重列 D 企业名称），外部去重工具退役
- 点击「开始去重」可对勾选的 Sheet 去重（未勾选的 Sheet 原样复制进输出文件）：支持「按 Sheet 内去重 / 全局去重」两种模式与判重列下拉自选，设置持久化到本地 SQLite
- 判重键 = 判重列值去首尾空白并全角转半角；判重键为空或录入时间不可解析的行不参与判重、原样保留；同一判重键保留录入时间最早者（平手保留首次出现），整行删除其余重复行
- 去重输出为源文件的全格式保真副本（单元格样式、条件格式、列宽、超链接、自动筛选、保护等原样保留），仅删除重复行并紧凑重排行号；同时生成「重复清单__原名_已去重.csv」对照清单
- 去重输出永不覆盖任何已有文件（目标已存在自动加时间戳）；中途取消作废整个输出文件；成功后主窗口自动切换到输出文件，可直接「开始导入」
- 点击「验证数据」可做离线校验（NOT NULL、字段长度、日期格式），一次性找出所有错误并以可筛选表格展示，不写数据库；为可选排查工具，不在每周例行流程中
- 数据库 / ODBC 原始报错经 `error_msgs.humanize_db_error` 翻译为中文提示；所有错误统一弹窗并附带联系信息（`ERROR_CONTACT`）
- 记录导入 / 去重日志（开始 / 结束时间、状态、各表行数、失败表明细、错误名单路径），超 1MB 自动轮转，多实例写入加文件锁
- 系统托盘驻留：关窗询问「直接退出（默认）/ 最小化到托盘」；托盘菜单「显示主窗口 / 退出」，双击图标恢复；任务运行中拒绝退出；托盘不可用时退化为关窗即退出
- 统一亮色主题（`ui/theme.py`）与顶部居中堆叠的 Toast 轻提示（`ui/toast.py`）；内置「使用说明」窗口（目录胶囊跳转）
- 支持「Sheet名-表映射」的增删改查、搜索筛选与批量替换；「列映射」只读展示 11 条约束
- 打包为可运行的 .exe 文件

### 范围外功能（不做）

- 不做增量导入、数据对比或数据清洗
- 不做用户登录验证和权限管理
- 不做 Web 版本或 API
- 不做数据报表或可视化
- 不做 Excel → DB 字段映射的在线编辑（「列映射」只读展示，按固定结构处理）

---

## 技术架构

### 技术栈

| 层 | 技术 |
|---|---|
| 语言 | Python 3.13+（当前开发环境 3.13.2） |
| 桌面 GUI | PySide6 6.11.1（Qt for Python） |
| Excel 读取 | python-calamine 0.8.2（Rust 解析器，数据读取）+ zipfile（Sheet 名与 XML 条目定位） |
| Excel 写出 | 去重输出：XML 手术（zipfile 逐条目复制 + worksheet XML 流式重写，全格式保真）；错误名单：xlsxwriter 3.2.9 |
| 远程数据库驱动 | pyodbc 5.3.0（SQL Server，ODBC Driver 17） |
| 本地数据库 | SQLite（sqlite3 标准库），存储连接配置、映射、列映射与去重设置 |
| 打包分发 | PyInstaller 6.21.0（单文件 exe，windowed） |

### 目录结构

```
sifang-data-importer/
├── main.py                      # 应用入口：本地库初始化、主题、托盘、自动连接、连接管理循环
├── app/                         # 业务逻辑层
│   ├── __init__.py
│   ├── config.py                # 连接配置读写（转调 local_db）
│   ├── constants.py             # 全局常量（统一错误联系信息 ERROR_CONTACT）
│   ├── local_db.py              # 本地 SQLite（建表、迁移、播种、连接/映射/设置的 CRUD）
│   ├── database.py              # SQL Server 连接、表检查、批量插入、批量 COUNT、清空
│   ├── dedup.py                 # 数据去重（扫描定保留行 + XML 手术写出 + 重复清单 CSV）
│   ├── xlsx_surgery.py          # xlsx XML 手术引擎（行级删行/重排 + 尾部引用修正）
│   ├── error_list.py            # 导入错误名单生成（汇总 + 明细双 Sheet xlsx）
│   ├── error_msgs.py            # 数据库 / ODBC 报错中文化
│   ├── date_utils.py            # 日期归一化与解析（验证与导入共用）
│   ├── excel_reader.py          # zipfile 读 Sheet 名 + calamine 流式分批读数据
│   ├── importer.py              # 导入编排器（逐表事务、预检、错误收集、名单与日志）
│   ├── validator.py             # 离线数据验证（NOT NULL、长度、日期）
│   ├── utils.py                 # 列字母、行号区间合并、判重键规范化、时间戳命名
│   └── logger.py                # 导入 / 去重日志（1MB 轮转、多实例文件锁）
├── ui/                          # 界面层（PySide6）
│   ├── __init__.py
│   ├── main_window.py           # 主窗口：文件选择、Sheet 概览、失败红标、去重/验证/导入入口
│   ├── base_task_dialog.py      # 任务进度对话框基类
│   ├── connection_dialog.py     # 数据库连接管理（多连接列表、测试/连接）
│   ├── import_dialog.py         # 导入进度/结果（含「打开错误名单」）
│   ├── validate_dialog.py       # 验证进度/结果（错误表格 + 类型筛选）
│   ├── dedup_settings_dialog.py # 去重设置（模式/判重列，摘要兼确认）
│   ├── dedup_dialog.py          # 去重进度/结果（支持取消）
│   ├── confirm_dialog.py        # 导入/验证前的映射确认
│   ├── sheet_directory_dialog.py# Sheet名-表映射管理（搜索/编辑/新增/删除/批量替换）
│   ├── column_mapping_dialog.py # 列映射只读展示
│   ├── help_dialog.py           # 使用说明窗口（目录胶囊跳转）
│   ├── help_content.py          # 使用说明正文（HTML）
│   ├── theme.py                 # 全局亮色主题 QSS
│   ├── toast.py                 # 顶部居中堆叠的非阻塞轻提示
│   └── tray.py                  # 系统托盘图标与菜单
├── assets/                      # 图标资源（icon.png / icon.ico / icon_rounded_256.png）
├── local.db                     # 运行时生成的本地 SQLite（与 exe 同目录）
├── import_log.txt               # 运行时生成的导入日志
├── sheet_names.txt              # 初始 Sheet 名列表（首次启动播种）
├── create_all_tables.sql        # 目标表建表 DDL
├── requirements.txt
└── build.spec                   # PyInstaller 打包配置
```

### 各层职责

**入口（`main.py`）**

| 职责 |
|---|
| 注册全局 `sys.excepthook`（主线程弹统一错误框，工作线程只落日志，避免跨线程操作控件）；设置 Windows AppUserModelID；应用主题；创建托盘；`init_db()` 失败时弹框后退出；后台线程自动连接上次使用的库；主窗口关闭后可循环进入连接管理（「连接管理」切换连接不自动重连） |

**UI 层（`ui/`）**

| 模块 | 职责 |
|---|---|
| `main_window.py` | 文件选择（后台读取 + 读取计时 + Toast）、Sheet 概览（勾选 / 序号 / 名称 / 最后导入时间，失败 Sheet 红标 + tooltip）、Shift 区间勾选与全选、映射缺失 / 同表冲突拦截、去重/验证/导入入口、失败 Sheet 一键补录提示、菜单栏（连接管理 `Ctrl+Shift+C` / Sheet名-表映射 `Ctrl+N` / 列映射 / 使用说明）、关窗托盘询问、状态栏连接信息 |
| `base_task_dialog.py` | 任务进度对话框基类：进度条（支持不确定模式）、状态文字、已用时、日志区、关闭按钮；运行中拦截 `reject`/`closeEvent`；`_add_extra_buttons` 钩子供子类注入按钮；关闭按钮在线程真正退出后才启用 |
| `connection_dialog.py` | 连接管理：左侧已保存连接列表（连接名 + 服务器·数据库副标题 + 「最近使用」标签），右侧表单（连接名称/服务器/数据库/Schema/用户名/密码 + 密码显隐）；新增 / 删除；后台线程测试或连接；防重入与关闭拦截；连接成功后保存配置并返回连接信息 |
| `import_dialog.py` | 继承 BaseTaskDialog；工作线程内用主窗口传入的本次会话连接参数快照独立建连；单 Sheet 导入改不确定进度；失败自动跳过后展示「成功 X / 失败 Y」与失败明细（报错经中文化）；注入「打开错误名单」按钮；对成功表批量 `SELECT COUNT(*)` 刷新实际行数 |
| `validate_dialog.py` | 继承 BaseTaskDialog；错误结果表格（序号/Sheet/行号/字段/当前值/原因），连续出错行折叠为区间，类型下拉筛选，行高随内容撑开；整体失败（文件损坏等）走独立提示 |
| `dedup_settings_dialog.py` | 去重模式单选（按 Sheet 内 / 全局）、判重列下拉（11 条列映射 + 固定追加「L 匹配类型」）；摘要说明兼作去重前确认；确认时保存设置到 SQLite |
| `dedup_dialog.py` | 继承 BaseTaskDialog；逐 Sheet 结果表（处理方式/总行数/删除/保留）；经基类钩子注入「取消」按钮；`dedup_result` 供主窗口判断是否自动切换文件 |
| `confirm_dialog.py` | 导入 / 验证前的确认对话框：展示选中 Sheet→表名映射（序号、Sheet名称、数据库表名） |
| `sheet_directory_dialog.py` | Sheet名-表映射：搜索筛选（200ms 防抖）、双击编辑（回车即保存并 Toast 提示「列名: 旧值 → 新值」）、右上「新增」、右键删除（弹窗确认）、「替换为 + 替换全部」在筛选结果内批量替换 |
| `column_mapping_dialog.py` | 列映射只读展示（序号、Excel列、数据库字段、Excel索引、说明、约束说明） |
| `help_dialog.py` / `help_content.py` | 非模态使用说明：顶部目录胶囊（使用流程/菜单功能/注意事项/联系信息）跳转锚点；正文 HTML 由 `help_content.build_help_html()` 生成 |
| `theme.py` | 全局亮色 QSS：白底 + 蓝色主色 + 圆角卡片；约定 `class="primary"`、`secondary=True`、`card`、`innerTable`；`apply_theme()` 设 Fusion 风格与调色板 |
| `toast.py` | 仿 Element Plus 的非阻塞轻提示：父窗口顶部居中、多条向下堆叠、淡入 + 下滑、自动淡出；四种类型 success/error/warning/info |
| `tray.py` | 系统托盘：`TrayController` 封装 QSystemTrayIcon（「显示主窗口/退出」菜单、双击恢复、最小化/忙碌气泡提示）；`create_tray_icon()` 优先加载 `assets/icon.png` 并圆角遮罩多尺寸，缺失时返回空图标 |

**业务逻辑层（`app/`）**

| 模块 | 职责 |
|---|---|
| `constants.py` | 全局常量：`ERROR_CONTACT` 统一错误联系信息 |
| `config.py` | 封装 `local_db` 的连接读写接口，`load_config()` / `save_config()` 对外透明 |
| `local_db.py` | 本地 SQLite 管理：`db_connections`（多连接 + `schema_name` + `is_last_used`，按 server+database 复用记录）、`sheet_names`（Sheet→表名 + `last_import_time` + `last_import_status`）、`column_mapping`（列映射 + `constraint_desc`）、`dedup_settings`（key-value，默认全局去重 / D 列）；`init_db()` 建表、迁移新增列并回填约束说明与连接名，从 `sheet_names.txt` 播种；CRUD 含 `get_all_connections()` / `get_last_connection()` / `save_connection()` / `delete_connection()` / `add_sheet_mapping()` / `update_sheet_mapping()` / `delete_sheet_mapping()` / `update_import_result()` / `get_failed_sheet_names()` / `get_dedup_settings()` / `save_dedup_settings()` |
| `database.py` | `connect()`（ODBC 连接串值花括号转义，登录超时 10s，查询超时 300s）/ `test_connection()` / `check_tables_exist()`（单次 IN 查询）/ `delete_all_tables()`（DELETE 清空）/ `insert_batch()`（fast_executemany）/ `count_tables_rows_batch()`（UNION ALL 批量 COUNT）；所有 SQL 带 schema 前缀并转义标识符 |
| `dedup.py` | 数据去重：calamine 单遍流式扫描定保留行（不缓存行数据，日期解析记忆化、字符串驻留）+ `xlsx_surgery.rewrite_workbook` 全保真写出；判重键经 `utils.normalize_dedup_key` 规范化，空键 / 空时间不判重；未勾选 Sheet 字节级搬运；进度三段单调（扫描→校验→写出）；输出 `原名_已去重.xlsx` 与 `重复清单__原名….csv`（长表：处理/Sheet名称/Excel行号/判重列原始值/录入时间），`_resolve_output_paths` 永不覆盖已有文件；取消作废整个输出；PanicException 等非 Exception 错误同样收敛进 `error` 字段；返回 dict 契约与 `importer.run_import` 一致 |
| `xlsx_surgery.py` | XML 手术引擎：`sheet_xml_entries()` 复用 `excel_reader.read_sheet_entries` 建立 Sheet 名→zip 条目映射；`rewrite_workbook()` 输出 = 源 zip 逐条目复制，勾选去重的 worksheet XML 两读一写（MODE_SCAN 预扫描校验行号对齐并拒止共享公式 → MODE_SURGERY 删行 + 行号紧凑重排 + dimension/autoFilter/合并单元格/数据验证 sqref/超链接修正，含被删行的合并单元格剔除）；未勾选 sheet 预扫描计数后纯字节泵搬运；取消用单一公开 `Cancelled` 异常贯穿三层检查点 |
| `error_list.py` | 错误名单生成：`generate_error_list()` 把失败表的结构化错误写成「源文件名__导入错误名单_时间戳.xlsx」（同秒冲突加 `_2`，永不覆盖）；「汇总」按 (负责人, Sheet) 聚合错误行数、出错行区间、主要问题；「明细」为行级错误（含 autofilter）；无行级错误的整表失败合成一条明细 |
| `error_msgs.py` | `humanize_db_error()`：把 ODBC 错误码（22018、HY000、HY010、08S01 等）与「截断/空值」等常见报错翻译为中文；已是中文的错误原样返回 |
| `date_utils.py` | `DATE_FORMATS`（5 种格式）、`normalize_date_str()`（NFKC 全角转半角，日期段 `/`、`.` → `-`，时间段 `.`、全角冒号 → `:`）、`parse_date()` 统一返回纯 `datetime.date` |
| `excel_reader.py` | `read_sheet_entries()` / `read_sheets()` 用 zipfile + ElementTree 解析 `xl/workbook.xml`；`iter_sheet_rows_from_workbook()` 从已打开的 workbook 流式读取（跳过表头、跳过空行、截断到 11 列），返回 `(批次起始行号, [(实际Excel行号, 行数据)])` |
| `importer.py` | 编排导入：检查勾选表 → 逐表（DELETE → 流式预检 + 批量插入 → 提交）→ 更新导入状态；某表数据错误仅回滚该表、记录失败并继续后续表，连接级错误中止全程；`_row_to_dict()` 转字段 dict（collected_at 走 `date_utils`，nullable 空值转 `""`）；批量失败 `_diagnose_batch()` 逐行定位；结构化错误（row/message/kind/fields/values）同时供日志与错误名单；有失败表自动生成名单；结果统一 dict |
| `validator.py` | 离线验证：`FIELD_CONSTRAINTS`（2 个 NOT NULL + 9 个长度限制 + 1 个日期校验，与 DDL 一致），复用 `date_utils` 与 `importer._row_to_dict`，一次性收集选中 Sheet 全部错误 |
| `utils.py` | `col_letter()`；`merge_row_ranges()` 行号合并为连续区间；`normalize_dedup_key()`（strip + 全角 ASCII / 全角空格转半角）；`timestamped_output_candidates()` 永不覆盖的时间戳候选路径 |
| `logger.py` | 导入 / 去重日志：开始 / 结束时间、状态（含「部分成功（成功 X / 失败 Y）」）、各表行数、失败表明细、错误名单路径、去重逐 Sheet 统计；超 1MB 轮转为 `.bak`；msvcrt 文件锁；`log_uncaught()` 记录未捕获异常 |

### 核心数据流

```
启动 → 自动尝试上次使用的连接（后台线程 + 遮罩）
  ├─ 成功 → 主窗口
  └─ 失败 → 连接管理对话框（多连接新增/删除/测试/连接）
              ↓ 连接成功
            主窗口（运行中切换连接会回到连接管理）
  ↓ 用户选择 .xlsx（后台 zipfile 秒级读 Sheet 名，显示读取用时）
Sheet 概览（勾选 + 序号 + 名称 + 最后导入时间，默认全选；Shift 区间勾选）
  ├─→ 点「开始去重」→ 去重设置（模式/判重列，摘要兼确认）
  │     → calamine 扫描定保留行（空键/坏时间保留、同键保留录入时间最早）
  │     → XML 手术写出全格式保真副本（未勾选 Sheet 字节级搬运）
  │     → 输出「原名_已去重.xlsx」+（如有删除）「重复清单__原名….csv」→ 记录日志
  │       ↓ 成功（取消则作废输出、不切换）
  │     主窗口自动切换到输出文件（重建勾选为全选）→ 直接「开始导入」
  ├─→ 点「验证数据」→ 确认映射 → 离线校验选中 Sheet（可选排查，不写库）
  └─→ 点「开始导入」→ 确认映射 → 检查勾选表存在（缺失即终止）
        ↓ 全部存在
      工作线程独立建连 → 逐表：BEGIN → DELETE → 批量预检 + INSERT → COMMIT → 写导入状态
        ↓（某表错误：仅该表回滚、记入失败、继续下一表；连接级错误才中止全程）
      汇总「成功 X / 失败 Y」→ 有失败表自动生成错误名单（汇总 + 明细）
        ↓ 成功或部分成功
      批量 SELECT COUNT(*)（UNION ALL）查询成功表实际行数
        ↓
      记录 import_log.txt → 主窗口刷新最后导入时间与失败红标
        ↓ 业务按名单修正后重新选择定稿文件
      检测到失败 Sheet → 提示「只勾选上次失败的 Sheet」→ 一键补录 → 状态翻正、红标消除
```

### 关键设计决策

1. **扁平模块，`importer.py` 只做编排**：UI 只负责展示与交互，导入 / 去重 / 验证各自独立成模块；面向内部少量用户，不引入 MVC / MVVM 框架。
2. **逐表独立事务 + 失败继续 + 连接探活**：每表 `BEGIN → DELETE → INSERT → COMMIT`；表级 / 数据错误仅回滚该表并继续，`SELECT 1` 探活失败才中止全程；清空统一用 DELETE，兼容无 TRUNCATE 权限。
3. **本地 SQLite 是唯一配置源**：`db_connections`（多连接 + 上次使用）、`sheet_names`（映射 + 导入时间 + 失败状态）、`column_mapping`、`dedup_settings`；首次启动自动建表、迁移新增列并从 `sheet_names.txt` 播种。
4. **错误发现内建于导入，独立验证只作可选排查**：导入逐批做 NOT NULL / 日期 / 长度预检，坏行在整个 Sheet 扫描完后判失败；结构化错误同时生成日志文本与错误名单，保证「同一份数据、两种展示」。
5. **失败表按表名记忆、跨文件补录**：失败状态写入 `last_import_status`（`success` / `failed`，NULL 表示未尝试），与文件名无关；主窗口红标 + 加载新文件时一键只勾失败 Sheet，补录成功后状态翻正。
6. **去重用 XML 手术而非重写工作簿**：输出 = 源 zip 逐条目复制，仅重写勾选 Sheet 的 worksheet XML（删行、行号紧凑、dimension / autoFilter / 合并单元格 / 数据验证 / 超链接修正）；未勾选 Sheet 字节级搬运，样式与条件格式原样保留；预扫描校验行号对齐、拒止共享公式，输出永不覆盖、取消作废整个文件。
7. **pyodbc 线程安全与超时**：工作线程内独立建连，每批独立 cursor；登录超时 10s、查询超时 300s，避免目标表被他人锁住时 DELETE / INSERT 永久阻塞。
8. **错误集中与统一话术**：`ERROR_CONTACT` 集中联系信息，`error_msgs.humanize_db_error` 翻译底层报错；全局 `sys.excepthook` 兜底，工作线程异常只落日志不弹窗（QMessageBox 不可跨线程）。
9. **UI 一致性与防误操作**：统一 `theme.py` QSS + `toast.py` 非阻塞提示；模态任务运行中拦截关闭（运行中的 QThread 被析构会崩溃）；导入前拦截「Sheet 无映射」「多 Sheet 映射同一表」；系统托盘支持最小化与彻底退出。
10. **性能取舍**：整个任务只打开 workbook 一次；Sheet 名与 XML 条目用 zipfile；列映射与长度约束模块级缓存；表存在性检查与导入后 `COUNT(*)` 合并为单次批量 SQL，减少网络往返。

---

## 使用指南

### 数据源结构

所有 46 个 Sheet 共 11 列，部分 Sheet 第 2 列名为 `小组` 而非 `负责人`，Sheet 046 多出第 12 列 `匹配类型`。

| # | 列名 |
|---|---|
| 1 | 日期 |
| 2 | 负责人 / 小组 |
| 3 | 来源 |
| 4 | 企业名称 |
| 5 | 官网 |
| 6 | 一级分类 |
| 7 | 二级分类 |
| 8 | 三级分类 |
| 9 | 单位类型 |
| 10 | 环节 |
| 11 | 系统重复 |

列与数据库字段的对应关系及约束见菜单「列映射」（11 条映射，含约束说明）。

### 使用流程

1. **连接数据库**：启动后自动尝试上次使用的连接；失败则打开「数据库连接管理」，左侧点选已保存连接即回填表单，可新增 / 删除；右侧填写连接名称、服务器、数据库、Schema（默认 dbo）、用户名、密码，「测试连接」成功后点「连接」进入主窗口
2. **选择 Excel 文件**：点击「选择文件」，后台线程秒级读取全部 Sheet，概览显示序号、名称及最后导入时间
3. **勾选要处理的 Sheet**：默认全选；可逐行勾选，或先点起始行再按住 Shift 点击结束行批量勾选；底部「全选」一键全选 / 取消
4. **去重（可选，每周例行）**：点击「开始去重」→ 选择模式（默认全局去重）与判重列（默认 D 企业名称）→ 确认后执行；输出「原名_已去重.xlsx」与「重复清单__原名_已去重.csv」，成功后主窗口自动切换到去重后文件
5. **导入（失败自动跳过）**：点击「开始导入」→ 在确认对话框核对 Sheet→表名映射 → 逐表执行「清空目标表 → 批量插入 → 提交」；某表失败自动回滚并跳过，结束汇总「成功 X / 失败 Y」并展示数据库实际行数
6. **处理错误名单**：有失败表时自动在源文件同目录生成「源文件名__导入错误名单_时间戳.xlsx」，点「打开错误名单」查看；「汇总」页按负责人统计可直接复制进群催办，「明细」页可筛选定位
7. **修正与补录**：把名单发业务人员修正；修正后重新选择定稿文件，程序自动提示「只勾选上次失败的 Sheet」，确认后「开始导入」一键补录，失败的 Sheet 红标随之消除

### 配置管理

| 配置项 | 位置 | 说明 |
|---|---|---|
| 数据库连接 | 连接管理对话框 / SQLite `db_connections` | 可保存多条连接（连接名、服务器、库名、Schema、用户名、密码）；`is_last_used` 标记上次使用，启动时自动连接并自动填充 |
| Sheet名-表映射 | 菜单「Sheet名-表映射」（`Ctrl+N`） | 展示全部映射（序号、Sheet名称、数据库表名、最后导入时间），支持搜索筛选、双击编辑、新增、右键删除、批量替换 |
| 列映射 | 菜单「列映射」 | 只读展示 Excel 列→数据库字段映射（序号、Excel列、数据库字段、Excel索引、说明、约束说明） |
| 去重设置 | 去重设置弹窗 / SQLite `dedup_settings` | 去重模式（默认全局去重）与判重列（默认 D 企业名称），确认去重时自动保存 |
| 失败状态 | SQLite `sheet_names.last_import_status` | 按表名记录 `success` / `failed`，用于红标与一键补录 |

### 部署与打包

- 使用 PyInstaller 打包为单个 .exe 文件，在 Windows 上直接运行（`pyinstaller build.spec`）
- `build.spec` 将 `sheet_names.txt` 与 `assets/icon.png` 打进包内，exe 图标使用 `assets/icon.ico`，`console=False`
- 本地 SQLite 数据库 `local.db` 与 exe 同目录，首次启动自动建表并播种
- 最终用户无需安装 Python 或任何依赖
- 远程数据库表结构由开发者提前在 SQL Server 中建好，工具本身不建表
- 导入 / 去重日志输出到 exe 同目录的 `import_log.txt`（超 1MB 轮转为 `.bak`）

---

## 注意事项

- **关窗行为**：托盘可用时点 ✕ 每次弹窗询问「直接退出（默认）/ 最小化到托盘 / 取消」（Esc、点弹窗 ✕ 均为取消关窗）；最小化后双击托盘图标恢复，右键「退出」彻底退出（任务运行中拒绝退出并气泡提示）；托盘不可用时直接退出不询问
- **全量覆盖导入**：每次导入先清空目标表再插入全部数据，请确认勾选范围后再执行
- **逐表独立事务且失败不中断**：某表导入失败仅该表回滚，其余表照常导入并记录 `last_import_time`；连接中断等严重错误才中止整个流程（中止前已成功的表保留）
- **失败表记忆与一键补录**：失败状态按表名持久化，主窗口红标提示；加载新文件时自动提示只勾选失败 Sheet 补录，跨文件名有效
- **错误名单**：有失败表时自动生成于源文件同目录（带时间戳、永不覆盖）；「汇总」页按负责人统计，「明细」页可筛选；「打开错误名单」按钮一键打开
- **清空方式为 DELETE**：目标表使用 `DELETE FROM` 清空（而非 TRUNCATE），兼容无 TRUNCATE 权限的账号
- **表缺失检查**：导入前仅检查本次勾选的表是否全部存在，任一缺失则终止并提示执行 `create_all_tables.sql`
- **映射冲突检查**：Sheet 无本地映射、或多个 Sheet 映射到同一张表时，导入 / 验证前直接拦截并提示修正
- **Schema 支持**：连接管理可指定 Schema（默认 dbo），所有 SQL 均带 schema 前缀
- **日期格式兼容**：Excel 日期可能被 python-calamine 读为 `datetime.datetime` 或字符串（如 `'2026-02-02 00:00:00'`、`'2026/2/2 0:00'`、`'2026/7/4 13.29'`、`'2026/4/20/09:50'`、`'2026/5/27/11：27'`），`date_utils` 统一归一化后按 5 种格式解析为纯 `datetime.date`，避免 SQL Server「日期时间字段溢出」
- **数值格式日期会被拦截**：Excel「常规」单元格把日期读成序列号（int/float）时，导入预检直接报错并提示「日期列应为文本格式」
- **可空列空值处理**：nullable nvarchar 列的 `None` 自动转为空字符串 `""`，避免 `fast_executemany` 类型推断过窄导致 "String data, right truncation"
- **行号追踪**：Excel 空行会被跳过，诊断时以实际 Excel 行号定位 Sheet、行号、列名及单元格值；同类错误按报错分组展示，连续行号折叠为区间
- **查询超时**：`connect()` 登录超时 10s，连接后查询超时 300s；目标表被他人长时间锁住时会报超时而非无限等待
- **错误处理**：所有错误统一弹窗提示，附带联系信息（`ERROR_CONTACT`）；「使用说明」菜单中亦可查看使用流程与联系人
- **验证功能定位**：「验证数据」为可选离线检查（NOT NULL、字段长度、日期格式，不写库），用于导入前抽查或排查疑难；每周例行流程直接导入，导入器内置预检会完整收集坏行
- **数据去重**：判重键 = 判重列值去首尾空白并全角转半角；判重键为空或录入时间不可解析的行不参与判重、原样保留；同一判重键保留录入时间最早者（平手保留首次出现），整行删除其余重复行（含 Sheet 046 第 12 列在内的全列保真）；输出为全格式保真副本（XML 手术：样式、条件格式、列宽、超链接、自动筛选、保护原样保留，仅删行 + 行号重排；合并单元格与数据验证区域随行号平移修正，范围内含被删行的合并单元格剔除；含共享公式的 Sheet 预扫描即拒止），未勾选的 Sheet 字节级原样搬运；输出永不覆盖任何已有文件（目标已存在自动加时间戳，对已去重文件再去重也生成新副本）；重复清单 CSV 为长表对照（处理/Sheet名称/Excel行号/判重列原始值/录入时间，保留行与其全部删除行相邻）；判重列选 L 匹配类型时，无第 12 列的 Sheet 键全为空、自然退化为仅复制，属预期行为
- **去重取消**：中途取消则作废整个输出文件（不产出半去重文件），且不自动切换文件；输出文件被 Excel 占用时提示关闭后重试
- **多实例**：`local.db` 与日志均按「与 exe 同目录」定位；日志写入加文件锁，连接配置以 `is_last_used` 标记，双开实例时主窗口使用本次会话的连接参数快照建连，不受另一实例改写影响
