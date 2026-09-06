# 四方信息源入库

> 将 Excel 文件中 40+ 个 sheet 的数据批量导入 SQL Server 的桌面工具。

---

## 项目概述

### 产品定位

将 Excel 文件中 40+ 个 sheet 的数据批量导入 SQL Server 的桌面工具。每个 sheet 映射为一张表，每次导入全量覆盖（先删后插）。面向内部少量用户，启动后先填写数据库连接参数，连接成功后选择文件导入数据。

### 项目文件说明

| 文件 | 说明 |
|---|---|
| `信息源8.8_已去重.xlsx` | 数据源 Excel 文件，包含 46 个 sheet，每个 sheet 对应一个行业分类的企业数据（运行时由用户选择，不打包进 exe） |
| `数据规范.png` | 数据规范参考图（人工查看用，程序不引用） |
| `sheet_names.txt` | 从数据源 Excel 提取的所有 sheet 名称列表，共 46 个（首次启动时自动播种到 SQLite） |
| `local.db` | 本地 SQLite 数据库（首次启动自动生成），含 `db_connections`（连接配置/登录）、`sheet_names`（sheet→表名映射 + 导入状态）、`column_mapping`（Excel 列→DB 字段映射）、`dedup_settings`（去重模式与判重列）四张表 |
| `create_all_tables.sql` | 46 张表的建表 DDL 脚本（GB2312 编码），表名 `enterprise_info_001~046`，结构参照已有表 |
| `import_log.txt` | 运行时生成的导入日志（超过 1MB 自动轮转为 `import_log.txt.bak`） |

---

## 核心功能

### 功能清单

- 启动后先填写数据库连接参数（服务器地址、数据库名、Schema、用户名、密码），测试连接成功后方可继续
- 用户手动选择 .xlsx 文件，程序秒级读取全部 sheet 名称（zipfile 解析 `xl/workbook.xml`，不阻塞界面）
- 导入前检查数据库中 46 张目标表（`enterprise_info_001~046`）是否全部存在，任一缺失则终止导入并弹窗提示
- 按 sheet 名称匹配数据库表，数据批量写入 SQL Server（每批 5000 行，`fast_executemany`）
- 每次导入逐表独立事务：先清空目标表（DELETE，兼容无 TRUNCATE 权限环境），再重新插入全部数据
- 导入失败不中断：某 sheet 导入失败时仅回滚该表、自动跳过并继续导入后续表，全部表处理完后汇总「成功 X / 失败 Y」；仅连接断开等基础设施错误中止整个流程
- 有失败表时自动在源文件同目录生成「源文件名__导入错误名单_时间戳.xlsx」（永不覆盖）：「汇总」页按负责人统计错误行数（可直接复制进群消息催办），「明细」页列出 Sheet、Excel 行号、列名、当前值、问题描述，可筛选
- 失败表按表名持久化记忆（SQLite `sheet_names.last_import_status`）：主窗口概览中标红提示，加载新文件（如业务修正后的定稿文件）时自动提示「只勾选上次失败的 Sheet」一键补录
- 每周例行流程使用内置去重（全局模式、判重列默认 D 企业名称），外部去重工具退役；「验证数据」保留为可选离线检查（不写库），不在每周例行流程中使用
- 记录导入日志（开始时间、结束时间、各表行数、成功/部分成功/失败状态、失败表明细、错误名单路径），日志超 1MB 自动轮转
- 所有错误统一弹窗提示，附带联系信息（集中在 `app/constants.py`）："发生错误，请联系世贸项目部-数据组-王霖霖，世贸项目部-数据组-张同宁"
- 支持勾选部分 sheet 进行验证/导入（通过 SQLite `sheet_names` 表映射 sheet→表名）
- 导入失败时自动逐行诊断，按错误类型分组输出，定位到具体 Sheet、Excel 行号、列名及单元格值，并记录原始数据库报错信息
- 点击「验证数据」按钮可对 Excel 数据做离线校验（NOT NULL、字段长度、日期格式），一次性找出所有错误并展示，不写数据库；为可选排查工具，每周例行流程不使用
- 点击「开始去重」可对勾选的 Sheet 去重（未勾选的 Sheet 原样复制进输出文件）：支持「按 Sheet 内去重 / 全局去重」两种模式切换与判重列下拉自选（默认 D 企业名称），设置持久化到本地 SQLite
- 判重键 = 判重列值去首尾空白并全角转半角；判重列为空的行不参与判重、原样保留；保留首次出现的行，整行删除后续重复行
- 去重输出为源文件同目录「原名_已去重.xlsx」，永不覆盖任何已有文件：目标 xlsx 或重复清单 CSV 已存在（或与源文件同名，即对已去重文件再去重）时自动加时间戳（如「原名_已去重_20260905_153012.xlsx」，xlsx 与 CSV 配对同一时间戳，同秒冲突加计数后缀）；源文件名已带 `_已去重` 后缀或旧时间戳则先归一再重建、不叠加后缀；如有删除同时生成「原名_已去重__重复清单.csv」对照清单（UTF-8-SIG 长表：处理/Sheet名称/Excel行号/判重列原始值，同一保留行与其全部删除行相邻成组，保留/删除各自显示自己的原始值）
- 去重成功后主窗口自动切换到输出文件，可直接点「开始导入」走现有流程入库；去重过程支持取消（取消后输出文件保留已处理部分，不自动切换文件）
- 系统托盘驻留（`ui/tray.py`，QSystemTrayIcon）：图标优先加载 `assets/icon.png`（用户「四方」logo，运行时居中裁方 + 圆角遮罩，多尺寸 16~256；缺失时兜底 QPainter 画蓝底「四」字；PyInstaller 经 datas 打包、`sys._MEIPASS` 定位），exe 文件图标用 `assets/icon.ico`（圆角多尺寸，Pillow 从 logo 生成）；主窗口运行期间右下角显示图标；点 ✕ 关窗每次弹窗询问「直接退出（默认）/最小化到托盘」，选最小化则气泡提示去向，双击托盘图标恢复窗口，右键菜单「显示主窗口/退出」彻底退出；导入/去重/验证任务运行中拒绝退出并气泡提示；托盘不可用时退化为关窗即退出（不询问）
- 打包为可运行的 .exe 文件

