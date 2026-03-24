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


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
