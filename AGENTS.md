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
- [Task](https://taskfile.dev/)（任务运行器）
- [just](https://github.com/casey/just)（可选，更好的任务运行器）
- [uv](https://github.com/astral-sh/uv)（Python 包管理器）

### Task 常用命令

```bash
# 查看所有可用任务
task --list

# 查看特定目录的任务
task --list browser
task --list db:mysql
task --list storage:s3

# 运行特定任务
task browser                    # 浏览器自动化
task db:mysql                   # MySQL 数据库操作
task storage:s3                 # S3 存储操作
task test:api                   # API 测试
task deploy:k8s:helm:myapp      # Kubernetes Helm 部署
task scripts:data:etl           # 运行 ETL 数据处理

# 使用别名运行任务
task mysql                      # 等同于 task db:mysql
task s3                         # 等同于 task storage:s3
task api                        # 等同于 task test:api

# 查看任务帮助信息
task --help
```

### just 常用命令

```bash
just                  # 格式化 justfile 并列出任务
just run              # 通过 fzf 交互式选择任务
just clear            # 清理日志、缓存、临时文件

# Git
just fetch            # git fetch --all --tags --prune
just pull             # git pull --rebase
just push             # 推送到 origin, gitcode, gitee（main 分支）

# 格式化
just format           # 格式化 justfile + ruff 检查 Python 文件
```

### Task 任务执行

**Task 命令** - 使用 Taskfile.yml 定义的任务：
```bash
# 运行特定任务
task browser                    # 浏览器自动化
task db:mysql                   # MySQL 数据库操作
task storage:s3                 # S3 存储操作
task test:api                   # API 测试
task deploy:k8s:helm:myapp      # Kubernetes Helm 部署

# 运行功能性任务
task scripts:data:etl           # 运行 ETL 数据处理
task scripts:devops:diagnose-db # 数据库诊断
task scripts:infra:k8s          # Kubernetes 管理
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

## Taskfile.yml 约定

所有 Taskfile.yml 文件遵循以下模式：

1. **includes 结构** - 包含子目录的 Taskfile.yml：
   ```yaml
   includes:
     mysql:
       taskfile: ./mysql/Taskfile.yml
       aliases:
         - mysql
     postgresql:
       taskfile: ./postgresql/Taskfile.yml
       aliases:
         - pg
         - postgres
   ```

2. **任务定义** - 定义可执行的任务：
   ```yaml
   tasks:
     default:
       desc: 默认任务描述
       cmds:
         - echo "Hello, world!"
     migrate:
       desc: 运行数据库迁移
       cmds:
         - bash migrate.sh
   ```

3. **别名系统** - 为任务提供快捷方式：
   ```yaml
   aliases:
     - mysql      # 主别名
     - mariadb    # 额外别名
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

## Task 任务系统

### 任务层次结构

项目使用 Taskfile.yml 文件定义任务层次结构：

```
task --list | head -10
├── browser (aliases: browser)
├── ci (aliases: ci)
├── cron (aliases: cron)
├── data (aliases: data)
├── db (aliases: db)
├── deploy (aliases: deploy)
├── docs (aliases: docs)
├── examples (aliases: examples)
├── mq (aliases: mq)
└── ops (aliases: ops)
```

### 子目录任务

每个主要目录都有其子目录任务：

```bash
# 数据库任务
task db:mysql                 # MySQL 数据库
task db:postgresql            # PostgreSQL 数据库
task db:mongodb               # MongoDB 数据库
task db:redis                 # Redis 缓存
task db:elasticsearch         # Elasticsearch 搜索

# 存储任务
task storage:s3               # S3 对象存储
task storage:minio            # MinIO 对象存储
task storage:file-tools       # 文件处理工具

# 测试任务
task test:api                 # API 测试
task test:integration         # 集成测试
task test:load                # 性能测试
task test:fixtures            # 测试数据

# 部署任务
task deploy:k8s:helm:myapp    # Kubernetes Helm 应用
task deploy:compose           # Docker Compose
task deploy:dockerfiles       # Docker 镜像构建
```

### 功能性任务

除了目录任务，还有各种功能性任务：

```bash
# 数据处理
task scripts:data:etl         # 运行 ETL 脚本
task scripts:data:clean       # 清理数据
task scripts:data:transfer      # 数据转移

# 运维工具
task scripts:devops:diagnose-db  # 数据库诊断
task scripts:devops:generate-token # 生成 Token
task scripts:devops:reset-cache   # 重置缓存

# 基础设施
task scripts:infra:k8s        # Kubernetes 管理
task scripts:infra:docker     # Docker 操作
task scripts:infra:helm       # Helm 操作
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

## Task 使用技巧

### 查看任务层次
```bash
# 查看所有任务
task --list

# 查看特定前缀的任务
task --list | grep "db:"
task --list | grep "storage:"
```

### 运行任务
```bash
# 运行顶层任务
task browser
task db:mysql
task storage:s3

# 运行功能性任务
task scripts:data:etl
task scripts:devops:diagnose-db

# 使用别名
task mysql      # 等同于 task db:mysql
task s3         # 等同于 task storage:s3
task api        # 等同于 task test:api
```

### 任务开发
当添加新任务时，确保：
1. 在正确的目录创建或更新 Taskfile.yml
2. 包含适当的 includes 和 aliases
3. 定义清晰的任务描述
4. 测试任务是否正常工作