### 范围外功能（不做）

- 不做增量导入、数据对比或数据清洗
- 不做用户登录验证和权限管理
- 不做 Web 版本或 API
- 不做数据报表或可视化
- 不做 Excel → DB 的字段映射配置（按固定结构处理）

---

## 技术架构

### 技术栈

| 层 | 技术 |
|---|---|
| 语言 | Python 3.14（解释器：C:/Users/Administrator/Desktop/sifang/.venv/Scripts/python.exe） |
| 桌面 GUI | PySide6（Qt for Python） |
| Excel 读取 | python-calamine（Rust 解析器，数据读取）+ zipfile（sheet 名秒级解析） |
| Excel 写出 | xlsxwriter（constant_memory 模式，去重结果流式写出） |
| 远程数据库驱动 | pyodbc（SQL Server，ODBC Driver 17） |
| 本地数据库 | SQLite（sqlite3 标准库），存储连接配置和 sheet 名称映射 |
| 打包分发 | PyInstaller（单文件 exe） |

### 目录结构

```
sifang/
├── main.py                      # 应用入口
├── app/                         # 业务逻辑层
│   ├── __init__.py
│   ├── config.py                # 配置管理（从本地 SQLite 读写连接参数，替代 config.ini）
│   ├── constants.py             # 全局常量（统一错误联系信息 ERROR_CONTACT）
│   ├── local_db.py              # 本地 SQLite 数据库管理（建表、迁移、播种、CRUD）
│   ├── database.py              # 数据库连接、表检查、批量插入、COUNT(*) 查询（全部带 schema 支持）
│   ├── dedup.py                 # 数据去重（calamine 单遍读 + xlsxwriter constant_memory 写，重复行不写入输出）
│   ├── error_list.py            # 导入错误名单生成（失败表结构化错误 → 汇总/明细双 sheet xlsx，永不覆盖）
│   ├── date_utils.py            # 日期解析工具（验证与导入共用同一套格式与归一化逻辑）
│   ├── excel_reader.py          # Excel 文件读取（zipfile 读 sheet 名 + python-calamine 读数据）
│   ├── importer.py              # 导入编排器（协调 database + excel_reader）
│   ├── validator.py             # 数据验证（NOT NULL、长度、日期格式离线校验）
│   ├── utils.py                 # 通用工具（col_letter 列号转字母、normalize_dedup_key 判重键规范化）
│   └── logger.py                # 日志记录（import_log.txt，1MB 轮转，多实例文件锁）
├── ui/                          # 界面层（PySide6）
│   ├── __init__.py
│   ├── main_window.py           # 主窗口：文件选择、Sheet 概览（勾选框+最后导入时间）、验证/导入入口
│   ├── base_task_dialog.py      # 任务进度对话框基类（进度条、状态、已用时、日志区、关闭按钮）
│   ├── connection_dialog.py     # 数据库连接对话框（服务器/库名/Schema/用户名/密码）
│   ├── import_dialog.py         # 导入进度/结果展示（继承 BaseTaskDialog）
│   ├── validate_dialog.py       # 验证数据进度/结果展示（继承 BaseTaskDialog）
│   ├── dedup_settings_dialog.py # 去重设置对话框（模式/判重列下拉，摘要兼作确认，设置持久化）
│   ├── dedup_dialog.py          # 去重进度/结果展示（继承 BaseTaskDialog，支持取消）
│   ├── confirm_dialog.py        # 确认对话框（展示选中 sheet→表名映射）
│   ├── sheet_directory_dialog.py # Sheet名-表映射对话框（支持增删改查、筛选）
│   ├── column_mapping_dialog.py  # 列映射对话框（含约束说明）
│   └── tray.py                   # 系统托盘图标（QSystemTrayIcon：显示/退出菜单、气泡提示、程序绘制图标）
├── local.db                     # 运行时生成的本地 SQLite 数据库（与 exe 同目录）
├── import_log.txt               # 运行时生成的导入日志
├── requirements.txt
└── build.spec                   # PyInstaller 打包配置
```

