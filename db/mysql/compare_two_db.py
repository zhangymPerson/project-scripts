#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer>=0.9",
#     "loguru>=0.7",
#     "rich>=13.0",
#     "pymysql>=1.1",
#     "pyyaml>=6.0",
# ]
# ///
"""
@file : compare_two_db.py
@desc : 比较两个 MySQL 数据库的表结构和数据差异，并自动生成同步 SQL 语句
        运行方式: uv run compare_two_db.py compare --config compare.yaml
@date : 2025-05-30
@auth : danao
@version : 2.1
"""

import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymysql
import typer
import yaml
from loguru import logger
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

# ---------------------------------------------------------------------------
# 应用配置
# ---------------------------------------------------------------------------

DEBUG_MODE = os.getenv("DEBUG", "").lower() in ("true", "1", "t")
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"

# 移除默认 loguru handler，重新配置
logger.remove()
logger.add(
    sink=sys.stderr,
    level=LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level>"
        " | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        " - <level>{message}</level>"
    ),
    colorize=True,
)
logger.add(
    sink="logs/compare_two_db_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="1 day",
    retention=7,
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

# Typer 应用
app = typer.Typer(
    name="compare-two-db",
    help="比较两个 MySQL 数据库的表结构和数据差异",
    rich_markup_mode="rich",
    add_completion=False,
)

console = Console()

# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class DBConfig:
    """数据库连接配置"""

    host: str = "localhost"
    port: int = 3306
    database: str = ""
    user: str = "root"
    password: str = "root"
    charset: str = "utf8mb4"

    def to_conn_params(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "db": self.database,
            "user": self.user,
            "passwd": self.password,
            "charset": self.charset,
        }


@dataclass
class DiffResult:
    """数据库差异比较结果"""

    only_in_main: list[str] = field(default_factory=list)
    only_in_slave: list[str] = field(default_factory=list)
    common_tables: set[str] = field(default_factory=set)
    diff_tables: list[tuple[str, list[str]]] = field(default_factory=list)


@dataclass
class CompareConfig:
    """比较配置，包含主库和从库的连接信息"""

    main: DBConfig
    slave: DBConfig

    @classmethod
    def from_yaml(cls, path: str) -> "CompareConfig":
        """从 YAML 文件加载比较配置"""
        config_path = Path(path).expanduser()
        if not config_path.exists():
            rprint(f"[red]❌ 配置文件不存在: {config_path}[/red]")
            raise typer.Exit(code=1)

        logger.debug(f"加载配置文件: {config_path.resolve()}")
        with config_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw or "main" not in raw or "slave" not in raw:
            rprint("[red]❌ 配置格式错误：必须包含 main 和 slave 两个节点[/red]")
            raise typer.Exit(code=1)

        def _build_db_config(prefix: str, data: dict) -> DBConfig:
            return DBConfig(
                host=data.get("host", "localhost"),
                port=int(data.get("port", 3306)),
                database=data.get("database", ""),
                user=data.get("user", "root"),
                password=data.get("password", "root"),
                charset=data.get("charset", "utf8mb4"),
            )

        main_cfg = _build_db_config("main", raw["main"])
        slave_cfg = _build_db_config("slave", raw["slave"])

        logger.debug(
            f"配置加载完成: "
            f"main=[{main_cfg.host}:{main_cfg.port}/{main_cfg.database}], "
            f"slave=[{slave_cfg.host}:{slave_cfg.port}/{slave_cfg.database}]"
        )
        return cls(main=main_cfg, slave=slave_cfg)


# ---------------------------------------------------------------------------
# 数据库连接
# ---------------------------------------------------------------------------


class DB:
    """数据库连接封装，支持上下文管理器"""

    def __init__(self, config: DBConfig):
        self.config = config
        self.conn: pymysql.Connection | None = None
        self.cur: pymysql.cursors.DictCursor | None = None
        self._connect()

    def _connect(self) -> None:
        """建立数据库连接"""
        params = self.config.to_conn_params()
        logger.debug(
            f"连接数据库: {self.config.host}:{self.config.port}/{self.config.database}"
        )
        try:
            self.conn = pymysql.connect(
                **params, cursorclass=pymysql.cursors.DictCursor
            )
            self.cur = self.conn.cursor()
            logger.info(
                f"✅ 成功连接到 [{self.config.host}:{self.config.port}/{self.config.database}]"
            )
        except pymysql.err.OperationalError as e:
            rprint(f"[red]❌ 数据库连接失败：{e}[/red]")
            rprint(
                f"[yellow]   连接参数：host={self.config.host},"
                f" port={self.config.port}, db={self.config.database}[/yellow]"
            )
            raise typer.Exit(code=1) from e
        except pymysql.MySQLError as e:
            rprint(f"[red]❌ MySQL 错误：{e}[/red]")
            raise typer.Exit(code=1) from e

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                self.conn.commit()
            except Exception as e:
                logger.warning(f"提交事务失败: {e}")
            finally:
                self.cur and self.cur.close()
                self.conn.close()
                logger.debug("数据库连接已关闭")

    def close(self) -> None:
        """显式关闭连接"""
        if self.conn:
            try:
                self.cur and self.cur.close()
                self.conn.close()
                logger.debug("数据库连接已关闭")
            except Exception as e:
                logger.warning(f"关闭连接异常: {e}")


# ---------------------------------------------------------------------------
# 配置加载（已迁移至 CompareConfig.from_yaml）
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 核心比较逻辑
# ---------------------------------------------------------------------------


def _fetch_tables(cur: pymysql.cursors.DictCursor, database: str) -> list[str]:
    """获取数据库中所有表名"""
    cur.execute("SHOW TABLES")
    key = f"Tables_in_{database}"
    tables = [row[key] for row in cur.fetchall()]
    logger.debug(f"获取到 {len(tables)} 张表: {tables}")
    return tables


def _fetch_create_table_sql(cur: pymysql.cursors.DictCursor, table: str) -> str:
    """获取表的 CREATE TABLE 语句"""
    cur.execute(f"SHOW CREATE TABLE `{table}`")
    result = cur.fetchone()
    return result["Create Table"] if result else ""


def _fetch_columns_detail(cur: pymysql.cursors.DictCursor, table: str) -> list[dict]:
    """获取表的完整字段信息"""
    cur.execute(f"SHOW FULL COLUMNS FROM `{table}`")
    return cur.fetchall()


def compare_table_structure(
    main_cur: pymysql.cursors.DictCursor,
    slave_cur: pymysql.cursors.DictCursor,
    table: str,
    main_db_name: str,
    slave_db_name: str,
) -> tuple[bool, list[str]]:
    """
    比较单张表在两个数据库中的结构差异。

    返回: (结构是否一致, 差异 SQL 语句列表)
    """
    main_sql = _fetch_create_table_sql(main_cur, table)
    slave_sql = _fetch_create_table_sql(slave_cur, table)

    logger.debug(f"比较表结构: {table}")

    if main_sql == slave_sql:
        return True, []

    # 结构不一致，逐字段对比
    main_columns = _fetch_columns_detail(main_cur, table)
    slave_columns = _fetch_columns_detail(slave_cur, table)

    main_col_map = {col["Field"]: col for col in main_columns}
    slave_col_map = {col["Field"]: col for col in slave_columns}

    main_col_names = set(main_col_map.keys())
    slave_col_names = set(slave_col_map.keys())

    diff_sqls: list[str] = []

    # 主库有、从库没有 → 需要在从库 ADD
    for col_name in sorted(main_col_names - slave_col_names):
        col = main_col_map[col_name]
        sql = _generate_add_column_sql(table, col_name, col)
        diff_sqls.append(sql)
        logger.debug(f"生成 ADD COLUMN SQL: {sql}")

    # 从库有、主库没有 → 需要在主库 DROP
    for col_name in sorted(slave_col_names - main_col_names):
        sql = f"ALTER TABLE `{table}` DROP COLUMN `{col_name}`;"
        diff_sqls.append(sql)
        logger.debug(f"生成 DROP COLUMN SQL: {sql}")

    # 共有字段但类型/属性不一致
    for col_name in sorted(main_col_names & slave_col_names):
        main_col = main_col_map[col_name]
        slave_col = slave_col_map[col_name]
        modify_sql = _compare_and_generate_modify_sql(
            table, col_name, main_col, slave_col
        )
        if modify_sql:
            diff_sqls.append(modify_sql)

    return False, diff_sqls


def _generate_add_column_sql(table: str, column: str, col: dict) -> str:
    """生成 ADD COLUMN SQL"""
    sql = f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col['Type']}"

    if col.get("Null") == "NO":
        sql += " NOT NULL"
    else:
        sql += " NULL"

    default = col.get("Default")
    if default is not None:
        # 数字类型不需要引号，其他类型需要
        if _is_numeric_type(col["Type"]):
            sql += f" DEFAULT {default}"
        else:
            sql += f" DEFAULT '{default}'"

    extra = col.get("Extra", "")
    if extra:
        sql += f" {extra}"

    comment = col.get("Comment", "")
    if comment:
        sql += f" COMMENT '{comment}'"

    sql += ";"
    return sql


