#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
MySQL 数据库表行数统计脚本

用法:
    uv run db/mysql/table-row-count.py                          # 统计所有表
    uv run db/mysql/table-row-count.py --include "^user"        # 仅统计 user 开头的表
    uv run db/mysql/table-row-count.py --exclude "^tmp_"        # 排除 tmp_ 开头的表
    uv run db/mysql/table-row-count.py --include "log" --exact  # 精确匹配包含 log 的表名
    uv run db/mysql/table-row-count.py --sort count             # 按行数排序
    uv run db/mysql/table-row-count.py --sort count --desc      # 按行数降序排序

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
from enum import Enum
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
    conn: MySQLConnection | None = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.debug(
            f"数据库连接成功: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        yield conn
    except mysql.connector.Error as e:
        logger.error(f"数据库连接失败: {e}")
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()
            logger.debug("数据库连接已关闭")


# =============================================================================
# 核心函数
# =============================================================================


def get_all_table_names() -> list[str]:
    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = sorted(row[0] for row in cursor.fetchall())
        logger.debug(f"获取到 {len(tables)} 个表")
        return tables


def filter_tables(tables: list[str], pattern: str | None, exclude: bool) -> list[str]:
    if not pattern:
        return tables

    try:
        regex = re.compile(pattern)
    except re.error as e:
        logger.error(f"无效的正则表达式: {pattern!r} -> {e}")
        raise ValueError(f"无效的正则表达式: {pattern!r}") from e

    logger.debug(f"正则过滤: pattern={pattern!r}, exclude={exclude}")

    if exclude:
        result = [t for t in tables if not regex.search(t)]
        logger.debug(f"排除模式: {len(tables)} -> {len(result)} 个表")
    else:
        result = [t for t in tables if regex.search(t)]
        logger.debug(f"包含模式: {len(tables)} -> {len(result)} 个表")

    return result


def count_table_rows(table_name: str) -> int:
    safe_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")
    if not safe_pattern.match(table_name):
        raise ValueError(f"非法表名: {table_name!r}")

    with _get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        row = cursor.fetchone()
        count = row[0] if row else 0
        logger.debug(f"表 {table_name}: {count} 行")
        return count


class SortField(str, Enum):
    name = "name"
    count = "count"


def get_table_row_counts(
    tables: list[str],
    sort_field: SortField = SortField.name,
    descending: bool = False,
) -> list[tuple[str, int]]:
    results = []
    total = len(tables)

    for i, table in enumerate(tables, 1):
        try:
            count = count_table_rows(table)
            results.append((table, count))
            if i % 10 == 0 or i == total:
                logger.debug(f"进度: {i}/{total}")
        except (mysql.connector.Error, ValueError) as e:
            logger.warning(f"跳过表 {table}: {e}")
            results.append((table, -1))

    if sort_field == SortField.count:
        results.sort(key=lambda x: x[1], reverse=descending)
    elif sort_field == SortField.name:
        results.sort(key=lambda x: x[0], reverse=descending)

    return results


def print_results(results: list[tuple[str, int]], database: str):
    if not results:
        logger.info("没有匹配的表")
        return

    name_width = max(len(t) for t, _ in results)
    name_width = max(name_width, len("表名"))
    count_width = max(len(str(c)) for _, c in results)
    count_width = max(count_width, len("行数"))

    header = f"{'表名':<{name_width}}  {'行数':>{count_width}}"
    sep = f"{'-' * name_width}  {'-' * count_width}"

    print(f"\n数据库: {database}\n")
    print(header)
    print(sep)

    total_rows = 0
    error_count = 0
    for table, count in results:
        if count == -1:
            count_str = "ERROR"
            error_count += 1
        else:
            count_str = f"{count:,}"
            total_rows += count
        print(f"{table:<{name_width}}  {count_str:>{count_width}}")

    print(sep)
    print(f"共 {len(results)} 个表, 总计 {total_rows:,} 行", end="")
    if error_count:
        print(f", {error_count} 个表查询失败", end="")
    print()


# =============================================================================
# 命令行接口
# =============================================================================

app = typer.Typer(
    help="""MySQL 数据库表行数统计脚本

环境变量 (设置数据库连接):
    MYSQL_HOST      数据库主机地址 (默认: localhost)
    MYSQL_PORT      数据库端口 (默认: 3306)
    MYSQL_USER      数据库用户名 (默认: root)
    MYSQL_PASSWORD  数据库密码 (默认: password)
    MYSQL_DATABASE  数据库名称 (默认: test_db)
"""
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    include: str | None = typer.Option(
        None, "--include", "-i", help="正则匹配表名 (包含模式, 仅统计匹配的表)"
    ),
    exclude: str | None = typer.Option(
        None, "--exclude", "-e", help="正则匹配表名 (排除模式, 排除匹配的表)"
    ),
    sort: SortField = typer.Option(
        SortField.name, "--sort", "-s", help="排序字段: name 或 count"
    ),
    desc: bool = typer.Option(False, "--desc", "-d", help="降序排列"),
):
    """统计数据库中各表的行数，支持正则过滤和排序

    示例:
        uv run db/mysql/table-row-count.py                          # 统计所有表
        uv run db/mysql/table-row-count.py --include "^user"        # 仅统计 user 开头的表
        uv run db/mysql/table-row-count.py --exclude "^tmp_"        # 排除 tmp_ 开头的表
        uv run db/mysql/table-row-count.py --sort count --desc      # 按行数降序
    """
    if include and exclude:
        logger.error("--include 和 --exclude 不能同时使用")
        raise typer.Exit(code=1)

    logger.debug(
        f"参数: include={include!r}, exclude={exclude!r}, sort={sort}, desc={desc}"
    )

    try:
        all_tables = get_all_table_names()

        pattern = include or exclude
        is_exclude = exclude is not None
        filtered = filter_tables(all_tables, pattern, is_exclude)

        if not filtered:
            logger.info(f"没有匹配的表 (共 {len(all_tables)} 个表)")
            raise typer.Exit(code=0)

        results = get_table_row_counts(filtered, sort, desc)
        print_results(results, DB_CONFIG["database"])

    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(code=1)
    except mysql.connector.Error as e:
        logger.error(f"数据库错误: {e}")
        raise typer.Exit(code=1)


@app.command("task")
def task():
    """默认任务"""
    print("Hello, World!")


@app.command("info")
def info():
    """显示脚本信息和当前数据库连接配置"""
    print("MySQL 表行数统计脚本")
    print(f"  主机: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"  用户: {DB_CONFIG['user']}")
    print(f"  数据库: {DB_CONFIG['database']}")
    print(f"  调试模式: {'开启' if DEBUG_MODE else '关闭'}")


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
