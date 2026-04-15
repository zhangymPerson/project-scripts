# https://just.systems

set unstable := true
set shell := ["nu", "-c"]

# 默认任务 - 显示所有可用任务列表

alias l := default

default:
    just --fmt
    just --list

# 动态选择任务运行

alias r := run

run:
    @just --choose

alias tr := task_run

# 运行task任务
task_run:
    @nu {{ justfile_directory() }}/task_choose.nu

alias tl := task_list

# 任务列表
task_list:
    task --list-all | fzf

alias d := dir

# 查看当前目录
dir:
    echo {{ justfile_directory() }}

# format
format:
    just --fmt
    @echo "🔍 检查 Python 文件格式..."
    @uvx ruff check --fix .
    nu -c 'echo "shell 格式化"'
    nu -c 'ls ...(glob **/*.{sh}) | get name | each { |f| shfmt -i 2 -w $f ; echo $"($f) format success" }'
    nu -c 'echo "shell 文件检查"'
    nu -c 'ls ...(glob **/*.{sh}) | get name | shellcheck ...$in'
    nu -c 'echo "yaml 格式化"'
    nu -c 'ls ...(glob **/*.{yaml,yml}) | get name | each { |f| yq -i "." $f ; echo $"($f) format success" }'
    nu -c 'echo "遍历所有 justfile 并执行 just -f"'
    nu -c 'ls ...(glob **/justfile) | get name | each { |f| just -f $f ; echo $"($f) just executed" }'

# 清理项目中的日志文件和临时目录
clear:
    # 清理所有 logs 目录
    @echo "🧹 清理 logs 目录..."
    @nu -c 'try { fd --type d "logs" | xargs rm -rf 2>/dev/null } catch { }'
    # 清理所有 .log 文件
    @echo "🧹 清理 .log 文件..."
    @nu -c 'try { fd --type f --glob "*.log" | xargs rm -f 2>/dev/null } catch { }'
    # 清理所有 .log.tar.gz 文件
    @echo "🧹 清理 .log.tar.gz 文件..."
    @nu -c 'try { fd --type f --glob "*.log.tar.gz" | xargs rm -f 2>/dev/null } catch { }'
    # 清理测试产生的临时目录
    @echo "🧹 清理测试临时目录..."
    @nu -c 'try { rm -rf test-results playwright-report 2>/dev/null } catch { }'
    # 清理 Python 缓存目录
    @echo "🧹 清理 Python 缓存..."
    @nu -c 'try { fd --type d "__pycache__" | xargs rm -rf 2>/dev/null } catch { }'
    @nu -c 'try { fd --type f --glob "*.pyc" | xargs rm -f 2>/dev/null } catch { }'
    @nu -c 'try { fd --type f --glob "*.pyo" | xargs rm -f 2>/dev/null } catch { }'
    @nu -c 'try { fd --type f --glob "*.pyd" | xargs rm -f 2>/dev/null } catch { }'
    # 清理测试和工具缓存
    @echo "🧹 清理测试工具缓存..."
    @nu -c 'try { rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache 2>/dev/null } catch { }'
    # 清理系统临时文件
    @echo "🧹 清理系统临时文件..."
    @nu -c 'try { fd --type f --hidden --glob ".DS_Store" | xargs rm -f 2>/dev/null } catch { }'
    @nu -c 'try { fd --type f --glob "Thumbs.db" | xargs rm -f 2>/dev/null } catch { }'
    @echo "✅ 清理完成！"

# git fetch
fetch:
    git fetch --all --tags --prune --jobs=10

# git pull 全部仓库代码
pull:
    git pull --rebase

# git push 推送到 origin gitcode gitee main 仓库
push:
    git push origin main
    git push gitcode main
    git push gitee main

# 创建 tmux 窗口
tmux:
    #!/usr/bin/env sh
    TMUX_SESSION_NAME=ps
    echo "检查并启动 tmux 会话[${TMUX_SESSION_NAME}]..."
    # 检查是否已经处于 tmux 会话中
    if [ -n "$TMUX" ]; then
        echo "已在 tmux 会话中，直接连接到 ${TMUX_SESSION_NAME} 会话..."
        tmux switch-client -t ${TMUX_SESSION_NAME} 2>/dev/null || tmux new-session -d -s ${TMUX_SESSION_NAME} && tmux switch-client -t ${TMUX_SESSION_NAME}
    else
        # 检查 ${TMUX_SESSION_NAME} 会话是否存在
        if ! tmux has-session -t ${TMUX_SESSION_NAME} 2>/dev/null; then
            echo "创建新的 tmux 会话 ${TMUX_SESSION_NAME}..."
            tmux new-session -d -s ${TMUX_SESSION_NAME}
        else
            echo "tmux 会话 ${TMUX_SESSION_NAME} 已存在"
        fi
        echo "连接到 tmux 会话 ${TMUX_SESSION_NAME}..."
        tmux attach -t ${TMUX_SESSION_NAME}
    fi