def _compare_and_generate_modify_sql(
    table: str,
    column: str,
    main_col: dict,
    slave_col: dict,
) -> str | None:
    """比较共有字段差异，生成 MODIFY COLUMN SQL"""
    diffs: list[str] = []

    # 比较类型
    if main_col["Type"] != slave_col["Type"]:
        diffs.append(f"Type: {slave_col['Type']} → {main_col['Type']}")

    # 比较 NULL 属性
    if main_col.get("Null") != slave_col.get("Null"):
        diffs.append(f"Null: {slave_col.get('Null')} → {main_col.get('Null')}")

    # 比较默认值
    if main_col.get("Default") != slave_col.get("Default"):
        diffs.append(f"Default: {slave_col.get('Default')} → {main_col.get('Default')}")

    # 比较注释
    if main_col.get("Comment") != slave_col.get("Comment"):
        diffs.append(f"Comment: {slave_col.get('Comment')} → {main_col.get('Comment')}")

    # 比较额外属性
    if main_col.get("Extra") != slave_col.get("Extra"):
        diffs.append(f"Extra: {slave_col.get('Extra')} → {main_col.get('Extra')}")

    if not diffs:
        return None

    # 以主库为准生成 MODIFY 语句
    return _generate_add_column_sql(table, column, main_col).replace(
        "ADD COLUMN", "MODIFY COLUMN"
    )


