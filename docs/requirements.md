# 项目需求文档

## 1. 项目概述

### 1.1 项目名称

project-scripts — 全栈项目支撑脚本仓库

### 1.2 项目背景

面向全栈开发工程师，提供一个按职责域组织的通用项目支撑脚本仓库，为全栈项目提供数据库管理、测试、部署、CI/CD、数据处理等基础设施支持。

### 1.3 核心理念

目录反映的是"你在做什么事"，不是"你用了什么工具"。按职责域组织，每个目录是一个完整的"做事单元"。

## 2. 目标用户

| 角色             | 需求                                  |
| ---------------- | ------------------------------------- |
| 全栈开发工程师   | 快速获取各技术栈的脚本和配置参考      |
| DevOps 工程师    | 部署、CI/CD、运维工具的标准化实现     |
| 新入职成员       | 通过 examples 目录快速学习项目规范    |
| AI 助手 (Claude) | 通过 AGENTS.md 理解项目架构并辅助开发 |

## 3. 功能需求

### 3.1 核心功能模块

#### 3.1.1 数据库管理 (`db/`)

- **MySQL**: 备份、迁移、种子数据、信息查询
- **PostgreSQL**: 备份、迁移、种子数据
- **MongoDB**: 聚合操作、集合导出、索引管理
- **Redis**: 缓存检查、速率限制器
- **Elasticsearch**: 索引管理、重建索引、信息查询
- **SQLite**: 轻量数据库示例和迁移

#### 3.1.2 部署编排 (`deploy/`)

- **Docker Compose**: 多环境配置 (dev/test/prod)
- **Dockerfiles**: 多语言镜像构建 (Python/Node/Go/Nginx)
- **Kubernetes**: Kustomize overlays + Helm Chart

#### 3.1.3 CI/CD 配置 (`ci/`)

- **GitHub Actions**: CI/CD 流水线配置
- **GitLab CI**: GitLab CI 配置
- **Jenkins**: Jenkinsfile 流水线定义
- **共享工具**: 构建、lint、测试脚本

#### 3.1.4 测试 (`test/`)

- **API 测试**: HTTP 文件测试 (REST Client / Hurl)
- **集成测试**: 数据库 CRUD、缓存、迁移测试
- **性能测试**: k6、Locust 负载测试
- **测试数据**: Mock 数据和 Fixtures

#### 3.1.5 数据处理 (`data/`)

- **ETL**: API 同步、CSV 导入
- **数据清洗**: 用户数据清洗、去重
- **数据转移**: 表导出、跨库迁移

#### 3.1.6 消息队列 (`mq/`)

- **RabbitMQ**: 队列管理、死信检查、监控
- **Kafka**: Topic 管理、消费者组、生产测试
- **Redis Streams**: Stream 管理、延迟监控

#### 3.1.7 存储 (`storage/`)

- **S3**: Bucket 同步、预签名 URL、过期清理
- **MinIO**: 健康检查、Bucket 初始化、S3 迁移
- **文件工具**: 图片压缩、格式转换、去重、文本提取

#### 3.1.8 浏览器自动化 (`browser/`)

- Playwright 自动化示例
- Edge 浏览器调试模式启动

#### 3.1.9 定时任务 (`cron/`)

- Crontab / Systemd Timer 配置
- Celery Beat 调度配置
- 定时任务脚本 (日志清理、备份、健康检查)

#### 3.1.10 运维工具 (`ops/`)

- 连接检查
- 数据库诊断
- Token 生成
- 缓存重置

### 3.2 任务系统

#### 3.2.1 Taskfile 层次结构

```
task <domain>:<sub-domain>:<action>
```

- 根 Taskfile 通过 includes 聚合所有子模块
- 每个子模块再聚合其下级
- 支持别名系统简化命令

#### 3.2.2 just 命令 (根目录快捷操作)

- `just format` - 格式化代码
- `just fetch/pull/push` - Git 操作
- `just symlink-project` - 创建软链接

## 4. 非功能需求

### 4.1 代码规范

| 语言   | 规范                                                  |
| ------ | ----------------------------------------------------- |
| Python | PEP 723 内联依赖 + `uv run` + loguru 日志 + typer CLI |
| Shell  | `set -euo pipefail` + 内联函数                        |
| SQL    | `001_description.sql` + `rollback_001.sql` 命名       |
| YAML   | 使用 `yq -i "." file.yml` 格式化                      |

### 4.2 目录结构规范

