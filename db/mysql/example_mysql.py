#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
MySQL 数据库操作示例脚本

用法:
    uv run db/mysql/example_mysql.py --help

说明:
    - 使用 PEP 723 标准的内联依赖声明
    - 使用 typer 处理命令行参数
    - 使用 loguru 进行日志记录
    - 使用 mysql-connector-python 连接 MySQL 数据库

环境变量 (设置数据库连接):
    MYSQL_HOST      数据库主机地址 (默认: localhost)
    MYSQL_PORT      数据库端口 (默认: 3306)
    MYSQL_USER      数据库用户名 (默认: root)
    MYSQL_PASSWORD  数据库密码 (默认: password)
    MYSQL_DATABASE  数据库名称 (默认: test_db)

快速设置示例:
    export MYSQL_HOST=192.168.1.100
    export MYSQL_PORT=3306
    export MYSQL_USER=myuser
    export MYSQL_PASSWORD=mypassword
    export MYSQL_DATABASE=mydb

    # 或者一行设置
    MYSQL_HOST=localhost MYSQL_PASSWORD=root uv run db/mysql/example_mysql.py connect
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
import sys
from pathlib import Path

import typer
from loguru import logger

# =============================================================================
# 配置
# =============================================================================

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
    "database": os.getenv("MYSQL_DATABASE", "test_db"),
}

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
    try:
        import mysql.connector
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.debug(f"数据库连接成功: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


def execute_query(query: str, fetch: bool = True):
    """执行 SQL 查询"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        logger.debug(f"执行 SQL: {query}")
        cursor.execute(query)

        if fetch:
            results = cursor.fetchall()
            logger.info(f"查询返回 {len(results)} 条记录")
            return results
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

app = typer.Typer(help="""MySQL 数据库操作示例脚本

环境变量 (设置数据库连接):
    MYSQL_HOST      数据库主机地址 (默认: localhost)
    MYSQL_PORT      数据库端口 (默认: 3306)
    MYSQL_USER      数据库用户名 (默认: root)
    MYSQL_PASSWORD  数据库密码 (默认: password)
    MYSQL_DATABASE  数据库名称 (默认: test_db)

快速设置示例:
    export MYSQL_HOST=192.168.1.100
    export MYSQL_PORT=3306
    export MYSQL_USER=myuser
    export MYSQL_PASSWORD=mypassword
    export MYSQL_DATABASE=mydb

    # 或者一行设置
    MYSQL_HOST=localhost MYSQL_PASSWORD=root uv run db/mysql/example_mysql.py connect      
                  """)


@app.command()
def connect():
    """
    测试数据库连接

    示例:
        uv run db/mysql/example_mysql.py connect
    """
    logger.info("测试数据库连接...")
    try:
        conn = get_db_connection()
        conn.close()
        logger.info("✅ 数据库连接成功!")
        print(f"✅ 成功连接到 {DB_CONFIG['database']} 数据库")
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        print(f"❌ 连接失败: {e}")
        raise typer.Exit(code=1)


@app.command()
def tables():
    """
    查看数据库中的所有表

    示例:
        uv run db/mysql/example_mysql.py tables
    """
    logger.info("查询数据库中的表...")
    query = "SHOW TABLES"
    results = execute_query(query)

    if results:
        # 提取表名
        table_key = f"Tables_in_{DB_CONFIG['database']}"
        tables = [row[table_key] for row in results]

        print(f"📋 数据库 {DB_CONFIG['database']} 中的表:")
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
        uv run db/mysql/example_mysql.py query --sql "SELECT * FROM users LIMIT 5"
        uv run db/mysql/example_mysql.py query -s "SELECT COUNT(*) as count FROM users"
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
        uv run db/mysql/example_mysql.py users
        uv run db/mysql/example_mysql.py users --limit 5
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
    print(f"  主机：{DB_CONFIG['host']}")
    print(f"  端口：{DB_CONFIG['port']}")
    print(f"  用户：{DB_CONFIG['user']}")
    print(f"  数据库：{DB_CONFIG['database']}")
    print(f"  密码：{'*' * len(DB_CONFIG['password'])}")


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
