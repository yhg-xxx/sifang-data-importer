"""数据库 / 导入错误「人话化」工具

把晦涩的 ODBC / SQL Server 原始报错翻译成用户能看懂的中文。
对于我们已经在 importer / validator 中拼好的中文错误，本函数原样返回，
只拦截 ODBC 错误码与常见模式。
"""

# (匹配关键字(小写), 中文说明)
_TRANSLATIONS = [
    ("22018", "数据格式错误：某个「日期/数字」字段里包含了非法字符（例如本该填日期的列被填成了人名或文字）。请先运行「验证数据」定位具体行。"),
    ("invalid character value for cast specification", "数据类型转换失败：字段值与目标列类型不匹配（常见于日期/数字列被填了文字）。请先运行「验证数据」定位具体行。"),
    ("string or binary data would be truncated", "数据过长：某个字段的值超出了数据库列的长度限制。请检查超长文本字段。"),
    ("将截断", "数据过长：某个字段的值超出了数据库列的长度限制。请检查超长文本字段。"),
    ("cannot insert the value null into column", "必填字段为空：有列被写入了 NULL，但该列不允许为空。请先运行「验证数据」检查空值。"),
    ("hy000", "数据库驱动错误：请确认 ODBC Driver 17 已安装且连接参数正确。"),
    ("hy104", "数据库参数错误，请检查连接配置。"),
    ("08s01", "网络连接中断，请确认数据库服务器可达后重试。"),
    ("hy010", "连接状态异常（函数序列错误），请关闭后重新连接再试。"),
]


def humanize_db_error(message: str) -> str:
    """将原始数据库/ODBC 报错翻译为可读中文。

    已格式化的中文错误（importer/validator 自己拼出的）原样返回；
    仅对 ODBC 错误码与常见模式做翻译。未匹配时亦原样返回。
    """
    if not message:
        return message
    lowered = message.lower()
    for key, text in _TRANSLATIONS:
        if key in lowered:
            return text
    return message
