# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## 项目概览

这是一个**按职责域组织的通用项目支撑脚本仓库**，为全栈项目提供数据库管理、测试、部署、CI/CD、数据处理、运维工具等基础设施支持。

## 目录结构（按职责域划分）

| 目录 | 职责 | 典型技术 |
|------|------|----------|
| `browser/` | 浏览器自动化、E2E 测试、爬虫 | Playwright, Selenium, Puppeteer |
| `db/` | 数据库迁移、种子数据、备份 | MySQL, PostgreSQL, SQLite, MongoDB, Redis, Elasticsearch |
| `storage/` | 对象存储操作、文件处理 | S3, MinIO, 图片压缩、去重、格式转换 |
| `mq/` | 消息队列管理 | RabbitMQ, Kafka, Redis Streams |
| `test/` | API 测试、集成测试、性能测试 | pytest, Hurl, Locust, k6, .http 文件 |
| `data/` | ETL、数据清洗、跨库同步 | Python 脚本 |
| `deploy/` | Docker Compose、K8s 配置 | docker-compose, kubectl, Kustomize, Helm |
| `ci/` | CI/CD 流水线配置 | GitHub Actions, GitLab CI |
| `cron/` | 定时任务脚本和配置 | Cron 任务 |
| `ops/` | 按需诊断/应急工具 | Python 诊断脚本 |
| `docs/` | 操作手册、架构文档、ADR | Markdown |
| `examples/` | 代码样例、最佳实践 | Python, Shell, HTTP, Hurl, SQL |

## 核心设计原则

1. **按职责域切分**，不按文件类型。是 `db/` 而不是 `scripts/`。
2. **一个目录只做一件事。** `db/` 只管数据库，`deploy/` 只管部署。
3. **目录深度不超过 4 层。** 例如 `db/mysql/migrations/001_create_users.sql`
4. **叶子目录是"可执行单元"** — 包含完整上下文（脚本 + SQL + 种子数据）。
5. **脚本自包含** — 任意脚本拷走就能独立运行。

## 开发命令

### 前置要求
- Python 3.11+
- Bash 5.0+
- [just](https://github.com/casey/just)（任务运行器）
- [uv](https://github.com/astral-sh/uv)（Python 包管理器）

### just 常用命令

```bash
just                  # 格式化 justfile 并列出任务
just run              # 通过 fzf 交互式选择任务
just clear            # 清理日志、缓存、临时文件

# 浏览器
just -f browser/justfile mac-start-edge    # 启动 Edge 浏览器（Playwright 调试模式）
just -f browser/justfile baidu            # 运行百度搜索示例

# 数据库
just db-migrate       # 运行 MySQL 迁移
just db-seed          # 加载种子数据
just db-backup        # 备份数据库
just example-mysql    # 运行 MySQL 示例脚本
just example-sqlite   # 运行 SQLite 示例脚本

# 测试
just test-api         # 运行 API 测试（test/api 下的 pytest）
just test-integration # 运行集成测试（test/integration 下的 pytest）
just test-load        # 运行性能测试（test/load 下的 locust）
just test-http        # 列出 HTTP 测试文件
just example-http-hurl # 运行 Hurl 测试

# 部署
just deploy-dev       # Docker Compose 开发环境
just deploy-staging   # Docker Compose 预发布环境
just deploy-prod      # Docker Compose 生产环境
just k8s-apply        # 应用 K8s 配置（kustomize dev overlay）

# 运维
just ops-diagnose     # 运行数据库诊断
just ops-token        # 生成 Token

# Git
just fetch            # git fetch --all --tags --prune
just pull             # git pull --rebase
just push             # 推送到 origin, gitcode, gitee（main 分支）

# 格式化
just format           # 格式化 justfile + ruff 检查 Python 文件
```

### 单独运行脚本

**Python 脚本**使用 PEP 723 内联依赖声明，通过 `uv run` 运行：
```bash
# 浏览器自动化
just -f browser/justfile mac-start-edge    # 先启动浏览器
uv run browser/browser_example_baidu.py    # 再运行示例脚本

# 数据库操作
uv run db/mysql/example_mysql.py connect
uv run db/mysql/example_mysql.py tables
uv run db/mysql/example_mysql.py query --sql "SELECT * FROM users LIMIT 5"
uv run ops/generate_token.py
```

**Shell 脚本**自包含（不 source 外部文件）：
```bash
bash db/mysql/migrate.sh
bash examples/shell/example.sh
DEBUG=true bash examples/shell/example.sh
```

**HTTP 测试文件**（`.http`）— 使用 VS Code REST Client 插件。

**Hurl 测试**：
```bash
source examples/http/hurl/hurl.env && hurl -v examples/http/hurl/hurl_test_example.hurl
```

### 测试

```bash
# API 测试（pytest）
cd test/api && pytest -v

# 集成测试（pytest）
cd test/integration && pytest -v

# 性能测试（Locust）
cd test/load && locust --headless -u 100 -r 10 --run-time 60s

# 视觉回归测试
uv run test/visual/capture.py
uv run test/visual/compare.py
```

### 代码检查与格式化

```bash
just format               # justfile 格式化 + ruff 检查修复
uvx ruff check --fix .    # Python 代码检查（ruff）
```

## Python 脚本约定

所有 Python 脚本遵循以下模式：

1. **PEP 723 内联依赖** 写在文件头部：
   ```python
   # /// script
   # requires-python = ">=3.11"
   # dependencies = ["pandas>=2.0", "python-dotenv>=1.0"]
   # ///
   ```

2. **CLI 使用 `typer`** — 命令暴露为 typer 子命令
3. **日志使用 `loguru`** — 同时输出到控制台（带颜色）和文件（自动轮转）
4. **配置通过环境变量** — 不硬编码密钥
5. **日志目录** — 项目根目录下的 `logs/`（自动创建）

## Shell 脚本约定

```bash
#!/usr/bin/env bash
set -euo pipefail

# 内联工具函数（不 source 外部文件）
log_info() { echo "[INFO] $*"; }

main() {
    # 主逻辑
}
main
```

## SQL 迁移文件命名

```
001_create_users.sql      # 迁移文件（编号 + 描述性名称）
rollback_001.sql          # 对应的回滚文件
```

## 部署

### Docker Compose
- `deploy/compose/docker-compose.dev.yml` — 开发环境
- `deploy/compose/docker-compose.test.yml` — 测试环境
- `deploy/compose/docker-compose.prod.yml` — 生产环境

### Kubernetes
- 基础配置：`deploy/k8s/base/`（kustomization.yaml, deployment.yaml, service.yaml 等）
- 环境覆盖：`deploy/k8s/overlays/{dev,staging,prod}/`
- Helm Charts：`deploy/k8s/helm/myapp/`

### 应用 K8s 配置
```bash
kubectl apply -k deploy/k8s/overlays/dev
kubectl apply -k deploy/k8s/overlays/prod
```

## 环境变量

- `.env.example` — 环境变量模板
- `.env` 及其变体已被 gitignore — 永远不要提交密钥
- 数据库配置使用 `MYSQL_*`、`POSTGRES_*` 等环境变量
- 调试模式：`DEBUG=true` 启用详细日志
