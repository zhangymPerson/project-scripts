use std/log

def main [] {

    # let extracted_task = (task --list --json | from json | get tasks | get task | to text | fzf)
    let extracted_task = (task --list --json | jq -r '.tasks[] | "\(.task)\t\(.desc)"' | fzf | split row "\t" | first)

    log info $"要执行的任务是: ($extracted_task)"

    # 运行选中的任务
    task $extracted_task
}