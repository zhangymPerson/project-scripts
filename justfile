set unstable := true

# 默认任务：使用 fzf 选择要执行的任务
default:
    just $(just --list | gum filter --no-limit | awk '{print $1}')

# =============================================================================
# 别名
# =============================================================================
# 示例命令别名

alias ep := example-python
alias eph := example-python-hello
alias epi := example-python-info
alias es := example-shell
alias esd := example-shell-debug
alias ex := examples

# 清理命令别名

alias c := clear

# 数据库命令别名

alias dm := db-migrate
alias ds := db-seed
alias db := db-backup
alias doc := docs

# 测试命令别名

alias ta := test-api
alias th := test-http
alias ehh := example-http-hurl
alias ti := test-integration
alias tl := test-load

# 部署命令别名

alias dd := deploy-dev
alias dst := deploy-staging
alias dp := deploy-prod
alias k := k8s-apply

# 运维命令别名

alias od := ops-diagnose
alias ot := ops-token

# =============================================================================
# 示例命令
# =============================================================================

# 运行 examples/python/example.py 脚本的帮助命令
example-python:
    @uv run examples/python/example.py --help

# 运行 examples/python/example.py 的 hello 子命令
example-python-hello:
    @uv run examples/python/example.py hello --name World

# 运行 examples/python/example.py 的 info 子命令
example-python-info:
    @uv run examples/python/example.py info

# 运行 examples/shell/example.sh 脚本
example-shell:
    @bash examples/shell/example.sh

# 以调试模式运行 examples/shell/example.sh 脚本
example-shell-debug:
    @DEBUG=true bash examples/shell/example.sh

# =============================================================================
# 清理命令
# =============================================================================

# 清理项目中的日志文件和临时目录
clear:
    # 清理所有 logs 目录
    @echo "🧹 清理 logs 目录..."
    @find . -type d -name "logs" -exec rm -rf {} + 2>/dev/null || true

    # 清理所有 .log 文件
    @echo "🧹 清理 .log 文件..."
    @find . -type f -name "*.log" -delete 2>/dev/null || true

    # 清理所有 .log.tar.gz 文件
    @echo "🧹 清理 .log.tar.gz 文件..."
    @find . -type f -name "*.log.tar.gz" -delete 2>/dev/null || true

    # 清理测试产生的临时目录
    @echo "🧹 清理测试临时目录..."
    @rm -rf test-results playwright-report 2>/dev/null || true

    @echo "✅ 清理完成！"

# =============================================================================
# 数据库相关
# =============================================================================

# 运行 db/mysql/migrate.sh 数据库迁移脚本
db-migrate:
    @echo "运行数据库迁移..."
    @uv run db/mysql/migrate.sh

# 运行 db/mysql/seed.sh 加载种子数据
db-seed:
    @echo "加载种子数据..."
    @uv run db/mysql/seed.sh

# 运行 db/mysql/backup.sh 备份数据库
db-backup:
    @echo "备份数据库..."
    @uv run db/mysql/backup.sh

# =============================================================================
# 测试相关
# =============================================================================

# 运行 test/api 目录下的 API 测试
test-api:
    @echo "运行 API 测试..."
    @cd test/api && pytest -v

# 查看 test/api/http 目录下的 HTTP 测试文件
test-http:
    @echo "查看 HTTP 测试文件..."
    @ls -la test/api/http/

# 运行 examples/http/hurl_test_example.hurl 的 Hurl 测试
example-http-hurl:
    @echo "运行 Hurl 测试..."
    @source examples/http/hurl/hurl.env && hurl -v examples/http/hurl/hurl_test_example.hurl
    @hurl --variable baseUrl=https://jsonplaceholder.typicode.com --variable token="Bearer your-token" examples/http/hurl/sample_requests.hurl

# 运行 test/integration 目录下的集成测试
test-integration:
    @echo "运行集成测试..."
    @cd test/integration && pytest -v

# 运行 test/load 目录下的性能/负载测试
test-load:
    @echo "运行性能测试..."
    @cd test/load && locust --headless -u 100 -r 10 --run-time 60s

# =============================================================================
# 部署相关
# =============================================================================

# 使用 deploy/compose/docker-compose.dev.yml 部署到开发环境
deploy-dev:
    @echo "部署到开发环境..."
    @docker-compose -f deploy/compose/docker-compose.dev.yml up -d

# 使用 deploy/compose/docker-compose.staging.yml 部署到预发布环境
deploy-staging:
    @echo "部署到预发布环境..."
    @docker-compose -f deploy/compose/docker-compose.staging.yml up -d

# 使用 deploy/compose/docker-compose.prod.yml 部署到生产环境
deploy-prod:
    @echo "部署到生产环境..."
    @docker-compose -f deploy/compose/docker-compose.prod.yml up -d

# 应用 deploy/k8s/overlays/dev 目录下的 K8s 配置
k8s-apply:
    @echo "应用 K8s 配置..."
    @kubectl apply -k deploy/k8s/overlays/dev

# =============================================================================
# 运维工具
# =============================================================================

# 运行 ops/diagnose_db.py 进行数据库诊断
ops-diagnose:
    @echo "运行数据库诊断..."
    @uv run ops/diagnose_db.py

# 运行 ops/generate_token.py 生成 Token
ops-token:
    @echo "生成 Token..."
    @uv run ops/generate_token.py

# =============================================================================
# 文档
# =============================================================================

# 查看 docs 目录下的文档
docs:
    @echo "查看文档..."
    @ls -la docs/

# 查看 examples 目录下的示例代码
examples:
    @echo "查看示例代码..."
    @ls -la examples/