### 各层职责

**UI 层（`ui/`）**

| 模块 | 职责 |
|---|---|
| `main_window.py` | 主窗口：文件选择（后台线程读取、显示读取用时）、Sheet 概览（勾选框 + 序号 + Sheet名称 + 最后导入时间、失败 Sheet 红标）、失败 Sheet 一键补录提示、全选 checkbox、验证/导入操作入口、菜单栏（Sheet名-表映射/列映射/使用说明） |
| `base_task_dialog.py` | 任务进度对话框基类：进度条、状态文字、已用时间、日志区、关闭按钮；子类实现 `_run_worker()` / `_on_finished()` |
| `connection_dialog.py` | 启动时弹出，填写服务器/库名/Schema/用户名/密码，后台线程测试连接，成功后保存配置并返回 `connection` 与 `schema` |
| `import_dialog.py` | 继承 BaseTaskDialog；工作线程内独立创建 pyodbc 连接（避免跨线程共享）；失败自动跳过后展示「成功 X / 失败 Y」与失败表明细，注入「打开错误名单」按钮；部分成功时对成功表批量 `SELECT COUNT(*)`（UNION ALL）查询数据库实际行数 |
| `validate_dialog.py` | 继承 BaseTaskDialog；展示数据验证进度条和结果日志 |
| `dedup_settings_dialog.py` | 去重设置对话框：去重模式单选（按 Sheet 内/全局）、判重列下拉（11 条列映射 + 固定追加「L 匹配类型」）、摘要说明兼作去重前确认；确认时保存设置到 SQLite |
| `dedup_dialog.py` | 继承 BaseTaskDialog；展示去重进度与逐 Sheet 结果表（处理方式/总行数/删除/保留），经基类 `_add_extra_buttons` 钩子注入「取消」按钮；`dedup_result` 属性供主窗口判断是否自动切换文件 |
| `confirm_dialog.py` | 确认对话框：展示选中 sheet→表名映射（3 列），用户确认后执行操作 |
| `sheet_directory_dialog.py` | Sheet名-表映射对话框：展示全部 sheet→表名映射（含最后导入时间），支持搜索筛选（防抖）、双击编辑、新增、右键删除 |
| `column_mapping_dialog.py` | 列映射对话框：展示 Excel 列→数据库字段映射（序号、Excel列、数据库字段、Excel索引、说明、约束说明） |
| `tray.py` | 系统托盘：`TrayController` 封装 QSystemTrayIcon（「显示主窗口/退出」菜单、双击恢复、最小化/忙碌气泡提示），`create_tray_icon()` 优先加载 assets/icon.png（圆角遮罩多尺寸），缺失时兜底画「四」字 |