def _is_numeric_type(col_type: str) -> bool:
    """判断字段类型是否为数字类型"""
    numeric_patterns = [
        r"^(tiny|small|medium|big)?int",
        r"^(decimal|float|double|real)",
        r"^(numeric|number)",
        r"^(bit|boolean|bool)",
    ]
    return any(re.match(p, col_type, re.IGNORECASE) for p in numeric_patterns)


def compare_databases(main_config: DBConfig, slave_config: DBConfig) -> DiffResult:
    """
    比较两个数据库，返回差异结果。

    流程：
        1. 分别获取两个数据库的表列表
        2. 找出只在主/从库的表
        3. 对共有表逐一比较结构
    """
    main_db = DB(main_config)
    slave_db = DB(slave_config)

    try:
        main_tables = _fetch_tables(main_db.cur, main_config.database)
        slave_tables = _fetch_tables(slave_db.cur, slave_config.database)

        logger.debug(f"主库表数: {len(main_tables)}, 从库表数: {len(slave_tables)}")

        main_set = set(main_tables)
        slave_set = set(slave_tables)

        result = DiffResult(
            only_in_main=sorted(main_set - slave_set),
            only_in_slave=sorted(slave_set - main_set),
            common_tables=main_set & slave_set,
        )

        logger.info(
            f"共有表: {len(result.common_tables)} 张,"
            f" 仅在主库: {len(result.only_in_main)} 张,"
            f" 仅在从库: {len(result.only_in_slave)} 张"
        )

        # 比较共有表结构
        for table in sorted(result.common_tables):
            logger.debug(f"比较表结构: {table}")
            is_same, diff_sqls = compare_table_structure(
                main_db.cur,
                slave_db.cur,
                table,
                main_config.database,
                slave_config.database,
            )
            if not is_same:
                result.diff_tables.append((table, diff_sqls))

        return result
    finally:
        main_db.close()
        slave_db.close()


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------


def _render_tree(title: str, items: list[str], color: str = "white") -> None:
    """用 Tree 组件渲染列表"""
    if not items:
        rprint(f"[{color}]（无）[/{color}]")
        return
    tree = Tree(f"[bold {color}]{title} ({len(items)})[/bold {color}]")
    for item in items:
        tree.add(f"[{color}]{item}[/{color}]")
    console.print(tree)


