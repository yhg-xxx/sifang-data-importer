"""本地 SQLite 数据库管理 - 连接配置表 + sheet 名称映射表"""

import os
import sqlite3
import sys
from datetime import datetime

DB_FILE_NAME = "local.db"

# ── DDL ──

CREATE_DB_CONNECTIONS = """
CREATE TABLE IF NOT EXISTS db_connections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    server      TEXT    NOT NULL,
    database    TEXT    NOT NULL,
    schema_name TEXT    NOT NULL DEFAULT 'dbo',
    username    TEXT    NOT NULL DEFAULT '',
    password    TEXT    NOT NULL DEFAULT '',
    is_last_used INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);
"""

CREATE_SHEET_NAMES = """
CREATE TABLE IF NOT EXISTS sheet_names (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    sheet_order      INTEGER NOT NULL,
    sheet_name       TEXT    NOT NULL,
    table_name       TEXT    NOT NULL,
    last_import_time TEXT
);
"""

CREATE_COLUMN_MAPPING = """
CREATE TABLE IF NOT EXISTS column_mapping (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    col_order       INTEGER NOT NULL,
    db_column       TEXT    NOT NULL,
    excel_index     INTEGER NOT NULL,
    description     TEXT    NOT NULL DEFAULT '',
    constraint_desc TEXT    NOT NULL DEFAULT ''
);
"""


def _get_db_dir() -> str:
    """获取数据库文件所在目录（与 exe 同目录，开发环境下为当前目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.getcwd()


def _get_db_path() -> str:
    return os.path.join(_get_db_dir(), DB_FILE_NAME)


def _get_conn() -> sqlite3.Connection:
    """获取 SQLite 连接（自动创建文件）。"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ═══════════════════════════════════════════════════
# 初始化
# ═══════════════════════════════════════════════════

def init_db() -> None:
    """初始化本地数据库：建表 + 首次运行时播种数据。"""
    conn = _get_conn()
    try:
        conn.execute(CREATE_DB_CONNECTIONS)
        conn.execute(CREATE_SHEET_NAMES)
        conn.execute(CREATE_COLUMN_MAPPING)

        # ── 迁移：为已有数据库添加 last_import_time 列 ──
        _migrate_add_column_if_missing(conn, "sheet_names", "last_import_time", "TEXT")

        # ── 迁移：为已有数据库添加 constraint_desc 列 ──
        _migrate_add_column_if_missing(conn, "column_mapping", "constraint_desc", "TEXT")
        _migrate_backfill_constraint_desc(conn)

        # 如果 sheet_names 表为空，从 sheet_names.txt 播种
        cur = conn.execute("SELECT COUNT(*) FROM sheet_names")
        if cur.fetchone()[0] == 0:
            _seed_sheet_names(conn)

        # 如果 column_mapping 表为空，播种默认映射
        cur = conn.execute("SELECT COUNT(*) FROM column_mapping")
        if cur.fetchone()[0] == 0:
            _seed_column_mapping(conn)

        conn.commit()
    finally:
        conn.close()


def _migrate_add_column_if_missing(conn, table: str, column: str, col_type: str) -> None:
    """如果表中不存在指定列，则添加（兼容已有数据库的迁移）。"""
    cur = conn.execute(f"PRAGMA table_info({table})")
    existing_cols = {row[1] for row in cur.fetchall()}
    if column not in existing_cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def _migrate_backfill_constraint_desc(conn: sqlite3.Connection) -> None:
    """为已有 column_mapping 记录补填约束说明（仅更新 constraint_desc 为空的记录）。"""
    backfill = {
        "collected_at":  "date 类型，可为空",
        "team":          "文本，最长50字，可为空",
        "source":        "文本，最长200字，可为空",
        "company_name":  "文本，最长500字，不能为空",
        "link":          "文本，最长1000字，可为空",
        "industry":      "文本，最长100字，不能为空",
        "sub_category_2":"文本，最长100字，可为空",
        "sub_category_3":"文本，最长100字，可为空",
        "org_type":      "文本，最长100字，可为空",
        "status":        "文本，最长200字，可为空",
        "system_reply":  "文本，不限长度，可为空",
    }
    for db_col, desc in backfill.items():
        conn.execute(
            "UPDATE column_mapping SET constraint_desc = ? "
            "WHERE db_column = ? AND (constraint_desc IS NULL OR constraint_desc = '')",
            (desc, db_col),
        )