**业务逻辑层（`app/`）**

| 模块 | 职责 |
|---|---|
| `constants.py` | 全局常量：`ERROR_CONTACT` 统一错误联系信息 |
| `config.py` | 封装 `local_db` 的连接读写接口，`load_config()` / `save_config()` 对外透明 |
| `local_db.py` | 本地 SQLite 数据库管理：`db_connections` 表（连接配置 + `schema_name` + `is_last_used`）、`sheet_names` 表（sheet→table_name 映射，含 `last_import_time` 与 `last_import_status` 导入状态）、`column_mapping` 表（Excel 列→DB 字段，含 `constraint_desc` 约束说明）、`dedup_settings` 表（key-value，去重模式与判重列，默认全局去重）；`init_db()` 首次建表并播种，自动迁移新增列并回填约束说明；CRUD：`add_sheet_mapping()` / `update_sheet_mapping()` / `delete_sheet_mapping()` / `update_import_result()` / `get_failed_sheet_names()` / `get_dedup_settings()` / `save_dedup_settings()` |
| `database.py` | `connect()`（ODBC 连接串值花括号转义）/ `test_connection()` / `check_tables_exist()`（单次 IN 查询）/ `delete_all_tables()`（DELETE 清空，兼容无 TRUNCATE 权限）/ `insert_batch()`（fast_executemany）/ `count_tables_rows_batch()`（UNION ALL 批量 COUNT）；所有 SQL 均带 schema 前缀并转义标识符 |
| `dedup.py` | 数据去重：`run_dedup()` calamine 单遍读 + xlsxwriter `constant_memory` 逐行写出保留行（重复行根本不写入，结构上不存在「残留删不净」）；判重键经 `utils.normalize_dedup_key` 规范化，空键不判重；未勾选 Sheet 原样复制；输出 `原名_已去重.xlsx` 与 `__重复清单.csv` 保留/删除对照清单（长表，`_write_duplicates_csv`），`_resolve_output_paths` 目标已存在时整体加时间戳、永不覆盖任何已有文件；返回 dict 契约同 `importer.run_import` |
| `utils.py` | 通用工具：`col_letter()` 列号转字母；`normalize_dedup_key()` 判重键规范化（strip + 全角 ASCII U+FF01-FF5E 与全角空格 U+3000 转半角） |
| `date_utils.py` | 日期解析：`DATE_FORMATS`（5 种格式）、`normalize_date_str()`（`/`→`-`、`.`→`:`、全角冒号→半角）、`parse_date()` 统一转为纯 `datetime.date` |
| `excel_reader.py` | `read_sheets()` 用 zipfile 解析 workbook.xml 秒级读取全部 sheet 名；`iter_sheet_rows_from_workbook()` 从已打开的 workbook 流式读取（跳过表头、跳过空行、截断到 11 列），返回 `(批次起始行号, [(实际Excel行号, 行数据)])` |
| `importer.py` | 编排导入流程：检查表 → 逐表（DELETE 清空 → 流式批量插入 → 提交）→ 更新导入状态；某表数据错误仅回滚该表、记录失败并**继续后续表**，连接级错误（`SELECT 1` 探活失败）才中止全程；`_row_to_dict()` 将 Excel 行转为数据库字段 dict（collected_at 走 `date_utils`，nullable 空值转 `""`）；`_diagnose_batch()` 批量失败时逐行定位；行级错误收集为结构化 dict（row/message/kind/fields/values），日志文本与错误名单 xlsx 同源；`_format_sheet_errors()` 按错误类型分组输出 |
| `error_list.py` | 导入错误名单生成：`generate_error_list()` 把失败表的结构化错误写成「源文件名__导入错误名单_时间戳.xlsx」（同秒冲突加 `_2` 计数，永不覆盖）：「汇总」sheet 按负责人聚合（可直接复制进群催办），「明细」sheet 行级错误（Sheet/Excel行号/列名/当前值/问题描述/负责人，带 autofilter）；无行级错误的整表失败合成一条明细保证可见 |
| `validator.py` | Python 离线数据验证：`FIELD_CONSTRAINTS` 定义约束（与 DDL 一致），按行校验 NOT NULL、nvarchar 长度、date 格式（复用 `date_utils` 与 `importer._row_to_dict`），一次性收集选中 sheet 的所有错误 |
| `logger.py` | 记录导入/去重日志（开始/结束时间、状态含「部分成功（成功 X / 失败 Y）」、各表行数、失败表明细、错误名单路径），超 1MB 轮转为 `.bak`，msvcrt 文件锁避免多实例交错写入 |

