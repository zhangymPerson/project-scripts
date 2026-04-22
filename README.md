# 支撑全栈项目 - 脚本项目

> 一个按职责域组织的通用项目支撑脚本仓库，面向全栈开发工程师

## 📖 项目简介

本项目是一个**通用的项目支撑脚本仓库**，为全栈项目提供数据库管理、测试、部署、CI/CD、数据处理等基础设施支持。

核心理念：**目录反映的是"你在做什么事"，不是"你用了什么工具"**。按职责域组织，每个目录是一个完整的"做事单元"。

## 🚀 快速开始

### 前置要求

- Python 3.11+（推荐安装 [uv](https://github.com/astral-sh/uv)）
- Bash 5.0+
- [Task](https://taskfile.dev/)（任务运行器）
- [just](https://github.com/casey/just)（可选，更好的任务运行器）

### 克隆项目

```bash
git clone <your-repo>/project-scripts.git
cd project-scripts
```

### 使用 Task 命令

```bash
# 查看所有可用任务
task --list

# 运行特定任务
task browser                    # 浏览器自动化
task db:mysql                 # MySQL 数据库操作
task storage:s3               # S3 存储操作
task test:api                 # API 测试
task deploy:k8s:helm:myapp    # Kubernetes Helm 部署
task scripts:data:etl         # 运行 ETL 数据处理
```

### 使用 just 命令（如果有 justfile）

```bash
# 查看 just 任务
just

# 常用 just 命令
just format                   # 格式化代码
```

### 单独运行脚本

**Python 脚本**使用 PEP 723 内联依赖声明，通过 `uv run` 运行：

```bash
# 浏览器自动化
uv run browser/browser_example_baidu.py

# 数据库操作
uv run db/mysql/example_mysql.py connect
uv run db/mysql/example_mysql.py tables
uv run ops/generate_token.py

# 运维工具
uv run ops/diagnose_db.py
```

**Shell 脚本**自包含（不 source 外部文件）：

```bash
bash db/mysql/migrate.sh
bash examples/shell/example.sh
DEBUG=true bash examples/shell/example.sh
```

## 📁 目录结构

```
project-scripts/
│
├── browser/             # 浏览器自动化 — E2E 测试、爬虫、自动化操作 | Playwright, Selenium
├── db/                  # 数据库层 — 所有数据存储相关
├── storage/             # 存储 & 文件处理 — 非结构化数据
├── mq/                  # 消息队列层
├── test/                # 测试层 — 所有验证相关
├── data/                # 数据处理层 — ETL / 清洗 / 迁移
├── deploy/              # 部署层 — 运行时编排
├── ci/                  # CI/CD 配置层
├── cron/                # 定时任务层
├── ops/                 # 运维工具层 — 诊断/紧急工具
├── docs/                # 文档
├── examples/            # 代码样例 — 最佳实践参考
│
├── .env.example         # 环境变量模板
├── .gitignore
├── justfile             # 任务运行器
└── README.md
```

### 各目录职责

| 目录        | 职责                         | 典型场景                            |
| ----------- | ---------------------------- | ----------------------------------- |
| `browser/`  | 浏览器自动化、E2E 测试、爬虫 | Playwright 自动化、Selenium 爬虫    |
| `db/`       | 数据库迁移、种子数据、备份   | MySQL 迁移、MongoDB 索引管理        |
| `storage/`  | 对象存储操作、文件处理       | S3→MinIO 迁移、图片压缩             |
| `mq/`       | 消息队列管理                 | RabbitMQ 队列创建、Kafka Topic 管理 |
| `test/`     | API 测试、E2E 测试、性能测试 | REST Client 测试、Playwright E2E    |
| `data/`     | ETL、数据清洗、跨库同步      | CSV 导入、用户数据清洗              |
| `deploy/`   | Docker Compose、K8s 配置     | 多环境部署、Kustomize overlays      |
| `ci/`       | CI/CD 流水线配置             | GitHub Actions、GitLab CI           |
| `cron/`     | 定时任务脚本和配置           | 数据库备份、健康检查                |
| `ops/`      | 一次性运维工具               | 数据库诊断、Token 生成              |
| `docs/`     | 操作手册、架构文档           | runbook、ADR                        |
| `examples/` | 代码样例、最佳实践           | 各类文件的参考实现                  |

## 💡 核心设计原则

### 1. 按职责域切分，不按文件类型

```
❌ 错误：scripts/  templates/  configs/
✅ 正确：db/  deploy/  test/  ci/
```

**依据**：修改一个功能时，你需要同时看到相关的脚本、配置、模板。按职责域组织，它们就在同一个目录树下。

### 2. 职责单一，一个目录一件事

每个顶层目录的职责边界清晰。`db/` 只管数据库，`deploy/` 只管部署。

### 3. 深度不超过 4 层

```
db/mysql/migrations/001_create_users.sql  # 四层，刚好
```

### 4. 叶子目录是"可执行单元"

最底层目录包含完整的可执行上下文。如 `db/mysql/` 有迁移脚本 + SQL 文件 + 种子数据。

### 5. 脚本自包含

- **Python**：使用 `uv` 内联依赖（PEP 723）
- **Shell**：不 source 外部文件，函数内联

任意一个脚本拷走就能跑。

## 🛠️ 使用指南

### Python 脚本：uv 内联依赖

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.0", "python-dotenv>=1.0"]
# ///

import pandas as pd
```

运行：

```bash
uv run script.py
```

### Shell 脚本：自包含

```bash
#!/usr/bin/env bash
set -euo pipefail

# 内联工具函数
log_info() { echo "[INFO] $*"; }

# 主逻辑
main() {
    log_info "脚本执行"
}
main
```

### SQL 迁移文件：命名约定

```
001_create_users.sql      # 迁移文件
rollback_001.sql          # 回滚文件
```

### .http 文件：API 测试

安装 VS Code 插件 [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)，然后：

```http
### 获取用户列表
GET {{baseUrl}}/api/v1/users
Authorization: Bearer {{token}}
```

## 📚 文档导航

| 文档                                                     | 说明         |
| -------------------------------------------------------- | ------------ |
| [project-scripts-design.md](./project-scripts-design.md) | 详细设计指南 |
| [docs/runbook.md](./docs/runbook.md)                     | 操作手册     |
| [docs/architecture.md](./docs/architecture.md)           | 架构说明     |
| [AGENTS.md](./AGENTS.md)                                 | AI 助手指南  |
| [examples/](./examples/)                                 | 代码样例     |

## 🔧 常用命令

### Task 命令

```bash
# 查看所有任务
task --list

# 浏览器自动化
task browser                    # 浏览器自动化
task browser:default          # 默认浏览器任务

# 数据库操作
task db:mysql                 # MySQL 数据库
task db:postgresql            # PostgreSQL 数据库
task db:mongodb               # MongoDB 数据库
task db:redis                 # Redis 缓存
task db:elasticsearch         # Elasticsearch 搜索
task db:sqlite                # SQLite 轻量数据库

# 存储操作
task storage:s3               # S3 对象存储
task storage:minio            # MinIO 对象存储
task storage:file-tools       # 文件处理工具

# 消息队列
task mq:rabbitmq              # RabbitMQ 消息队列
task mq:kafka                 # Kafka 消息队列
task mq:redis-streams         # Redis Streams

# 测试
task test:api                 # API 测试
task test:integration         # 集成测试
task test:load                # 性能测试
task test:fixtures            # 测试数据

# 数据处理
task data:clean               # 数据清洗
task data:etl                 # ETL 处理
task data:transfer            # 数据转移

# 部署
task deploy:k8s:helm:myapp    # Kubernetes Helm 应用
task deploy:compose           # Docker Compose
task deploy:dockerfiles       # Docker 镜像构建

# 运维工具
task ops:default              # 运维工具
task scripts:devops:diagnose-db  # 数据库诊断
task scripts:data:etl         # 运行 ETL 脚本

# 脚本工具
task scripts:data:clean       # 清理数据
task scripts:infra:k8s        # Kubernetes 管理
```

### just 命令（如果有 justfile）

```bash
# 格式化代码
just format

# Git 操作
just fetch
just pull
just push
```

## 📋 与其他方案对比

| 方案              | 优点                     | 缺点           | 适用场景             |
| ----------------- | ------------------------ | -------------- | -------------------- |
| **本方案**        | 职责清晰，可扩展，自解释 | 顶层目录多     | 中大型项目、团队协作 |
| `scripts/` 一把梭 | 简单                     | 文件多了找不到 | 个人小项目           |
| Monorepo 工具链   | 强大                     | 过重           | 多包 monorepo        |
| Ansible/Terraform | 成熟                     | 只覆盖部署     | 纯运维项目           |

## ❓ 常见问题

**Q: 项目很小，不需要这么多目录怎么办？**

从你需要的开始。空目录不要创建，结构是"长出来的"，不是"一次建好的"。

**Q: 如何使用 Task 命令？**

```bash
# 查看所有可用任务
task --list

# 运行特定任务
task db:mysql                 # MySQL 数据库操作
task storage:s3               # S3 存储操作
task test:api                 # API 测试
```

**Q: 如何在团队中推广？**

1. 先在一个项目里跑通
2. 写一份 `runbook.md`（操作手册）
3. 新人入职时做 onboarding demo

**Q: `ops/` 和 `cron/jobs/` 有什么区别？**

- `cron/jobs/`：周期性、自动化（每天备份）
- `ops/`：按需、手动（诊断、紧急修复）

**Q: Taskfile.yml 文件的作用是什么？**

Taskfile.yml 文件用于定义和管理项目中的各种自动化任务。每个目录都有一个 Taskfile.yml 文件，可以包含子目录的任务引用和别名，形成完整的任务层次结构。

```bash
# 示例：查看任务层次
task --list | head -20
# 显示所有可用的任务及其别名
```

**Q: Taskfile.yml 中配置在当前 Taskfile.yml 所在目录执行**

需配置
```yaml
# 子任务目录中的 Taskfile.yml
version: '3'

tasks:
  your-task:
    dir: '{{.TASKFILE_DIR}}'
    cmds:
      - echo "当前目录是：$(pwd)"
      - # 你的其他命令
```

## 🎯 总结

核心思想：**按职责域组织目录，每个目录是一个完整的"做事单元"**。

| 原则       | 做法                                  |
| ---------- | ------------------------------------- |
| 职责域切分 | 顶层目录按业务职责分                  |
| 职责单一   | 一个目录一件事                        |
| 深度克制   | 不超过 4 层                           |
| 叶子即执行 | 最底层包含完整上下文                  |
| 脚本自包含 | Python 内联依赖，Shell 不 source 外部 |
| 配置外置   | 敏感信息走环境变量                    |
| 任务驱动   | 使用 Taskfile.yml 管理所有操作        |

## 📄 许可证

MIT License

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

---

**作者**: zhangyanming
**创建时间**: 2026 年 3 月
