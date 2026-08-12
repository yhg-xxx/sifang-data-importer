# 四方数据导入工具

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
| `local.db` | 本地 SQLite 数据库（首次启动自动生成），含 `db_connections`（连接配置/登录）、`sheet_names`（sheet→表名映射）、`column_mapping`（Excel 列→DB 字段映射）三张表 |
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
- 记录导入日志（开始时间、结束时间、各表行数、成功/失败状态），日志超 1MB 自动轮转
- 所有错误统一弹窗提示，附带联系信息（集中在 `app/constants.py`）："发生错误，请联系世贸项目部-数据组-王霖霖，世贸项目部-数据组-张同宁"
- 支持勾选部分 sheet 进行验证/导入（通过 SQLite `sheet_names` 表映射 sheet→表名）
- 导入失败时自动逐行诊断，按错误类型分组输出，定位到具体 Sheet、Excel 行号、列名及单元格值，并记录原始数据库报错信息
- 点击「验证数据」按钮可对 Excel 数据做离线校验（NOT NULL、字段长度、日期格式），一次性找出所有错误并展示，避免导入时逐个报错中断
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
| Excel 读取 | openpyxl（数据流式读取）+ zipfile（sheet 名秒级解析） |
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
│   ├── date_utils.py            # 日期解析工具（验证与导入共用同一套格式与归一化逻辑）
│   ├── excel_reader.py          # Excel 文件读取（zipfile 读 sheet 名 + openpyxl 流式读数据）
│   ├── importer.py              # 导入编排器（协调 database + excel_reader）
│   ├── validator.py             # 数据验证（NOT NULL、长度、日期格式离线校验）
│   └── logger.py                # 日志记录（import_log.txt，1MB 轮转，多实例文件锁）
├── ui/                          # 界面层（PySide6）
│   ├── __init__.py
│   ├── main_window.py           # 主窗口：文件选择、Sheet 概览（勾选框+最后导入时间）、验证/导入入口
│   ├── base_task_dialog.py      # 任务进度对话框基类（进度条、状态、已用时、日志区、关闭按钮）
│   ├── connection_dialog.py     # 数据库连接对话框（服务器/库名/Schema/用户名/密码）
│   ├── import_dialog.py         # 导入进度/结果展示（继承 BaseTaskDialog）
│   ├── validate_dialog.py       # 验证数据进度/结果展示（继承 BaseTaskDialog）
│   ├── confirm_dialog.py        # 确认对话框（展示选中 sheet→表名映射）
│   ├── sheet_directory_dialog.py # Sheet名-表映射对话框（支持增删改查、筛选）
│   └── column_mapping_dialog.py  # 列映射对话框（含约束说明）
├── local.db                     # 运行时生成的本地 SQLite 数据库（与 exe 同目录）
├── import_log.txt               # 运行时生成的导入日志
├── requirements.txt
└── build.spec                   # PyInstaller 打包配置
```

### 各层职责

**UI 层（`ui/`）**

| 模块 | 职责 |
|---|---|
| `main_window.py` | 主窗口：文件选择（后台线程读取、显示读取用时）、Sheet 概览（勾选框 + 序号 + Sheet名称 + 最后导入时间）、全选 checkbox、验证/导入操作入口、菜单栏（Sheet名-表映射/列映射/使用说明） |
| `base_task_dialog.py` | 任务进度对话框基类：进度条、状态文字、已用时间、日志区、关闭按钮；子类实现 `_run_worker()` / `_on_finished()` |
| `connection_dialog.py` | 启动时弹出，填写服务器/库名/Schema/用户名/密码，后台线程测试连接，成功后保存配置并返回 `connection` 与 `schema` |
| `import_dialog.py` | 继承 BaseTaskDialog；工作线程内独立创建 pyodbc 连接（避免跨线程共享），导入成功后通过批量 `SELECT COUNT(*)`（UNION ALL）查询数据库实际行数 |
| `validate_dialog.py` | 继承 BaseTaskDialog；展示数据验证进度条和结果日志 |
| `confirm_dialog.py` | 确认对话框：展示选中 sheet→表名映射（3 列），用户确认后执行操作 |
| `sheet_directory_dialog.py` | Sheet名-表映射对话框：展示全部 sheet→表名映射（含最后导入时间），支持搜索筛选（防抖）、双击编辑、新增、右键删除 |
| `column_mapping_dialog.py` | 列映射对话框：展示 Excel 列→数据库字段映射（序号、Excel列、数据库字段、Excel索引、说明、约束说明） |

**业务逻辑层（`app/`）**

| 模块 | 职责 |
|---|---|
| `constants.py` | 全局常量：`ERROR_CONTACT` 统一错误联系信息 |
| `config.py` | 封装 `local_db` 的连接读写接口，`load_config()` / `save_config()` 对外透明 |
| `local_db.py` | 本地 SQLite 数据库管理：`db_connections` 表（连接配置 + `schema_name` + `is_last_used`）、`sheet_names` 表（sheet→table_name 映射，含 `last_import_time`）、`column_mapping` 表（Excel 列→DB 字段，含 `constraint_desc` 约束说明）；`init_db()` 首次建表并播种，自动迁移新增列并回填约束说明；CRUD：`add_sheet_mapping()` / `update_sheet_mapping()` / `delete_sheet_mapping()` / `update_last_import_time()` |
| `database.py` | `connect()`（ODBC 连接串值花括号转义）/ `test_connection()` / `check_tables_exist()`（单次 IN 查询）/ `delete_all_tables()`（DELETE 清空，兼容无 TRUNCATE 权限）/ `insert_batch()`（fast_executemany）/ `count_tables_rows_batch()`（UNION ALL 批量 COUNT）；所有 SQL 均带 schema 前缀并转义标识符 |
| `date_utils.py` | 日期解析：`DATE_FORMATS`（5 种格式）、`normalize_date_str()`（`/`→`-`、`.`→`:`、全角冒号→半角）、`parse_date()` 统一转为纯 `datetime.date` |
| `excel_reader.py` | `read_sheets()` 用 zipfile 解析 workbook.xml 秒级读取全部 sheet 名；`iter_sheet_rows_from_workbook()` 从已打开的 workbook 流式读取（跳过表头、跳过空行、截断到 11 列），返回 `(批次起始行号, [(实际Excel行号, 行数据)])` |
| `importer.py` | 编排导入流程：检查表 → 逐表（DELETE 清空 → 流式批量插入 → 提交）→ 更新 last_import_time；`_row_to_dict()` 将 Excel 行转为数据库字段 dict（collected_at 走 `date_utils`，nullable 空值转 `""`）；`_diagnose_batch()` 批量失败时逐行定位；`_format_sheet_errors()` 按错误类型分组输出 |
| `validator.py` | Python 离线数据验证：`FIELD_CONSTRAINTS` 定义约束（与 DDL 一致），按行校验 NOT NULL、nvarchar 长度、date 格式（复用 `date_utils` 与 `importer._row_to_dict`），一次性收集选中 sheet 的所有错误 |
| `logger.py` | 记录导入日志（开始/结束时间、各表行数、状态），超 1MB 轮转为 `.bak`，msvcrt 文件锁避免多实例交错写入 |

### 核心数据流

```
启动 → 连接对话框（自动填充上次配置，含 Schema）
  ↓ 测试连接成功