### 核心数据流

```
启动 → 连接对话框（自动填充上次配置，含 Schema）
  ↓ 测试连接成功
主窗口
  ↓ 用户选择 .xlsx 文件（后台线程 zipfile 秒级读取 sheet 名，显示读取用时）
显示 sheet 概览（勾选框 + 序号 + Sheet名称 + 最后导入时间，默认全选）
  ├─→ 勾选 sheet → 点击"开始去重" → 去重设置对话框（模式/判重列，兼作确认） → 单遍流式去重
  │        ↓ 勾选的 Sheet 判重（空键保留、保留首现），未勾选的 Sheet 原样复制
  │      写出「原名_已去重.xlsx」（目标已存在自动加时间戳）+（如有删除）「原名_已去重__重复清单.csv」→ 记录日志
  │        ↓ 成功且未取消
  │      主窗口自动切换到输出文件（重建勾选为全选）→ 直接点"开始导入"入库
  ├─→ 勾选 sheet → 点击"验证数据" → 确认对话框（显示映射） → Python 离线校验选中 sheet（可选，排查用，不在每周例行流程中）
  └─→ 勾选 sheet → 点击"开始导入" → 确认对话框（显示映射） → 检查选中表是否存在 → 任一缺失则终止
         ↓ 全部存在
       工作线程内独立建连 → 逐表：BEGIN → DELETE → 批量 INSERT → COMMIT → 写入导入状态（成功）
         ↓（某表数据错误：仅该表回滚、记入失败表、继续下一表；连接级错误才中止全程）
       汇总「成功 X / 失败 Y」→ 有失败表时自动生成错误名单 xlsx（汇总+明细双 sheet）
         ↓ 成功或部分成功
       批量 SELECT COUNT(*)（UNION ALL）查询成功表实际行数
         ↓
       记录 import_log.txt → 主窗口刷新最后导入时间与失败红标
         ↓ 业务按名单修正后重新选择定稿文件
       加载文件时检测到失败 Sheet → 提示"只勾选上次失败的 Sheet" → 一键补录 → 状态翻正、红标消除
```

### 关键设计决策