def _seed_sheet_names(conn: sqlite3.Connection) -> None:
    """从 sheet_names.txt 读取数据，写入 sheet_names 表。

    sheet_name 存储完整行内容（与 Excel 中实际 sheet 名称一致）。
    """
    txt_path = os.path.join(_get_db_dir(), "sheet_names.txt")
    if not os.path.exists(txt_path) and getattr(sys, "frozen", False):
        # PyInstaller bundle 内查找
        txt_path = os.path.join(sys._MEIPASS, "sheet_names.txt")
    if not os.path.exists(txt_path):
        return

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    for i, line in enumerate(lines):
        order = i + 1
        table_name = f"enterprise_info_{order:03d}"
        line = line.strip()

        conn.execute(
            "INSERT INTO sheet_names (sheet_order, sheet_name, table_name) "
            "VALUES (?, ?, ?)",
            (order, line, table_name),
        )


def _seed_column_mapping(conn: sqlite3.Connection) -> None:
    """播种默认的 Excel 列 → 数据库字段映射。"""
    mappings = [
        (1,  "collected_at",  0, "日期",          "date 类型，可为空"),
        (2,  "team",          1, "负责人 / 小组",  "文本，最长50字，可为空"),
        (3,  "source",        2, "来源",           "文本，最长200字，可为空"),
        (4,  "company_name",  3, "企业名称",       "文本，最长500字，不能为空"),
        (5,  "link",          4, "官网",           "文本，最长1000字，可为空"),
        (6,  "industry",      5, "一级分类",       "文本，最长100字，不能为空"),
        (7,  "sub_category_2",6, "二级分类",       "文本，最长100字，可为空"),
        (8,  "sub_category_3",7, "三级分类",       "文本，最长100字，可为空"),
        (9,  "org_type",      8, "单位类型",       "文本，最长100字，可为空"),
        (10, "status",        9, "环节",           "文本，最长200字，可为空"),
        (11, "system_reply", 10, "系统重复",       "文本，不限长度，可为空"),
    ]
    conn.executemany(
        "INSERT INTO column_mapping (col_order, db_column, excel_index, description, constraint_desc) "
        "VALUES (?, ?, ?, ?, ?)",
        mappings,
    )


# ═══════════════════════════════════════════════════
# db_connections 操作（替代 config.ini）
# ═══════════════════════════════════════════════════

def load_connection() -> dict:
    """读取上次使用的数据库连接配置。

    返回:
        {"server": "", "database": "", "schema": "dbo", "username": "", "password": ""}
    """
    conn = _get_conn()
    try:
        conn.execute(CREATE_DB_CONNECTIONS)  # 确保表存在
        row = conn.execute(
            "SELECT server, database, schema_name, username, password "
            "FROM db_connections WHERE is_last_used = 1 LIMIT 1"
        ).fetchone()

        if row is None:
            return {
                "server": "", "database": "", "schema": "dbo",
                "username": "", "password": "",
            }

        return {
            "server": row[0],
            "database": row[1],
            "schema": row[2],
            "username": row[3],
            "password": row[4],
        }
    finally:
        conn.close()


def save_connection(config: dict) -> None:
    """保存数据库连接配置（设为上次使用，用于下次登录自动填充）。

    先检查是否已有相同 server+database 的记录，有则更新，无则插入。
    """
    conn = _get_conn()
    try:
        conn.execute(CREATE_DB_CONNECTIONS)
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        server = config.get("server", "")
        database = config.get("database", "")
        schema_name = config.get("schema", "dbo")
        username = config.get("username", "")
        password = config.get("password", "")

        # 清除所有 is_last_used
        conn.execute("UPDATE db_connections SET is_last_used = 0")

        # 查找是否已有相同 server+database 的记录
        row = conn.execute(
            "SELECT id FROM db_connections WHERE server = ? AND database = ?",
            (server, database),
        ).fetchone()

        if row:
            conn.execute(
                "UPDATE db_connections SET schema_name = ?, username = ?, password = ?, "
                "is_last_used = 1, updated_at = ? WHERE id = ?",
                (schema_name, username, password, now, row[0]),
            )
        else:
            conn.execute(
                "INSERT INTO db_connections "
                "(server, database, schema_name, username, password, is_last_used, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
                (server, database, schema_name, username, password, now, now),
            )

        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


