"""数据库操作 - 连接、检查、批量导入"""
from typing import Any

import pyodbc

# SQL Server ODBC 驱动候选名，按优先级排列。
# 各台机器装的驱动版本不一致（一个都没装时报 IM002「未发现数据源名称」），
# 写死 17 会让只装了 18 的机器连不上，故运行时探测第一个已安装的。
# 17 排在 18 前面：17 默认不加密，与程序原有行为完全一致；18 默认强制加密，
# 连内网自签名证书的服务器会报「证书链不受信任」——能装 17 的机器保持原样。
_DRIVER_CANDIDATES = (
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "ODBC Driver 11 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
)

# 驱动 18 起 Encrypt 默认改为 yes，显式关掉以复现驱动 17 的默认行为
_DRIVER_EXTRA_PARAMS = {
    "ODBC Driver 18 for SQL Server": {"Encrypt": "no"},
}

# 查询超时（秒）：pyodbc 默认无限等待，目标表被他人锁住时
# DELETE/INSERT 会永久阻塞且导入无取消入口
QUERY_TIMEOUT_SECONDS = 300


class DriverNotFoundError(Exception):
    """本机未安装任何 SQL Server ODBC 驱动。"""


def get_driver_name() -> str:
    """返回本机已安装的 SQL Server ODBC 驱动名（按 _DRIVER_CANDIDATES 优先级）。

    pyodbc.drivers() 只列出与当前 Python 位数一致的驱动：本程序为 64 位，
    因此只装了 32 位驱动的机器同样探测不到。不缓存探测结果，装完驱动回来
    直接点「测试连接」即可生效，无需重启程序。
    """
    installed = set(pyodbc.drivers())
    for name in _DRIVER_CANDIDATES:
        if name in installed:
            return name
    raise DriverNotFoundError(
        "未安装数据库驱动：这台电脑上找不到任何 SQL Server ODBC 驱动"
        "（需 64 位，与本程序位数一致）。请到微软官网下载安装"
        "「Microsoft ODBC Driver 17 for SQL Server (x64)」，"
        "装完回来再点一次「测试连接」即可。与网络、账号密码无关。"
    )


def _quote_conn_value(value: str) -> str:
    """转义连接串值：用花括号包裹，内部 } 加倍（ODBC 标准转义）。

    密码等值可能含 ; { } 字符，直接拼接会破坏连接串结构。
    空值无需包裹。
    """
    if not value:
        return ""
    return "{" + value.replace("}", "}}") + "}"


def connect(server: str, database: str, username: str, password: str) -> pyodbc.Connection:
    """连接 SQL Server，返回连接对象。失败时抛出异常。

    通过 pyodbc 关键字参数构造连接串（user→uid、password→pwd 自动转换），
    所有值统一做花括号转义，避免特殊字符破坏连接串。
    timeout=10 为登录超时；连接后另设查询超时（conn.timeout）。
    """
    driver = get_driver_name()
    conn = pyodbc.connect(
        driver=_quote_conn_value(driver),
        server=_quote_conn_value(server),
        database=_quote_conn_value(database),
        user=_quote_conn_value(username),
        password=_quote_conn_value(password),
        timeout=10,
        **_DRIVER_EXTRA_PARAMS.get(driver, {}),
    )
    conn.timeout = QUERY_TIMEOUT_SECONDS
    return conn


def test_connection(server: str, database: str, username: str, password: str) -> tuple[bool, str]:
    """测试数据库连接，返回 (是否成功, 消息)。"""
    try:
        conn = connect(server, database, username, password)
        conn.close()
        return True, "连接成功"
    except pyodbc.Error as e:
        return False, str(e)


def _quote_identifier(name: str) -> str:
    """将标识符用方括号包裹，避免 SQL 注入和关键字冲突。"""
    return "[" + name.replace("]", "]]") + "]"


def _full_table_name(schema: str, table: str) -> str:
    """返回完整的带 schema 前缀的表名。"""
    return f"{_quote_identifier(schema)}.{_quote_identifier(table)}"


def check_tables_exist(
    conn: pyodbc.Connection,
    table_names: list[str],
    schema: str = "dbo",
) -> tuple[bool, list[Any]] | None:
    """检查指定表名是否全部存在于数据库中。

    返回 (全部存在?, 缺失的表名列表)。
    使用单次 IN 查询，避免逐表网络往返。
    """
    if not table_names:
        return True, []

    cursor = conn.cursor()
    try:
        placeholders = ", ".join("?" for _ in table_names)
        cursor.execute(
            f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE' "
            f"AND TABLE_NAME IN ({placeholders})",
            (schema, *table_names),
        )
        existing = {row[0] for row in cursor.fetchall()}
        missing = [t for t in table_names if t not in existing]
        return len(missing) == 0, missing
    finally:
        cursor.close()


def count_table_rows(conn, table_name: str, schema: str = "dbo") -> None:
    """查询表中行数（通过 SELECT COUNT(*)）。"""
    cursor = conn.cursor()
    try:
        full_name = _full_table_name(schema, table_name)
        cursor.execute(f"SELECT COUNT(*) FROM {full_name}")
        return cursor.fetchone()[0]
    finally:
        cursor.close()


def count_tables_rows_batch(
    conn, table_names: list[str], schema: str = "dbo",
) -> dict[Any, Any] | None:
    """批量查询多张表的行数，用 UNION ALL 合并为单次网络往返。

    返回 {table_name: row_count, ...}。
    """
    if not table_names:
        return {}

    cursor = conn.cursor()
    try:
        full_names = [_full_table_name(schema, t) for t in table_names]
        parts = []
        for t, fn in zip(table_names, full_names):
            # 表名进字符串字面量，单引号需按 SQL 规则加倍（表名可经映射对话框编辑）
            literal = t.replace("'", "''")
            parts.append(f"SELECT '{literal}' AS tbl, COUNT(*) AS cnt FROM {fn}")
        sql = " UNION ALL ".join(parts)
        cursor.execute(sql)
        return {row[0]: row[1] for row in cursor.fetchall()}
    finally:
        cursor.close()


def delete_all_tables(cursor, table_names: list[str], schema: str = "dbo") -> None:
    """清空全部目标表（使用 DELETE，兼容无 TRUNCATE 权限的环境）。"""
    for table_name in table_names:
        full_name = _full_table_name(schema, table_name)
        cursor.execute(f"DELETE FROM {full_name}")


def insert_batch(cursor, table_name: str, rows: list[dict], schema: str = "dbo") -> None:
    """将一批行批量写入数据库（使用 fast_executemany 优化）。

    rows: [{字段名: 值}, ...]，每个 dict 的键即列名。
    """
    if not rows:
        return

    full_name = _full_table_name(schema, table_name)
    columns = list(rows[0].keys())
    col_names = ", ".join(_quote_identifier(c) for c in columns)
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {full_name} ({col_names}) VALUES ({placeholders})"

    values_batch = [[row.get(col) for col in columns] for row in rows]
    cursor.executemany(sql, values_batch)
