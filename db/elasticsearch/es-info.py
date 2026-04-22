#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
Elasticsearch 索引信息查询脚本（兼容 ES 7.x）

用法:
    uv run db/elasticsearch/es-info.py --help
    uv run db/elasticsearch/es-info.py indices
    uv run db/elasticsearch/es-info.py mapping --index my_index

环境变量 (设置 ES 连接):
    ES_URL       ES 完整地址，支持 ip:port 或完整 URL 格式
                 - ip:port 形式:      192.168.1.1:9200  (默认协议 http)
                 - 完整 URL 形式:     https://es.api.com
                 - 带端口完整 URL:    https://es.api.com:443
                 (默认: http://localhost:9200)
    ES_USER      ES 用户名 (默认: 空，不鉴权)
    ES_PASSWORD  ES 密码 (默认: 空)
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "loguru>=0.7",
#     "typer>=0.9",
#     "elasticsearch7>=7.17",
# ]
# ///

import json
import os
import re
import sys
from pathlib import Path

import typer
from elasticsearch7 import Elasticsearch
from loguru import logger
from typer import Typer

# =============================================================================
# 配置
# =============================================================================

ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "")
ES_PASSWORD = os.getenv("ES_PASSWORD", "")

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
# ES 连接管理
# =============================================================================


def _normalize_es_url(url: str) -> str:
    """将用户输入的地址规范化为完整 URL

    支持:
        - ip:port          → http://ip:port
        - https://es.api.com → https://es.api.com
        - http://ip:port   → http://ip:port
    """
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    # ip:port 形式，补充 http://
    return f"http://{url}"


def _get_es_client() -> Elasticsearch:
    """构建 Elasticsearch 7.x 客户端"""
    es_url = _normalize_es_url(ES_URL)
    if ES_USER and ES_PASSWORD:
        client = Elasticsearch(
            [es_url],
            http_auth=(ES_USER, ES_PASSWORD),
        )
    else:
        client = Elasticsearch([es_url])
    logger.debug(f"ES 连接: {es_url}")
    return client


# =============================================================================
# 白名单校验
# =============================================================================

_INDEX_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.+]{1,255}$")


def _validate_index_name(name: str) -> str:
    """校验索引名合法性"""
    if not _INDEX_NAME_PATTERN.match(name):
        raise ValueError(
            f"非法索引名: {name!r}，仅允许字母、数字、下划线、连字符、点号、加号"
        )
    return name


# =============================================================================
# 核心函数
# =============================================================================


def get_indices() -> list[dict]:
    """获取 ES 所有索引信息列表

    Returns:
        索引信息字典列表，包含 index, health, status, docs.count, store.size 等字段
    """
    client = _get_es_client()
    try:
        result = client.cat.indices(format="json")
        indices = sorted(result, key=lambda x: x.get("index", ""))
        logger.info(f"共获取 {len(indices)} 个索引")
        return indices
    finally:
        client.close()
        logger.debug("ES 连接已关闭")


def get_index_mapping(index_name: str) -> dict:
    """获取单个索引的 mapping（结构）信息

    Args:
        index_name: 索引名，会进行合法性校验

    Returns:
        该索引的 mapping 字典

    Raises:
        ValueError: 索引名不合法
        elasticsearch7.NotFoundError: 索引不存在
    """
    safe_name = _validate_index_name(index_name)
    client = _get_es_client()
    try:
        result = client.indices.get_mapping(index=safe_name)
        logger.info(f"获取索引 mapping 成功: {safe_name}")
        return result
    finally:
        client.close()
        logger.debug("ES 连接已关闭")


def search_index(index_name: str, query: dict, size: int = 10) -> dict:
    """在指定索引中执行搜索查询

    Args:
        index_name: 索引名
        query: ES DSL query 字典
        size: 返回文档数量 (默认: 10)

    Returns:
        ES 搜索结果字典
    """
    safe_name = _validate_index_name(index_name)
    client = _get_es_client()
    try:
        body = {"query": query, "size": size}
        result = client.search(index=safe_name, body=body)
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]
        total_value = total["value"] if isinstance(total, dict) else total
        logger.info(f"搜索完成: 命中 {total_value} 条, 返回 {len(hits)} 条")
        return result
    finally:
        client.close()
        logger.debug("ES 连接已关闭")


# =============================================================================
# 命令行接口
# =============================================================================

