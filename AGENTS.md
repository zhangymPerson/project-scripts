# AGENTS.md

## 项目概览
这是一个**按职责域组织的通用项目支撑脚本仓库**，为全栈项目提供数据库管理、测试、部署、CI/CD、数据处理、运维工具等基础设施支持。

## 关键架构信息

### 目录结构（按职责域划分）
- `browser/` - 浏览器自动化/E2E测试 - `task browser`
- `db/` - 数据库层（mysql/postgresql/mongodb/redis/sqlite） - `task db:mysql|postgresql|mongodb|redis|sqlite`
- `storage/` - 对象存储/文件处理（s3/minio） - `task storage:s3|minio|file-tools`
- `mq/` - 消息队列（rabbitmq/kafka/redis-streams） - `task mq:rabbitmq|kafka|redis-streams`
- `test/` - 测试层（api/integration/load） - `task test:api|integration|load`
- `data/` - ETL/数据清洗 - `task data:etl|clean|transfer`
- `deploy/` - 部署编排（docker-compose/k8s/helm） - `task deploy:k8s:helm:myapp|deploy:compose`
- `cron/` - 定时任务
- `ops/` - 运维诊断工具 - `task ops:default`
- `ci/` - CI/CD配置

### 每个目录都是独立的可执行单元
- 最底层目录包含完整上下文（脚本+配置+数据）
- 所有脚本必须自包含（可直接拷走运行）
- Python脚本使用PEP 723内联依赖（`# /// script` + `uv run`）
- Shell脚本必须自包含（不source外部文件）

## 重要工具链

### Task 任务系统
- 使用 `Taskfile.yml` 在每个目录定义任务
- 别名系统：主任务名是主键（如 `mysql` 别名对应 `db:mysql`）
- 常用命令：
  - `task --list` - 查看所有任务
  - `task <name>` - 运行任务
  - `task mysql` = `task db:mysql` = 别名机制
  - `task --list | grep "db:"` - 按前缀过滤

### just 命令（项目根目录）
- `just` - 格式化justfile并列出任务
- `just run` - 通过fzf交互选择任务
- `just clear` - 清理日志/缓存
- `just format` - 格式化代码+ruff检查

### 脚本运行方式
- **Python**: `uv run <script>`（自动处理PEP 723依赖）
- **Shell**: `bash <script.sh>`（确保脚本有 `set -euo pipefail`）
- **HTTP测试**: `.http` 文件用VS Code REST Client插件
- **性能测试**: Hurl测试 `.hurl` 文件

## 常见工作流

### 运行测试
```bash
# API测试
cd test/api && pytest -v

# 集成测试
cd test/integration && pytest -v

# 性能测试
cd test/load && locust --headless -u 100 -r 10 --run-time 60s

# 视觉回归
uv run test/visual/capture.py
uv run test/visual/compare.py
```

### 数据库操作
```bash
# MySQL
task db:mysql
uv run db/mysql/example_mysql.py connect

# PostgreSQL
task db:postgresql

# MongoDB
task db:mongodb

# Redis
task db:redis

# SQLite
task db:sqlite
```

### 部署流程
```bash
# 开发环境
task deploy:compose  # 或 kubectl apply -k deploy/k8s/overlays/dev

# 生产环境
task deploy:k8s:helm:myapp
```

## 代码规范
- Python: PEP 723 内联依赖 + loguru 日志 + typer CLI
- Shell: `set -euo pipefail` + 内联函数
- SQL迁移: `001_description.sql` + `rollback_001.sql`
- 目录深度不超过4层
- YAML格式化: `yq -i "." file.yml`

## 环境与配置
- `.env.example` - 环境变量模板（实际.env被gitignore）
- 数据库配置: `MYSQL_*`/`POSTGRES_*` 环境变量
- 调试模式: `DEBUG=true`
- 所有敏感配置通过环境变量注入

## 避坑指南
- 脚本拷走后必须能独立运行（自包含原则）
- 不要手动创建目录，按职责域原则创建
- 任务层次由Taskfile.yml自动发现
- 配置文件用yq格式化，不要手动编辑
- 永远不要提交.env文件或密钥