主窗口
  ↓ 用户选择 .xlsx 文件（后台线程 zipfile 秒级读取 sheet 名，显示读取用时）
显示 sheet 概览（勾选框 + 序号 + Sheet名称 + 最后导入时间，默认全选）
  ├─→ 勾选 sheet → 点击"验证数据" → 确认对话框（显示映射） → Python 离线校验选中 sheet
  └─→ 勾选 sheet → 点击"开始导入" → 确认对话框（显示映射） → 检查选中表是否存在 → 任一缺失则终止
         ↓ 全部存在
       工作线程内独立建连 → 逐表：BEGIN → DELETE → 批量 INSERT → COMMIT → 写入 last_import_time
         ↓（某表失败仅该表回滚，前表已提交保留；失败批次自动逐行诊断）
       批量 SELECT COUNT(*)（UNION ALL）查询各表实际行数
         ↓
       记录 import_log.txt
         ↓
       显示导入结果（各表行数、耗时）
```

### 关键设计决策

1. **扁平模块而非框架化**：面向少量内部用户，不引入 MVC/MVVM 等框架，够用即可
2. **`importer.py` 作为编排器**：不把导入逻辑写在 UI 层，保持 UI 只做展示和交互
3. **逐表独立事务**：每个表独立 `BEGIN TRANSACTION` → `DELETE` → `INSERT` → `COMMIT`。某表失败时该表回滚，前表已提交的数据不受影响，避免了一个表出错导致全部表回滚的问题
4. **DELETE 而非 TRUNCATE**：清空目标表使用 `DELETE FROM`，兼容无 TRUNCATE 权限的数据库账号
5. **本地 SQLite 替代 config.ini**：`local.db` 与 exe 同目录，含 `db_connections` 表（连接配置 + 登录自动填充，`schema_name` 与 `is_last_used` 标记上次连接）、`sheet_names` 表（46 条 sheet→table_name 映射 + `last_import_time`）、`column_mapping` 表（列映射 + `constraint_desc` 约束说明），首次启动自动建表、迁移新增列并从 `sheet_names.txt` 播种
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
4. **验证或导入**：
   - 点击「验证数据」：离线校验选中 sheet（NOT NULL、字段长度、日期格式），一次性展示所有错误
   - 点击「开始导入」：先在确认对话框中核对 sheet→表名映射，确认后执行导入
5. **查看结果**：导入完成后展示各表实际行数（数据库批量 `SELECT COUNT(*)`）与耗时；每表成功后自动更新「最后导入时间」

### 配置管理

| 配置项 | 位置 | 说明 |
|---|---|---|
| 数据库连接 | 连接对话框 / SQLite `db_connections` | 含服务器、库名、Schema、用户名、密码，自动保存，启动时自动填充上次配置（`is_last_used` 标记） |
| Sheet名-表映射 | 菜单「Sheet名-表映射」（`Ctrl+N`） | 展示全部 46 条映射（序号、Sheet名称、数据库表名、最后导入时间），支持搜索筛选、双击编辑、新增、右键删除 |
| 列映射 | 菜单「列映射」 | 展示 Excel 列→数据库字段映射（序号、Excel列、数据库字段、Excel索引、说明、约束说明） |

### 部署与打包

- 使用 PyInstaller 打包为单个 .exe 文件，在 Windows 上直接运行（`pyinstaller build.spec`）
- 本地 SQLite 数据库 `local.db` 与 exe 同目录，存储数据库连接信息（`db_connections` 表）、sheet 名称映射（`sheet_names` 表）和列映射（`column_mapping` 表），首次启动自动建表并从 `sheet_names.txt` 播种
- 最终用户无需安装 Python 或任何依赖
- 远程数据库表结构由开发者提前在 SQL Server 中建好，工具本身不建表
- 导入日志输出到 exe 同目录的 `import_log.txt`（超 1MB 轮转为 `.bak`），便于追溯导入历史

---

## 注意事项

- **全量覆盖导入**：每次导入先清空目标表再插入全部数据，请确认勾选范围后再执行
- **逐表独立事务**：某表导入失败时仅该表回滚，前表已提交的数据保留；已成功的表会记录 `last_import_time`
- **清空方式为 DELETE**：目标表使用 `DELETE FROM` 清空（而非 TRUNCATE），兼容无 TRUNCATE 权限的账号
- **表缺失检查**：导入前检查选中表是否全部存在，任一缺失则终止导入并弹窗提示
- **Schema 支持**：连接对话框可指定 Schema（默认 dbo），所有表名查询均带 schema 前缀
- **日期格式兼容**：Excel 日期可能被 openpyxl 读为 `datetime.datetime`（含时间部分）或字符串（如 `'2026-02-02 00:00:00'`、`'2026/2/2 0:00'`、`'2026/7/4 13.29'`、`'2026/4/20/09:50'`、`'2026/5/27/11：27'`），程序通过 `date_utils` 统一归一化（`/`→`-`、`.`→`:`、全角冒号→半角）后按 5 种格式解析为纯 `datetime.date`，避免 SQL Server「日期时间字段溢出」错误
- **可空列空值处理**：nullable nvarchar 列的 `None` 自动转为空字符串 `""`，避免 pyodbc `fast_executemany` 因类型推断过窄导致 "String data, right truncation" 错误
- **行号追踪**：Excel 空行会被跳过，报错诊断时以实际行号（而非物理行号）定位 Sheet、Excel 行号、列名及单元格值；同类错误按数据库报错分组展示
- **错误处理**：所有错误统一弹窗提示，附带联系信息（`ERROR_CONTACT`）；「使用说明」菜单中亦可查看使用流程与联系人
- **验证功能**：建议导入前先点击「验证数据」，可离线一次性发现全部数据问题，避免导入时逐个报错中断
