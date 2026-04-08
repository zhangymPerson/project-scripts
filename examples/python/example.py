#!/usr/bin/env python3
"""
Python 脚本示例 - 展示 uv 内联依赖和命令行参数处理

用法:
    uv run examples/python/example.py --name Alice
    python3 examples/python/example.py --name Alice

说明:
    - 使用 PEP 723 标准的内联依赖声明
    - 使用 typer 处理命令行参数
    - 使用 loguru 进行日志记录
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "loguru>=0.7",
#     "typer>=0.9",
#     "rich>=13.0",
# ]
# ///

import os
import sys
from pathlib import Path
import time

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.rule import Rule

# =============================================================================
# 配置
# =============================================================================

# 日志级别：通过 DEBUG 环境变量控制
DEBUG_MODE = os.getenv("DEBUG", "").lower() in ("true", "1", "t")
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"

# 日志输出目录
LOG_DIR = Path(__file__).parent / "logs"
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
# 命令行接口
# =============================================================================

app = typer.Typer(help="Python 脚本示例 - 演示 uv 内联依赖和命令行处理")


@app.command()
def hello(name: str = typer.Option(..., "--name", "-n", help="要问候的名字")):
    """
    输出一句问候语

    示例:
        uv run example.py --name Alice
        uv run example.py -n Bob
    """
    logger.debug(f"接收到名字参数：{name}")
    logger.info(f"Hello, {name}!")
    print(f"👋 Hello, {name}!")


@app.command()
def info():
    """
    显示脚本信息
    """
    logger.info("显示脚本信息")
    print("📖 脚本信息:")
    print(f"  脚本名称：{Path(__file__).name}")
    print(f"  脚本路径：{Path(__file__).absolute()}")
    print(f"  日志目录：{LOG_DIR}")
    print(f"  调试模式：{'开启' if DEBUG_MODE else '关闭'}")
    print(f"  Python 版本：{sys.version}")


@app.command()
def greet(
    name: str = typer.Option(..., "--name", "-n", help="要问候的名字"),
    times: int = typer.Option(1, "--times", "-t", help="问候次数", min=1, max=10),
    excited: bool = typer.Option(False, "--excited", "-e", help="是否激动模式"),
):
    """
    多次问候

    示例:
        uv run example.py greet --name Alice --times 3 --excited
    """
    logger.debug(f"问候配置：name={name}, times={times}, excited={excited}")

    for i in range(times):
        greeting = f"Hello, {name}!"
        if excited:
            greeting = greeting.upper() + " 🎉"
        else:
            greeting = greeting + " 👋"

        logger.info(f"第 {i + 1}/{times} 次问候：{greeting}")
        print(f"[{i + 1}/{times}] {greeting}")


@app.command()
def rich_demo():
    """
    Rich 包功能演示 - 颜色、表格、进度条、Markdown、语法高亮、树形结构等
    """
    console = Console()

    # 标题
    console.print(Rule("Rich 功能演示", style="bold magenta"))
    console.print()

    # 1. 颜色示例
    console.print(Panel("🎨 颜色示例", style="bold blue"))
    colors = [
        ("红色", "red"),
        ("绿色", "green"), 
        ("蓝色", "blue"),
        ("黄色", "yellow"),
        ("紫色", "purple"),
        ("青色", "cyan"),
        ("白色", "white"),
        ("黑色", "black"),
    ]
    
    color_texts = [Text(name, style=style) for name, style in colors]
    console.print(Columns(color_texts, equal=True, expand=True))
    console.print()

    # 2. 表格示例
    console.print(Panel("📊 表格示例", style="bold green"))
    table = Table(title="系统信息", show_header=True, header_style="bold magenta")
    table.add_column("项目", style="dim")
    table.add_column("值")
    table.add_column("状态", justify="right")
    
    table.add_row("操作系统", sys.platform, "[green]✓[/green]")
    table.add_row("Python版本", sys.version.split()[0], "[yellow]⚠[/yellow]")
    table.add_row("工作目录", str(Path.cwd()), "[blue]ℹ[/blue]")
    table.add_row("调试模式", "开启" if DEBUG_MODE else "关闭", "[cyan]•[/cyan]")
    
    console.print(table)
    console.print()

    # 3. 进度条示例
    console.print(Panel("⏳ 进度条示例", style="bold yellow"))
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task1 = progress.add_task("下载文件...", total=100)
        for i in range(100):
            progress.update(task1, advance=1)
            time.sleep(0.02)
        
        task2 = progress.add_task("处理数据...", total=50)
        for i in range(50):
            progress.update(task2, advance=1)
            time.sleep(0.04)

    console.print()

    # 4. Markdown 渲染示例
    console.print(Panel("📝 Markdown 渲染示例", style="bold cyan"))
    md_content = """
# 这是一个标题

**粗体文本**和*斜体文本*

- 列表项 1
- 列表项 2  
- 列表项 3

> 这是一段引用文本

```python
print("Hello, World!")
```
"""
    markdown = Markdown(md_content)
    console.print(markdown)
    console.print()

    # 5. 语法高亮示例
    console.print(Panel("💻 语法高亮示例", style="bold purple"))
    code = '''
import typer
from rich.console import Console

console = Console()
console.print("Hello, Rich!")

@app.command()
def hello():
    console.print("This is syntax highlighting!")
'''
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    console.print()

    # 6. 树形结构示例
    console.print(Panel("🌳 树形结构示例", style="bold red"))
    tree = Tree("项目结构")
    tree.add(Tree("src"))
    tree.add(Tree("tests"))
    tree.add(Tree("docs").add(Tree("api")).add(Tree("guides")))
    tree.add(Tree("config"))
    tree.add(Tree("logs"))
    
    console.print(tree)
    console.print()

    # 7. 组合面板示例
    console.print(Panel("🎯 组合面板示例", style="bold yellow"))
    panel1 = Panel("这是第一个面板", title="面板 1", border_style="green")
    panel2 = Panel("这是第二个面板", title="面板 2", border_style="blue")
    console.print(Columns([panel1, panel2], equal=True, expand=True))

    console.print(Rule("演示结束", style="bold"))


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
