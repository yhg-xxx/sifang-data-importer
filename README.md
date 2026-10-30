# 四方信息源入库

> 将 Excel 文件中 40+ 个 Sheet（当前 46 个）的数据批量导入 SQL Server 的桌面工具。

## 功能简介

- **数据库连接管理**：启动时自动尝试上次使用的连接，失败则打开「数据库连接管理」；可保存多条连接、新增 / 删除、测试连接（后台线程 + 遮罩提示，不阻塞界面）
- **秒级读取 Sheet 名**：选择 `.xlsx` 后由 zipfile 解析 `xl/workbook.xml`，读取期间界面不阻塞
- **勾选与映射**：Sheet 概览默认全选，支持 Shift 区间勾选；按本地 `sheet_names` 映射写入 `enterprise_info_001~046`
- **数据去重（可选，每周例行）**：按 Sheet 内 / 全局两种模式，判重列可选（默认 D 企业名称）；同一企业保留录入时间最早的行；输出全格式保真副本 + 重复清单 CSV
- **批量导入**：每批 5000 行、`fast_executemany`；逐表独立事务，先 DELETE 清空目标表再插入
- **失败自动跳过**：某表导入失败仅回滚该表并继续后续表；仅连接级错误中止整个流程
- **错误名单**：有失败表时自动生成「汇总 + 明细」双 Sheet xlsx，定位到 Sheet、Excel 行号、列名、当前值、问题描述
- **失败表记忆与一键补录**：失败状态按表名持久化，概览中标红；加载新文件时提示「只勾选上次失败的 Sheet」
- **可选离线验证**：「验证数据」校验 NOT NULL、字段长度、日期格式，不写库，用于排查疑难
- **导入内建预检**：NOT NULL / 日期 / 长度在导入时即拦截，批量插入失败自动逐行诊断
- **错误中文化**：ODBC / SQL Server 原始报错翻译为可读中文
- **配套能力**：列映射只读查看、Sheet名-表映射可编辑（支持筛选与批量替换）、系统托盘、Toast 轻提示、统一亮色主题、日志 1MB 轮转、可打包为单文件 exe

## 技术栈

| 层 | 技术 |
|---|---|
| 语言 | Python 3.13+（当前开发环境 3.13.2） |
| 桌面 GUI | PySide6 6.11.1 |
| Excel 读取 | python-calamine 0.8.2（数据）+ zipfile（Sheet 名与 XML 条目） |
| Excel 写出 | 去重：XML 手术（全格式保真）；错误名单：xlsxwriter 3.2.9 |
| 远程数据库 | pyodbc 5.3.0（SQL Server，ODBC Driver 17） |
| 本地数据库 | SQLite（sqlite3 标准库） |
| 打包 | PyInstaller 6.21.0 |

## 目录结构

