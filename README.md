# 四方数据导入工具

> 将 Excel 文件中 40+ 个 sheet 的数据批量导入 SQL Server 的桌面工具。

## 功能简介

- 启动后填写数据库连接参数（服务器、数据库、Schema、用户名、密码），测试连接成功后方可继续
- 选择 `.xlsx` 文件，秒级读取全部 sheet 名称（zipfile 解析，不阻塞界面）
- 按 sheet 名称匹配数据库表（`enterprise_info_001~046`），数据批量写入 SQL Server（每批 5000 行，`fast_executemany`）
- 每次导入逐表独立事务：先清空目标表（DELETE，兼容无 TRUNCATE 权限环境），再重新插入全部数据
- 支持勾选部分 sheet 验证/导入，导入前检查目标表是否存在
- 点击「验证数据」可离线校验（NOT NULL、字段长度、日期格式），一次性找出所有错误
- 导入失败时自动逐行诊断，按错误类型分组输出，定位到具体 Sheet、Excel 行号、列名及单元格值
- 记录导入日志，超 1MB 自动轮转
- 支持 PyInstaller 打包为单文件 exe

## 技术栈

| 层 | 技术 |
|---|---|
| 语言 | Python 3.14 |
| 桌面 GUI | PySide6（Qt for Python） |
| Excel 读取 | openpyxl + zipfile |
| 远程数据库 | pyodbc（SQL Server，ODBC Driver 17） |
| 本地数据库 | SQLite（sqlite3 标准库） |
| 打包 | PyInstaller |

## 目录结构

```
├── main.py                      # 应用入口
├── app/                         # 业务逻辑层
│   ├── config.py                # 配置管理（SQLite 读写连接参数）
│   ├── constants.py             # 全局常量（统一错误联系信息）
│   ├── local_db.py              # 本地 SQLite 管理（建表、迁移、播种、CRUD）
│   ├── database.py              # 数据库连接、表检查、批量插入、COUNT 查询
│   ├── date_utils.py            # 日期解析工具（验证与导入共用）
│   ├── excel_reader.py          # Excel 读取（zipfile 读 sheet 名 + openpyxl 流式读数据）
│   ├── importer.py              # 导入编排器
│   ├── validator.py             # 数据验证（NOT NULL、长度、日期格式离线校验）
│   └── logger.py                # 日志记录（1MB 轮转）
├── ui/                          # 界面层（PySide6）
│   ├── main_window.py           # 主窗口
│   ├── base_task_dialog.py      # 任务进度对话框基类
│   ├── connection_dialog.py     # 数据库连接对话框
│   ├── import_dialog.py         # 导入进度/结果展示
│   ├── validate_dialog.py       # 验证进度/结果展示
│   ├── confirm_dialog.py        # 确认对话框
│   ├── sheet_directory_dialog.py # Sheet名-表映射对话框
│   └── column_mapping_dialog.py  # 列映射对话框
├── sheet_names.txt              # 初始 sheet 名称列表（首次启动播种到 SQLite）
├── create_all_tables.sql        # 目标表建表 DDL
├── build.spec                   # PyInstaller 打包配置
└── requirements.txt
```

## 使用流程

1. **配置数据库连接**：启动后填写服务器、数据库名、Schema（默认 dbo）、用户名、密码，测试连接成功后可进入主窗口（自动填充上次配置）
2. **选择 Excel 文件**：后台线程秒级读取全部 sheet 名称
3. **勾选要处理的 sheet**：默认全选，可调整范围
4. **验证或导入**：「验证数据」离线校验；「开始导入」确认 sheet→表映射后执行
5. **查看结果**：展示各表实际行数与耗时

## 安装与运行

```bash
pip install -r requirements.txt
python main.py
```

## 打包为 exe

```bash
pyinstaller build.spec
```

## 说明

- 目标表结构需提前在 SQL Server 中建好（参考 `create_all_tables.sql`），工具本身不建表
- 每次导入为全量覆盖：先清空目标表再插入全部数据
- 导入日志输出到 exe 同目录的 `import_log.txt`