1. **扁平模块而非框架化**：面向少量内部用户，不引入 MVC/MVVM 等框架，够用即可
2. **`importer.py` 作为编排器**：不把导入逻辑写在 UI 层，保持 UI 只做展示和交互
3. **逐表独立事务 + 失败继续**：每个表独立 `BEGIN TRANSACTION` → `DELETE` → `INSERT` → `COMMIT`。某表数据错误时仅该表回滚、记录失败并**继续导入后续表**（历史上的行为是首个失败即整体中止，导致 8.24 式连导四次）；仅连接断开等基础设施错误（`_connection_alive` 用 `SELECT 1` 探活判定）中止整个流程，中止前已提交的表保留
4. **DELETE 而非 TRUNCATE**：清空目标表使用 `DELETE FROM`，兼容无 TRUNCATE 权限的数据库账号
5. **本地 SQLite 替代 config.ini**：`local.db` 与 exe 同目录，含 `db_connections` 表（连接配置 + 登录自动填充，`schema_name` 与 `is_last_used` 标记上次连接）、`sheet_names` 表（46 条 sheet→table_name 映射 + `last_import_time`）、`column_mapping` 表（列映射 + `constraint_desc` 约束说明）、`dedup_settings` 表（去重模式与判重列），首次启动自动建表、迁移新增列并从 `sheet_names.txt` 播种
6. **错误集中处理**：联系信息集中在 `app/constants.py` 的 `ERROR_CONTACT`，所有异常向上抛到 UI 层统一弹窗；`main.py` 注册全局 `sys.excepthook` 兜底
7. **单元格级错误诊断**：批量插入失败时自动降级为逐行重试，按数据库错误类型分组输出全部出错行号与列值样例，定位到具体 Sheet、Excel 行号和列名，便于快速排查数据质量问题
8. **Python 离线验证优于 DB 验证**：约束简单（2 个 NOT NULL + 8 个长度限制 + 1 个日期校验），纯内存操作速度快，可一次性收集全部 sheet 的所有错误，无需数据库连接；验证与导入共用 `date_utils` 的日期解析，保证两边判断一致
9. **导入后 SQL COUNT(*) 核实行数**：导入流程不在内存中计算行数，而是在事务提交后通过批量 `SELECT COUNT(*)`（UNION ALL 合并单次往返）查询数据库实际行数并展示，确保数据准确
10. **确认对话框不含行数统计**：确认对话框中仅展示 sheet→表名映射（3 列），不预先计算行数，确认按钮立即可用，无需等待
11. **Excel 文件与 SQL 查询的性能优化**：导入/验证全程只打开一次 workbook 复用；sheet 名用 zipfile 秒级解析；column_mapping 结果模块级缓存；表存在性检查与导入后 COUNT(*) 均合并为单次批量 SQL 查询，大幅减少网络往返
12. **`BaseTaskDialog` 统一任务展示**：导入/验证对话框继承同一基类（进度条、状态、已用时、日志区），UI 逻辑不复用不重复
13. **Schema 支持**：连接对话框新增 Schema 字段，`db_connections` 表存储 `schema_name`，所有 SQL 均带 schema 前缀；标识符与 ODBC 连接串值统一转义（方括号 / 花括号），避免特殊字符破坏 SQL 与连接串
14. **pyodbc 线程安全**：连接非线程安全，工作线程内独立创建连接，避免跨线程共享导致 HY010"函数序列错误"；每批插入使用独立 cursor，避免批量失败后 cursor 状态损坏影响后续批次
15. **日期解析统一**：日期归一化（`/`→`-`、`.`→`:`、全角冒号→半角）与 5 种格式解析收敛到 `date_utils.parse_date()`，导入与验证共用，避免 SQL Server「日期时间字段溢出」错误
16. **日志轮转与并发安全**：导入日志超 1MB 自动归档为 `.bak`，写入时用 msvcrt 文件锁，避免多实例交错写入
17. **去重单遍流式重写而非改写原文件**：去重不复用导入的行迭代（导入截断 11 列且跳空行，去重需全列保真），calamine 单遍读 + xlsxwriter `constant_memory` 逐行写出保留行——重复行根本不写入输出文件，旧去重工具（Go 引擎 XML 行级手术）「阶段2 残留删不净」类问题结构上不存在；输出永不覆盖任何已有文件：`_resolve_output_paths` 在目标 xlsx 或重复清单 CSV 已存在（或与源文件同名，即对已去重文件再去重）时整体加时间戳（xlsx 与 CSV 配对同一时间戳，同秒冲突再加 `_2` 计数），源文件名已带 `_已去重` 后缀或旧时间戳先归一再重建、不叠加后缀——实际写入路径必然不同于源文件，无原位替换场景（旧的 `.tmp` + `os.replace` 逻辑已随之删除）
18. **错误发现内建于导入、独立验证退出例行流程**：导入器逐批做 NOT NULL / 日期预检，坏行在导入时即被完整收集（整 sheet 扫描完才判失败），错误发现与导入天然一次完成；「验证数据」功能保留为可选离线检查（不写库、排查用），但每周例行流程不再包含独立验证步骤，避免同一套约束检查两遍
19. **结构化错误 + 名单同源**：行级错误收集为结构化 dict（`row`/`message`/`kind`/`fields`/`values`），导入日志文本（`_format_sheet_errors` 分组区间+样例）与错误名单 xlsx（`error_list.generate_error_list`：负责人汇总 + 行级明细）从同一份数据生成；名单在源文件同目录自动落盘、带时间戳永不覆盖，业务侧可直接筛选
20. **失败表按表名记忆、跨文件一键补录**：失败状态持久化到 `sheet_names.last_import_status`（'success'/'failed'，NULL 表示未尝试），不依赖文件名——定稿文件每周改名也能对上；主窗口概览给失败 Sheet 红标+tooltip，加载新文件时检测交集并弹「只勾选失败 Sheet」提示，补录成功后状态翻正、红标消除（解决失败表在库内长期隐性过期无人察觉的问题）

