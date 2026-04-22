#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
MySQL 数据库信息查询脚本

用法:
    uv run db/mysql/mysql-info.py --help
    uv run db/mysql/mysql-info.py tables
    uv run db/mysql/mysql-info.py create-table --table users

环境变量 (设置数据库连接):
    MYSQL_HOST      数据库主机地址 (默认: localhost)
    MYSQL_PORT      数据库端口 (默认: 3306)
    MYSQL_USER      数据库用户名 (默认: root)
    MYSQL_PASSWORD  数据库密码 (默认: password)
    MYSQL_DATABASE  数据库名称 (默认: test_db)
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "loguru>=0.7",
#     "typer>=0.9",
#     "mysql-connector-python>=8.0",
# ]
# ///

import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
import typer
from loguru import logger
from mysql.connector import MySQLConnection

# =============================================================================
# 配置
# =============================================================================

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
    "database": os.getenv("MYSQL_DATABASE", "test_db"),
}

DEBUG_MODE = os.getenv("DEBUG", "").lower() in ("true", "1", "t")
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# =============================================================================
# 日志配置
# =============================================================================

logger.remove()
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)
logger.add(
    LOG_DIR / "{time:YYYY-MM-DD}.log",
    level=LOG_LEVEL,
    rotation="00:00",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# =============================================================================
# 数据库连接管理
# =============================================================================

@contextmanager
def _get_db_connection():
    """获取数据库连接的上下文管理器，确保连接安全释放"""
    conn: MySQLConnection | None = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.debug(f"数据库连接成功: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        yield conn
    except mysql.connector.Error as e:
        logger.error(f"数据库连接失败: {e}")
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
            logger.debug("数据库连接已关闭")

# =============================================================================
# 白名单校验
# =============================================================================

_TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


def _validate_table_name(name: str) -> str:
    """校验表名合法性，防止 SQL 注入"""
    if not _TABLE_NAME_PATTERN.match(name):
        raise ValueError(f"非法表名: {name!r}，仅允许字母、数字及下划线，且以字母或下划线开头，长度 1-64")
    return name

# =============================================================================
# 核心函数
# =============================================================================

_SELECT_PATTERN = re.compile(r"^\s*SELECT\b", re.IGNORECASE)


_QUERY_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|REVOKE|LOAD|CALL|EXECUTE|HANDLER|LOCK|UNLOCK)\b",
    re.IGNORECASE,
)


def _validate_select_query(sql: str) -> str:
    """校验 SQL 必须是 SELECT 查询语句"""
    if not _SELECT_PATTERN.match(sql):
        raise ValueError("仅允许 SELECT 查询语句，不支持增删改等写操作")
    if _QUERY_FORBIDDEN.search(sql):
        raise ValueError("SQL 中包含不允许的关键字，仅允许 SELECT 查询")
    return sql.strip()


def get_table_names() -> list[str]:
    """获取当前数据库中所有表的表名列表

    Returns:
        按表名排序的表名列表
    """
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        rows = cursor.fetchall()
        table_names = [row[0] for row in rows]
        table_names.sort()
        logger.info(f"共获取 {len(table_names)} 个表")
        return table_names


def get_create_table_statement(table_name: str) -> str:
    """获取单个表的建表语句

    Args:
        table_name: 表名，会进行合法性校验

    Returns:
        SHOW CREATE TABLE 的完整输出

    Raises:
        ValueError: 表名不合法
        mysql.connector.Error: 表不存在或数据库错误
    """
    safe_name = _validate_table_name(table_name)
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SHOW CREATE TABLE `{safe_name}`")
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"表 {safe_name!r} 不存在")
        create_stmt = row[1]
        logger.info(f"获取建表语句成功: {safe_name}")
        return create_stmt

def execute_select_query(sql: str) -> list[tuple]:
    """执行 SELECT 查询语句并返回结果

    Args:
        sql: SELECT 查询语句，非查询语句会抛出 ValueError

    Returns:
        列名列表 + 数据行列表
    """
    safe_sql = _validate_select_query(sql)
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(safe_sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        logger.info(f"查询执行成功，返回 {len(rows)} 行")
        return columns, rows


# =============================================================================
# 命令行接口
# =============================================================================

app = typer.Typer(help="""MySQL 数据库信息查询脚本

环境变量 (设置数据库连接):
    MYSQL_HOST      数据库主机地址 (默认: localhost)
    MYSQL_PORT      数据库端口 (默认: 3306)
    MYSQL_USER      数据库用户名 (默认: root)
    MYSQL_PASSWORD  数据库密码 (默认: password)
    MYSQL_DATABASE  数据库名称 (默认: test_db)
""")


@app.command()
def tables():
    """获取数据库中所有表的表名列表

    示例:
        uv run db/mysql/mysql-info.py tables
    """
    result = get_table_names()
    if result:
        logger.debug(f"数据库 {DB_CONFIG['database']} 中的表 ({len(result)} 个):")
        for name in result:
            print(f"  - {name}")
    else:
        logger.debug(f"数据库 {DB_CONFIG['database']} 中没有表")


@app.command("create-table")
def create_table(
    table: str = typer.Option(..., "--table", "-t", help="表名"),
):
    """获取单个表的建表语句

    示例:
        uv run db/mysql/mysql-info.py create-table --table users
        uv run db/mysql/mysql-info.py create-table -t users
    """
    try:
        result = get_create_table_statement(table)
        print(result)
    except ValueError as e:
        logger.error(str(e))
        logger.debug(f"错误: {e}")
        raise typer.Exit(code=1)
    except mysql.connector.Error as e:
        logger.error(f"数据库错误: {e}")
        logger.debug(f"数据库错误: {e}")
        raise typer.Exit(code=1)


@app.command("query")
def query(
    sql: str = typer.Option(..., "--sql", "-s", help="SELECT 查询语句"),
):
    """执行 SELECT 查询语句并打印结果

    示例:
        uv run db/mysql/mysql-info.py query --sql "SELECT * FROM users LIMIT 5"
        uv run db/mysql/mysql-info.py query -s "SELECT COUNT(*) FROM users"
    """
    try:
        columns, rows = execute_select_query(sql)
        if not rows:
            logger.debug("查询结果为空")
            return
        col_widths = [len(str(c)) for c in columns]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        header = " | ".join(str(c).ljust(col_widths[i]) for i, c in enumerate(columns))
        sep = "-+-".join("-" * w for w in col_widths)
        print(header)
        print(sep)
        for row in rows:
            line = " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
            print(line)
        print(f"\n{len(rows)} 行")
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(code=1)
    except mysql.connector.Error as e:
        logger.error(f"数据库错误: {e}")
        logger.debug(f"数据库错误: {e}")
        raise typer.Exit(code=1)


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
