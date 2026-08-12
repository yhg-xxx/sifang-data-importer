"""配置管理 - 从本地 SQLite 数据库读写连接参数（替代 config.ini）"""

from app import local_db


def load_config() -> dict:
    """读取上次使用的数据库连接配置。

    返回:
        {"server": "", "database": "", "schema": "dbo", "username": "", "password": ""}
    """
    return local_db.load_connection()


def save_config(config: dict) -> None:
    """保存连接参数到本地 SQLite 数据库。"""
    local_db.save_connection(config)