- **职责域切分**: 顶层目录按业务职责分，不按文件类型
- **深度克制**: 不超过 4 层
- **叶子即执行**: 最底层目录包含完整上下文
- **脚本自包含**: 拷走就能跑

### 4.3 安全要求

- 所有敏感配置通过环境变量注入
- 永远不提交 `.env` 文件或密钥
- `.gitignore` 排除敏感文件

### 4.4 文档要求

- `README.md` - 项目说明和快速开始
- `AGENTS.md` - AI 助手指南
- `docs/architecture.md` - 架构说明
- `docs/runbook.md` - 操作手册
- `docs/adr/` - 架构决策记录

## 5. 技术栈

### 5.1 工具链

| 工具                                        | 用途                    |
| ------------------------------------------- | ----------------------- |
| [Task](https://taskfile.dev/)               | 任务运行器              |
| [just](https://github.com/casey/just)       | 另一个任务运行器        |
| [uv](https://github.com/astral-sh/uv)       | Python 包管理和脚本运行 |
| [fzf](https://github.com/junegunn/fzf)      | 交互式选择工具          |
| [gum](https://github.com/charmbracelet/gum) | Shell 脚本美化          |
| [Nushell](https://www.nushell.sh/)          | 现代化 Shell            |
| [yq](https://github.com/mikefarah/yq)       | YAML 处理               |
| [ruff](https://github.com/astral-sh/ruff)   | Python linter           |
| [prettier](https://prettier.io/)            | 代码格式化              |
| [shfmt](https://github.com/mvdan/sh)        | Shell 格式化            |
| [shellcheck](https://www.shellcheck.net/)   | Shell 静态分析          |

### 5.2 Python 依赖模式

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.0", "python-dotenv>=1.0"]
# ///
```

### 5.3 Shell 脚本模式

```bash
#!/usr/bin/env bash
set -euo pipefail

# 内联工具函数
log_info() { echo "[INFO] $*"; }
```

## 6. 环境配置

### 6.1 前置要求

- Python 3.11+
- Bash 5.0+
- Task 运行器
- Git

### 6.2 环境变量

参考 `.env.example` 配置:

- `MYSQL_*` - MySQL 连接配置
- `POSTGRES_*` - PostgreSQL 连接配置
- `REDIS_*` - Redis 连接配置
- `ES_*` - Elasticsearch 连接配置
- `S3_*` - S3/MinIO 存储配置
- `KAFKA_*` - Kafka 连接配置
- `RABBITMQ_*` - RabbitMQ 连接配置
- `DEBUG` - 调试模式开关

## 7. 项目结构

```
project-scripts/
├── browser/             # 浏览器自动化
├── ci/                  # CI/CD 配置
├── config/              # 应用配置
├── cron/                # 定时任务
├── data/                # 数据处理
├── db/                  # 数据库管理
├── deploy/              # 部署编排
├── docs/                # 文档
├── examples/            # 代码样例
├── mq/                  # 消息队列
├── ops/                 # 运维工具
├── scripts/             # 通用脚本
├── storage/             # 存储管理
├── test/                # 测试
├── .env.example         # 环境变量模板
├── .gitignore
├── AGENTS.md            # AI 助手指南
├── Taskfile.yml         # 根任务配置
├── justfile             # just 任务配置
├── symlink_project.nu   # 软链接脚本
├── task_choose.nu       # 任务选择脚本
└── README.md            # 项目说明
```

## 8. 任务示例

```bash
# 数据库操作
task db:mysql
task db:elasticsearch

# 部署
task deploy:k8s:helm:myapp
task deploy:compose

# 测试
task test:api
task test:load

# 数据处理
task data:etl
task data:clean

# 存储
task storage:s3
task storage:minio
```

## 9. 里程碑

| 阶段 | 内容                       | 状态      |
| ---- | -------------------------- | --------- |
| v0.1 | 项目结构搭建，核心模块实现 | ✅ 完成   |
| v0.2 | 文档完善，examples 补充    | 🔄 进行中 |
| v0.3 | ops/ 模块实现              | ⏳ 待开始 |
| v1.0 | 稳定版本发布               | ⏳ 待规划 |

## 10. 附录

### 10.1 相关文档

- [README.md](../README.md) - 项目说明
- [AGENTS.md](../AGENTS.md) - AI 助手指南
- [architecture.md](./architecture.md) - 架构说明
- [runbook.md](./runbook.md) - 操作手册

### 10.2 许可证

MIT License