```
sifang-data-importer/
├── main.py                      # 应用入口：初始化本地库/主题/托盘、自动连接、连接管理循环
├── app/                         # 业务逻辑层
│   ├── config.py                # 连接配置读写（经由 local_db）
│   ├── constants.py             # 全局常量（统一错误联系信息）
│   ├── local_db.py              # 本地 SQLite（连接/映射/列映射/去重设置，建表迁移播种）
│   ├── database.py              # SQL Server 连接、表检查、批量插入、批量 COUNT、清空
│   ├── date_utils.py            # 日期归一化与解析（验证与导入共用）
│   ├── excel_reader.py          # zipfile 读 Sheet 名 + calamine 流式分行读取
│   ├── importer.py              # 导入编排器（逐表事务、预检、错误收集、日志与名单）
│   ├── validator.py             # 离线数据验证（NOT NULL/长度/日期）
│   ├── dedup.py                 # 数据去重（扫描定保留 + XML 手术写出 + 重复清单）
│   ├── xlsx_surgery.py          # xlsx XML 手术引擎（行级删行/重排 + 引用修正）
│   ├── error_list.py            # 导入错误名单 xlsx（汇总 + 明细）
│   ├── error_msgs.py            # 数据库/ODBC 报错中文化
│   ├── utils.py                 # 列字母、行号区间合并、判重键规范化、时间戳命名
│   └── logger.py                # 导入/去重日志（1MB 轮转、多实例文件锁）
├── ui/                          # 界面层（PySide6）
│   ├── main_window.py           # 主窗口：文件选择、Sheet 概览、失败红标、去重/验证/导入入口
│   ├── base_task_dialog.py      # 任务进度对话框基类（进度/状态/用时/日志/关闭）
│   ├── connection_dialog.py     # 数据库连接管理（多连接列表、测试/连接）
│   ├── import_dialog.py         # 导入进度与结果（含「打开错误名单」）
│   ├── validate_dialog.py       # 验证进度与结果（错误表格 + 类型筛选）
│   ├── dedup_settings_dialog.py # 去重设置（模式/判重列，摘要兼确认）
│   ├── dedup_dialog.py          # 去重进度与结果（支持取消）
│   ├── confirm_dialog.py        # 导入/验证前的映射确认
│   ├── sheet_directory_dialog.py# Sheet名-表映射管理（搜索/编辑/新增/删除/批量替换）
│   ├── column_mapping_dialog.py # 列映射只读展示
│   ├── help_dialog.py           # 使用说明窗口（目录胶囊跳转）
│   ├── help_content.py          # 使用说明正文（HTML）
│   ├── theme.py                 # 全局亮色主题 QSS
│   ├── toast.py                 # 顶部居中堆叠的非阻塞轻提示
│   └── tray.py                  # 系统托盘图标与菜单
├── assets/
│   ├── icon.png                 # 托盘/窗口图标源文件（运行时圆角遮罩）
│   ├── icon.ico                 # exe 文件图标
│   └── icon_rounded_256.png     # 圆角图标预览
├── 数据规范.png                 # 数据规范参考图（人工查看，程序不引用）
├── 每周入库流程.html            # 每周例行操作说明（人工查看，程序不引用）
├── sheet_names.txt              # 初始 Sheet 名列表（首次启动播种到 SQLite）
├── create_all_tables.sql        # 目标表建表 DDL
├── requirements.txt
├── build.spec                   # PyInstaller 打包配置
├── local.db                     # 运行时生成（与 exe 同目录）
└── import_log.txt               # 运行时生成（超 1MB 轮转为 .bak）
```

## 使用流程

1. **连接数据库**：启动后自动尝试上次使用的连接；失败则打开「数据库连接管理」，可新增 / 删除连接，填写服务器、数据库、Schema（默认 dbo）、用户名、密码，点击「测试连接」成功后「连接」进入主窗口
2. **选择 Excel 文件**：后台读取全部 Sheet 名称，概览显示序号、名称与最后导入时间
3. **勾选要处理的 Sheet**：默认全选；可逐行勾选，或先点起始行再 Shift 点击结束行批量勾选；底部「全选」一键切换
4. **数据去重（可选，每周例行）**：点击「开始去重」→ 选择模式（默认全局去重）与判重列（默认 D 企业名称）→ 输出「原名_已去重.xlsx」与重复清单 CSV；成功后自动切换到去重后文件
5. **开始导入（失败自动跳过）**：核对映射后逐表执行「清空 → 批量插入 → 提交」；某表失败自动回滚并跳过，结束汇总「成功 X / 失败 Y」并展示数据库实际行数
6. **处理错误名单**：有失败表时自动在源文件同目录生成错误名单 xlsx；「汇总」页按负责人统计，「明细」页可筛选定位
7. **修正与补录**：业务修正后重新选择定稿文件，按提示「只勾选上次失败的 Sheet」一键补录，成功后红标消除

## 安装与运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包为 exe

```bash
pyinstaller build.spec
```

`build.spec` 会打包 `sheet_names.txt` 与 `assets/icon.png`，exe 图标使用 `assets/icon.ico`。

## 说明

- 目标表结构需提前在 SQL Server 中建好（参考 `create_all_tables.sql`），工具本身不建表
- 每次导入为全量覆盖：先清空目标表再插入全部数据
- 导入/去重日志输出到 exe 同目录的 `import_log.txt`（超 1MB 自动轮转为 `.bak`）
- 本地配置与状态存于 exe 同目录的 `local.db`（首次启动自动建表并从 `sheet_names.txt` 播种）

## 遇到问题

所有错误均会弹窗提示。本工具为内部使用，如需帮助请联系：

**世贸项目部-数据组-王霖霖，世贸项目部-数据组-张同宁**