---

## 使用指南

### 数据源结构

所有 46 个 sheet 共 11 列，部分 sheet 第 2 列名为 `小组` 而非 `负责人`，Sheet 046 多出第 12 列 `匹配类型`。

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

1. **配置数据库连接**：启动程序后弹出连接对话框，填写服务器地址、数据库名、Schema（默认 dbo）、用户名、密码，点击「测试连接」，连接成功后方可进入主窗口（自动填充上次配置）
2. **选择 Excel 文件**：在主窗口选择 `.xlsx` 文件（如 `信息源8.8_已去重.xlsx`），程序后台线程秒级读取全部 sheet（不阻塞界面），概览中显示每个 sheet 的序号、名称及最后导入时间
3. **勾选要处理的 sheet**：默认全选，可通过「全选」复选框或逐行勾选调整范围
4. **去重（可选，每周例行）**：点击「开始去重」→ 在去重设置中选择模式（默认全局去重，每周例行推荐）与判重列（默认 D 企业名称）→ 确认后执行；输出「原名_已去重.xlsx」（未勾选的 Sheet 原样复制；目标已存在自动加时间戳、永不覆盖）与「原名_已去重__重复清单.csv」对照清单，成功后主窗口自动切换到去重后文件
5. **导入（失败自动跳过）**：
   - 点击「开始导入」：先在确认对话框中核对 sheet→表名映射，确认后执行导入
   - 某张表导入失败不中断：该表自动回滚、跳过，继续导入后续表；结束汇总「成功 X / 失败 Y」
   - 有失败表时自动在源文件同目录生成「源文件名__导入错误名单_时间戳.xlsx」：汇总页按负责人统计（可直接复制进群催办），明细页含 Sheet、Excel 行号、列名、当前值、问题描述
6. **修正与补录**：把错误名单发业务人员修正；修正后重新选择定稿文件，程序自动提示「只勾选上次失败的 Sheet」，确认后「开始导入」一键补录（失败的 Sheet 在概览中标红，补录成功后消除）
7. **查看结果**：导入完成后展示各表实际行数（数据库批量 `SELECT COUNT(*)`）与成功/失败汇总；每表成功后自动更新「最后导入时间」

### 配置管理

| 配置项 | 位置 | 说明 |
|---|---|---|
| 数据库连接 | 连接对话框 / SQLite `db_connections` | 含服务器、库名、Schema、用户名、密码，自动保存，启动时自动填充上次配置（`is_last_used` 标记） |
| Sheet名-表映射 | 菜单「Sheet名-表映射」（`Ctrl+N`） | 展示全部 46 条映射（序号、Sheet名称、数据库表名、最后导入时间），支持搜索筛选、双击编辑、新增、右键删除 |
| 列映射 | 菜单「列映射」 | 展示 Excel 列→数据库字段映射（序号、Excel列、数据库字段、Excel索引、说明、约束说明） |
| 去重设置 | 去重设置弹窗 / SQLite `dedup_settings` | 去重模式（默认全局去重）与判重列（默认 D 企业名称），确认去重时自动保存，下次打开自动填充 |

### 部署与打包

- 使用 PyInstaller 打包为单个 .exe 文件，在 Windows 上直接运行（`pyinstaller build.spec`）
- 本地 SQLite 数据库 `local.db` 与 exe 同目录，存储数据库连接信息（`db_connections` 表）、sheet 名称映射（`sheet_names` 表）、列映射（`column_mapping` 表）和去重设置（`dedup_settings` 表），首次启动自动建表并从 `sheet_names.txt` 播种
- 最终用户无需安装 Python 或任何依赖
- 远程数据库表结构由开发者提前在 SQL Server 中建好，工具本身不建表
- 导入/去重日志输出到 exe 同目录的 `import_log.txt`（超 1MB 轮转为 `.bak`），便于追溯历史

