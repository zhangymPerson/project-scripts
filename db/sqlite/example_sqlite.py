#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
SQLite 数据库操作示例脚本

用法:
    uv run db/sqlite/example_sqlite.py --help

说明:
    - 使用 PEP 723 标准的内联依赖声明
    - 使用 typer 处理命令行参数
    - 使用 loguru 进行日志记录
    - 使用 sqlite3 标准库连接 SQLite 数据库

环境变量 (设置数据库连接):
    SQLITE_DB_PATH  数据库文件路径 (默认: ./data.db)

快速设置示例:
    export SQLITE_DB_PATH=/path/to/database.db

    # 或者一行设置
    SQLITE_DB_PATH=./test.db uv run db/sqlite/example_sqlite.py connect
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "loguru>=0.7",
#     "typer>=0.9",
# ]
# ///

import os
import sys
from pathlib import Path

import typer
from loguru import logger

# =============================================================================
# 配置
# =============================================================================

# 数据库配置
DB_PATH = os.getenv("SQLITE_DB_PATH", "db/sqlite/data.db")

# 日志级别：通过 DEBUG 环境变量控制
DEBUG_MODE = os.getenv("DEBUG", "").lower() in ("true", "1", "t")
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"

# 日志输出目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# =============================================================================
# 日志配置
# =============================================================================

# 移除默认的 handler
logger.remove()

# 输出到控制台（带颜色）
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# 输出到文件（按日期轮转）
logger.add(
    LOG_DIR / "{time:YYYY-MM-DD}.log",
    level=LOG_LEVEL,
    rotation="00:00",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# =============================================================================
# 数据库工具
# =============================================================================

def get_db_connection():
    """获取数据库连接"""
    import sqlite3

    # 确保数据库目录存在
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 允许用列名访问
    logger.debug(f"数据库连接成功: {DB_PATH}")
    return conn


def execute_query(query: str, fetch: bool = True):
    """执行 SQL 查询"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.debug(f"执行 SQL: {query}")
        cursor.execute(query)

        if fetch:
            results = cursor.fetchall()
            logger.info(f"查询返回 {len(results)} 条记录")
            # 转换为字典列表
            return [dict(row) for row in results]
        else:
            conn.commit()
            logger.info(f"影响行数: {cursor.rowcount}")
            return cursor.rowcount

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"SQL 执行失败: {e}")
        raise
    finally:
        if conn:
            conn.close()


# =============================================================================
# 命令行接口
# =============================================================================

app = typer.Typer(help="""SQLite 数据库操作示例脚本

环境变量 (设置数据库连接):
    SQLITE_DB_PATH  数据库文件路径 (默认: db/sqlite/data.db)

快速设置示例:
    export SQLITE_DB_PATH=/path/to/database.db

    # 或者一行设置
    SQLITE_DB_PATH=./test.db uv run db/sqlite/example_sqlite.py connect
""")


@app.command()
def connect():
    """
    测试数据库连接

    示例:
        uv run db/sqlite/example_sqlite.py connect
    """
    logger.info("测试数据库连接...")
    try:
        conn = get_db_connection()
        conn.close()
        logger.info("✅ 数据库连接成功!")
        print(f"✅ 成功连接到 {DB_PATH} 数据库")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        print(f"❌ 连接失败: {e}")
        raise typer.Exit(code=1)


@app.command()
def tables():
    """
    查看数据库中的所有表

    示例:
        uv run db/sqlite/example_sqlite.py tables
    """
    logger.info("查询数据库中的表...")
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    results = execute_query(query)

    if results:
        tables = [row["name"] for row in results]

        print(f"📋 数据库 {DB_PATH} 中的表:")
        for table in tables:
            print(f"  - {table}")
        logger.info(f"共找到 {len(tables)} 个表")
    else:
        print("📋 数据库中没有表")
        logger.info("数据库中没有表")


@app.command()
def query(
    sql: str = typer.Option(..., "--sql", "-s", help="要执行的 SQL 查询"),
):
    """
    执行自定义 SQL 查询

    示例:
        uv run db/sqlite/example_sqlite.py query --sql "SELECT * FROM users LIMIT 5"
        uv run db/sqlite/example_sqlite.py query -s "SELECT COUNT(*) as count FROM users"
    """
    logger.debug(f"执行自定义 SQL: {sql}")
    print(f"🔍 执行 SQL: {sql}")

    results = execute_query(sql)

    if results:
        print(f"\n📊 查询结果 ({len(results)} 条):")
        for i, row in enumerate(results, 1):
            print(f"  [{i}] {row}")
    else:
        print("📊 查询结果为空")

    logger.info("SQL 查询执行完成")


@app.command()
def users(
    limit: int = typer.Option(10, "--limit", "-l", help="返回记录数", min=1, max=100),
):
    """
    查询用户表数据（假设存在 users 表）

    示例:
        uv run db/sqlite/example_sqlite.py users
        uv run db/sqlite/example_sqlite.py users --limit 5
    """
    logger.info(f"查询用户数据，限制 {limit} 条...")
    query = f"SELECT * FROM users LIMIT {limit}"

    results = execute_query(query)

    if results:
        print(f"👥 用户数据 ({len(results)} 条):")
        for i, row in enumerate(results, 1):
            print(f"  [{i}] {row}")
    else:
        print("👥 用户表为空或不存在")

    logger.info("用户查询完成")


@app.command()
def create_sample():
    """
    创建一个示例 users 表并插入测试数据

    示例:
        uv run db/sqlite/example_sqlite.py create_sample
    """
    logger.info("创建示例 users 表...")

    # 创建表
    create_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    execute_query(create_sql, fetch=False)

    # 插入测试数据
    insert_sql = """
    INSERT OR IGNORE INTO users (name, email, age) VALUES
        ('Alice', 'alice@example.com', 25),
        ('Bob', 'bob@example.com', 30),
        ('Charlie', 'charlie@example.com', 35)
    """
    execute_query(insert_sql, fetch=False)

    logger.info("✅ 示例表创建成功!")
    print("✅ 已创建 users 表并插入测试数据")


@app.command()
def info():
    """
    显示脚本和数据库连接信息
    """
    logger.info("显示脚本信息")
    print("📖 脚本信息:")
    print(f"  脚本名称：{Path(__file__).name}")
    print(f"  脚本路径：{Path(__file__).absolute()}")
    print(f"  日志目录：{LOG_DIR}")
    print(f"  调试模式：{'开启' if DEBUG_MODE else '关闭'}")
    print(f"  Python 版本：{sys.version}")

    print("\n📦 数据库配置:")
    print(f"  数据库路径：{DB_PATH}")

    # 显示文件大小
    db_file = Path(DB_PATH)
    if db_file.exists():
        size = db_file.stat().st_size
        print(f"  文件大小：{size} bytes")
    else:
        print("  文件大小：文件不存在")


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
