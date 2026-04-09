#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.40", "loguru>=0.7"]
# ///
"""
@file : browser_example_baidu.py
@desc : 连接已启动的 Edge 浏览器（remote-debugging-port=9222），打开百度进行搜索
        运行方式: uv run browser/browser_example_baidu.py
        前置条件: 先执行 just -f browser/justfile start-edge 启动浏览器
@date : 2026-04-09
@auth : zhangyanming
@version : 1.0
"""

import os
import sys

from loguru import logger
from playwright.sync_api import Playwright, sync_playwright

# =============================================================================
# 日志配置
# =============================================================================

# 日志级别，DEBUG 或 INFO
level = os.getenv("DEBUG", "").lower() in ("true", "1", "t") and "DEBUG" or "INFO"
# 移除默认的 handler
logger.remove()
# 输出到控制台和文件
logger.add(sys.stderr, level=level)
logger.add(f"{os.path.splitext(os.path.basename(__file__))[0]}.log", level=level)


def run(playwright: Playwright) -> None:
    """连接已启动的 Edge 浏览器，执行百度搜索"""

    # 连接到已启动的 Edge 浏览器（CDP 协议）
    logger.debug("正在连接到 Edge 浏览器 (cdp_endpoint: http://localhost:9222)...")
    browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
    logger.debug("浏览器连接成功")

    # 获取默认上下文和页面
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    logger.debug(f"获取浏览器上下文，当前上下文数: {len(browser.contexts)}")

    page = context.new_page()
    logger.debug("创建新页面")

    # 打开百度
    logger.debug("正在访问百度首页...")
    page.goto("https://www.baidu.com/")
    logger.debug(f"页面标题: {page.title()}")

    # 搜索 playwright
    search_keyword = "playwright"
    logger.debug(f"在搜索框输入关键词: {search_keyword}")
    page.get_by_role("textbox").fill(search_keyword)

    logger.debug("点击「百度一下」按钮")
    page.get_by_role("button", name="百度一下").click()

    # 等待搜索结果加载
    page.wait_for_load_state("networkidle")
    logger.debug(f"搜索结果页标题: {page.title()}")
    logger.debug(f"当前 URL: {page.url}")

    # ---------------------
    logger.debug("测试完成，关闭页面和浏览器连接")
    page.close()
    browser.close()


def main() -> None:
    """主入口"""
    logger.info("=== 百度搜索自动化测试开始 ===")
    logger.info(f"日志级别: {level}")
    logger.info(f"日志文件: {os.path.splitext(os.path.basename(__file__))[0]}.log")

    with sync_playwright() as playwright:
        run(playwright)

    logger.info("=== 百度搜索自动化测试结束 ===")


if __name__ == "__main__":
    main()