---

## 注意事项

- **关窗行为**：主窗口点 ✕ 每次弹窗询问「直接退出（默认）/最小化到托盘/取消」（取消按钮、Esc、点弹窗 ✕ 均为取消关窗——QMessageBox 不显式 setEscapeButton(取消) 时 Esc/✕ 会误触默认按钮「直接退出」）；最小化到托盘后双击图标恢复，右键托盘「退出」彻底退出（任务运行中拒绝退出）；托盘不可用的环境直接退出不询问
- **全量覆盖导入**：每次导入先清空目标表再插入全部数据，请确认勾选范围后再执行
- **逐表独立事务且失败不中断**：某表导入失败仅该表回滚，其余表照常导入并记录 `last_import_time`；连接中断等严重错误才中止整个流程（中止前已成功的表保留）
- **失败表记忆与一键补录**：失败状态按表名持久化（`sheet_names.last_import_status`），主窗口红标提示；加载新文件时自动提示只勾选失败 Sheet 补录，跨文件名有效
- **错误名单**：有失败表时自动生成于源文件同目录（带时间戳、永不覆盖），汇总页按负责人统计可直接复制进群催办，明细页可筛选；「打开错误名单」按钮一键打开
- **清空方式为 DELETE**：目标表使用 `DELETE FROM` 清空（而非 TRUNCATE），兼容无 TRUNCATE 权限的账号
- **表缺失检查**：导入前检查选中表是否全部存在，任一缺失则终止导入并弹窗提示
- **Schema 支持**：连接对话框可指定 Schema（默认 dbo），所有表名查询均带 schema 前缀
- **日期格式兼容**：Excel 日期可能被 python-calamine 读为 `datetime.datetime`（含时间部分）或字符串（如 `'2026-02-02 00:00:00'`、`'2026/2/2 0:00'`、`'2026/7/4 13.29'`、`'2026/4/20/09:50'`、`'2026/5/27/11：27'`），程序通过 `date_utils` 统一归一化（`/`→`-`、`.`→`:`、全角冒号→半角）后按 5 种格式解析为纯 `datetime.date`，避免 SQL Server「日期时间字段溢出」错误
- **可空列空值处理**：nullable nvarchar 列的 `None` 自动转为空字符串 `""`，避免 pyodbc `fast_executemany` 因类型推断过窄导致 "String data, right truncation" 错误
- **行号追踪**：Excel 空行会被跳过，报错诊断时以实际行号（而非物理行号）定位 Sheet、Excel 行号、列名及单元格值；同类错误按数据库报错分组展示
- **错误处理**：所有错误统一弹窗提示，附带联系信息（`ERROR_CONTACT`）；「使用说明」菜单中亦可查看使用流程与联系人
- **验证功能定位**：「验证数据」保留为可选的离线检查（NOT NULL、字段长度、日期格式，不写库），用于导入前抽查或排查疑难；每周例行流程直接导入——导入器内置 NOT NULL/日期预检，坏行在导入时即被完整收集并汇总，无需预先单独验证
- **数据去重**：判重键 = 判重列值去首尾空白并全角转半角；判重列为空的行不参与判重、原样保留（导入时由 NOT NULL 预检报错）；保留首次出现、整行删除后续重复（含 Sheet 046 第 12 列在内的全列保真）；未勾选的 Sheet 原样复制进输出文件；输出永不覆盖任何已有文件（目标已存在自动加时间戳，对已去重文件再去重也生成新时间戳副本、不原位更新）；重复清单 `__重复清单.csv` 为长表对照（处理/Sheet名称/Excel行号/判重列原始值，保留行与其全部删除行相邻，各自显示自己的原始值，全角/半角差异可见）；判重列选 L 匹配类型时，无第 12 列的 sheet 键全为空、自然退化为仅复制，属预期行为
- **去重取消**：中途取消则输出文件仅含已处理 Sheet（未完成的 Sheet 会在结果中标注），且不自动切换文件；输出文件被 Excel 占用时提示关闭后重试