app = Typer(
    help="""Elasticsearch 索引信息查询脚本（兼容 ES 7.x）

环境变量 (设置 ES 连接):
    ES_URL       ES 完整地址，支持 ip:port 或完整 URL 格式
                 - ip:port 形式:      192.168.1.1:9200  (默认协议 http)
                 - 完整 URL 形式:     https://es.api.com
                 - 带端口完整 URL:    https://es.api.com:443
                 (默认: http://localhost:9200)
    ES_USER      ES 用户名 (默认: 空，不鉴权)
    ES_PASSWORD  ES 密码 (默认: 空)
"""
)


@app.command()
def indices():
    """获取 ES 所有索引信息列表

    示例:
        uv run db/elasticsearch/es-info.py indices
    """
    result = get_indices()
    if result:
        logger.debug(f"ES 中的索引 ({len(result)} 个):")
        for idx in result:
            name = idx.get("index", "?")
            health = idx.get("health", "?")
            status = idx.get("status", "?")
            docs = idx.get("docs.count", "?")
            size = idx.get("store.size", "?")
            print(f"  {health:<8} {status:<8} {docs:<12} {size:<12} {name}")
        print(f"\n共 {len(result)} 个索引")
        print("列说明: health | status | docs.count | store.size | index")
    else:
        logger.debug("ES 中没有索引")


@app.command()
def mapping(
    index: str = typer.Option(..., "--index", "-i", help="索引名"),
):
    """获取单个索引的 mapping（结构）信息

    示例:
        uv run db/elasticsearch/es-info.py mapping --index my_index
        uv run db/elasticsearch/es-info.py mapping -i my_index
    """

    try:
        result = get_index_mapping(index)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"ES 错误: {e}")
        logger.debug(f"ES 错误: {e}")
        raise typer.Exit(code=1)


@app.command()
def query(
    index: str = typer.Option(..., "--index", "-i", help="索引名"),
    q: str = typer.Option(..., "--query", "-q", help="ES DSL query JSON"),
    size: int = typer.Option(10, "--size", "-s", help="返回文档数量"),
):
    """在指定索引中执行搜索查询

    示例 — 获取索引 users 全部数据 (最多100条):
        uv run db/elasticsearch/es-info.py query -i users -q '{"match_all": {}}' -s 100

    单条件查询 — 精确匹配:
        uv run db/elasticsearch/es-info.py query -i users -q '{"term": {"status": "active"}}'

    单条件查询 — 全文检索:
        uv run db/elasticsearch/es-info.py query -i users -q '{"match": {"name": "张三"}}'

    单条件查询 — 通配符:
        uv run db/elasticsearch/es-info.py query -i users -q '{"wildcard": {"email": "*@gmail.com"}}'

    单条件查询 — 范围查询:
        uv run db/elasticsearch/es-info.py query -i users -q '{"range": {"age": {"gte": 18, "lte": 30}}}'

    多条件查询 — must (AND):
        uv run db/elasticsearch/es-info.py query -i users -q '{"bool": {"must": [{"term": {"status": "active"}}, {"range": {"age": {"gte": 20}}}]}}'

    多条件查询 — should (OR):
        uv run db/elasticsearch/es-info.py query -i users -q '{"bool": {"should": [{"term": {"city": "北京"}}, {"term": {"city": "上海"}}]}}'

    多条件查询 — must + must_not:
        uv run db/elasticsearch/es-info.py query -i users -q '{"bool": {"must": [{"match": {"title": "工程师"}}], "must_not": [{"term": {"status": "deleted"}}]}}'
    """

    try:
        query_dict = json.loads(q)
    except json.JSONDecodeError as e:
        logger.error(f"query 不是合法的 JSON: {e}")
        raise typer.Exit(code=1)

    if not isinstance(query_dict, dict):
        logger.error('query 必须是 JSON 对象，如 {"match_all": {}}')
        raise typer.Exit(code=1)

    try:
        result = search_index(index, query_dict, size)
        hits = result["hits"]["hits"]
        total = result["hits"]["total"]
        total_value = total["value"] if isinstance(total, dict) else total
        print(f"命中 {total_value} 条, 返回 {len(hits)} 条:\n")
        for hit in hits:
            src = hit.get("_source", {})
            # print(json.dumps(src, indent=2, ensure_ascii=False))
            print(json.dumps(src, ensure_ascii=False))
    except ValueError as e:
        logger.error(str(e))
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"ES 错误: {e}")
        logger.debug(f"ES 错误: {e}")
        raise typer.Exit(code=1)


# =============================================================================
# 入口点
# =============================================================================

if __name__ == "__main__":
    app()