def print_diff_result(
    result: DiffResult, main_db_name: str, slave_db_name: str
) -> None:
    """友好输出比较结果"""
    # 1. 概览面板
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("主库:", f"[cyan]{main_db_name}[/cyan]")
    summary.add_row("从库:", f"[cyan]{slave_db_name}[/cyan]")
    summary.add_row("共有表:", f"[green]{len(result.common_tables)}[/green] 张")
    summary.add_row("仅主库:", f"[yellow]{len(result.only_in_main)}[/yellow] 张")
    summary.add_row("仅从库:", f"[yellow]{len(result.only_in_slave)}[/yellow] 张")
    summary.add_row("结构差异:", f"[red]{len(result.diff_tables)}[/red] 张")
    console.print(Panel(summary, title="[bold]📊 比较概览[/bold]", border_style="blue"))
    print()

    # 2. 仅主库有的表
    _render_tree(f"📌 仅在 [{main_db_name}] 中的表", result.only_in_main, "yellow")
    print()

    # 3. 仅从库有的表
    _render_tree(f"📌 仅在 [{slave_db_name}] 中的表", result.only_in_slave, "yellow")
    print()

    # 4. 共有表中结构不一致的
    if not result.diff_tables:
        rprint("[green]✅ 所有共有表结构一致，无需同步。[/green]")
        return

    for table, sqls in result.diff_tables:
        panel_content = (
            "\n".join(sqls)
            if sqls
            else "[dim]无字段级差异（可能为索引/约束差异）[/dim]"
        )
        console.print(
            Panel(
                panel_content,
                title=f"[bold red]🔧 {table}[/bold red]",
                border_style="red",
                title_align="left",
            )
        )
        print()

    # 5. 汇总 SQL
    all_sqls = [sql for _, sqls in result.diff_tables for sql in sqls]
    if all_sqls:
        console.print(
            Panel(
                "\n".join(f"{i + 1:>3}. {sql}" for i, sql in enumerate(all_sqls)),
                title="[bold]📋 汇总同步 SQL（请审核后执行）[/bold]",
                border_style="green",
            )
        )


# ---------------------------------------------------------------------------
# CLI 命令
# ---------------------------------------------------------------------------


@app.command()
def compare(
    config: str = typer.Option(
        ...,
        "--config",
        "-c",
        help="YAML 配置文件的路径，包含 main/slave 数据库连接信息",
        envvar="COMPARE_DB_CONFIG",
    ),
) -> None:
    """
    比较两个 MySQL 数据库的表结构和字段差异。

    通过一个 YAML 配置文件指定主从库连接信息，自动对比：

    - 表级差异（仅在主/从库存在的表）
    - 字段级差异（类型、NULL、默认值、注释、额外属性）
    - 生成同步 SQL 语句
    """
    logger.debug(f"接收参数: config={config}")

    cfg = CompareConfig.from_yaml(config)
    main_config = cfg.main
    slave_config = cfg.slave

    if not main_config.database or not slave_config.database:
        rprint("[red]❌ 数据库名称不能为空，请检查 YAML 中的 database 配置[/red]")
        raise typer.Exit(code=1)

    logger.info(f"开始比较: {main_config.database} ↔ {slave_config.database}")

    with console.status("[bold green]正在比较数据库...", spinner="dots"):
        result = compare_databases(main_config, slave_config)

    print()
    print_diff_result(result, main_config.database, slave_config.database)


@app.command()
def info() -> None:
    """显示脚本信息"""
    console.print(
        Panel(
            "[bold]compare_two_db.py[/bold] v2.1\n\n"
            "比较两个 MySQL 数据库的表结构和字段差异，\n"
            "并自动生成 ALTER TABLE 同步 SQL 语句。\n\n"
            "[bold]用法:[/bold]\n"
            "  uv run compare_two_db.py compare config.yaml\n\n"
            "[bold]YAML 配置示例 (config.yaml):[/bold]\n"
            "  main:\n"
            "    host: localhost\n"
            "    port: 3306\n"
            "    database: db_main\n"
            "    user: root\n"
            "    password: '123456'\n"
            "    charset: utf8mb4\n\n"
            "  slave:\n"
            "    host: 192.168.1.100\n"
            "    port: 3306\n"
            "    database: db_slave\n"
            "    user: root\n"
            "    password: '123456'\n"
            "    charset: utf8mb4\n\n"
            "[bold]环境变量:[/bold]\n"
            "  DEBUG=true          启用调试日志\n"
            "  COMPARE_DB_CONFIG   配置文件路径（也可用命令行参数）",
            title="📖 脚本信息",
            border_style="cyan",
        )
    )


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------


def main() -> None:
    """脚本入口"""
    logger.debug(f"启动参数: {sys.argv}")
    app()


if __name__ == "__main__":
    main()