# ═══════════════════════════════════════════════════
# sheet_names 操作（替代 sheet_names.txt）
# ═══════════════════════════════════════════════════

def get_sheet_names() -> list[dict]:
    """返回所有 sheet 名称映射记录。

    返回:
        [{"id": 1, "sheet_order": 1, "sheet_name": "房屋建筑",
          "table_name": "enterprise_info_001",
          "last_import_time": "2026-07-20 14:30:00"}, ...]
        last_import_time 未记录时为空字符串。"""
    conn = _get_conn()
    try:
        conn.execute(CREATE_SHEET_NAMES)
        rows = conn.execute(
            "SELECT id, sheet_order, sheet_name, table_name, last_import_time "
            "FROM sheet_names ORDER BY sheet_order"
        ).fetchall()
        return [
            {
                "id": r[0],
                "sheet_order": r[1],
                "sheet_name": r[2],
                "table_name": r[3],
                "last_import_time": r[4] or "",
            }
            for r in rows
        ]
    finally:
        conn.close()


def add_sheet_mapping(sheet_order: int, sheet_name: str, table_name: str) -> int:
    """新增一条 sheet 映射记录，返回新记录的 id。"""
    conn = _get_conn()
    try:
        conn.execute(CREATE_SHEET_NAMES)
        cur = conn.execute(
            "INSERT INTO sheet_names (sheet_order, sheet_name, table_name) "
            "VALUES (?, ?, ?)",
            (sheet_order, sheet_name, table_name),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_sheet_mapping(record_id: int, sheet_order: int, sheet_name: str, table_name: str) -> None:
    """更新指定 id 的 sheet 映射记录（不修改 last_import_time）。"""
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE sheet_names SET sheet_order = ?, sheet_name = ?, table_name = ? "
            "WHERE id = ?",
            (sheet_order, sheet_name, table_name, record_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_sheet_mapping(record_id: int) -> None:
    """删除指定 id 的 sheet 映射记录。"""
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM sheet_names WHERE id = ?", (record_id,))
        conn.commit()
    finally:
        conn.close()


def update_last_import_time(table_name: str, import_time: str) -> None:
    """更新指定表的最后导入时间。

    参数:
        table_name: 数据库表名（如 enterprise_info_001）
        import_time: 时间字符串（如 "2026-07-20 14:30:00"）
    """
    conn = _get_conn()
    try:
        conn.execute(
            "UPDATE sheet_names SET last_import_time = ? WHERE table_name = ?",
            (import_time, table_name),
        )
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════
# column_mapping 操作（Excel 列 → 数据库字段）
# ═══════════════════════════════════════════════════

def get_column_mapping() -> list[tuple[str, int]]:
    """返回 Excel 列 → 数据库字段名的映射列表。

    返回:
        [("collected_at", 0), ("team", 1), ...]
    """
    conn = _get_conn()
    try:
        conn.execute(CREATE_COLUMN_MAPPING)
        rows = conn.execute(
            "SELECT db_column, excel_index FROM column_mapping ORDER BY col_order"
        ).fetchall()
        return [(r[0], r[1]) for r in rows]
    finally:
        conn.close()


def get_column_mapping_with_desc() -> list[dict]:
    """返回带描述的完整列映射记录（用于 UI 展示）。

    返回:
        [{"col_order": 1, "db_column": "collected_at",
          "excel_index": 0, "excel_col": "A", "description": "日期",
          "constraint_desc": "date 类型，可为空"}, ...]
    """
    conn = _get_conn()
    try:
        conn.execute(CREATE_COLUMN_MAPPING)
        rows = conn.execute(
            "SELECT col_order, db_column, excel_index, description, constraint_desc "
            "FROM column_mapping ORDER BY col_order"
        ).fetchall()
        return [
            {
                "col_order": r[0],
                "db_column": r[1],
                "excel_index": r[2],
                "excel_col": _index_to_col_letter(r[2]),
                "description": r[3],
                "constraint_desc": r[4] or "",
            }
            for r in rows
        ]
    finally:
        conn.close()


def _index_to_col_letter(idx: int) -> str:
    """将 0-based 列索引转为 Excel 列字母（0→A, 1→B, ..., 25→Z, 26→AA）。"""
    result = ""
    idx += 1  # 转为 1-based
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result = chr(rem + 65) + result
    return result
