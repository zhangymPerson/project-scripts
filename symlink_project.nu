use std/log

def main [] {
    # 1. 判断 ~/.project 目录是否存在，不存在则新建
    let project_dir = $"($nu.home-dir)/.project"

    if not ($project_dir | path exists) {
        log info $"创建项目目录: ($project_dir)"
        mkdir $project_dir
    } else {
        log info $"项目目录已存在: ($project_dir)"
    }

    # 2. 获取当前脚本所在目录并打印
    let script_dir = ($env.FILE_PWD | default ($env.CURRENT_FILE | path dirname))
    log info $"当前脚本所在目录: ($script_dir)"

    # 3. 判断当前操作系统类型
    let os_type = $nu.os-info.name
    log info $"当前操作系统: ($os_type)"

    let link_name = $"($project_dir)/($script_dir | path basename)"

    # 4. 判断软连接目标是否存在，不存在则创建
    if ($link_name | path exists) {
        log warning $"软连接已存在，跳过: ($link_name)"
    } else {
        log info $"创建软连接: ($link_name) -> ($script_dir)"
        if ($os_type == "mac") or ($os_type == "macos") or ($os_type == "linux") or ($os_type == "darwin") {
            ^ln -s $script_dir $link_name
        } else if $os_type == "windows" {
            ^cmd /c mklink /D $link_name $script_dir
        } else {
            ^ln -s $script_dir $link_name
        }
        log info $"软连接创建成功: ($link_name)"
    }
}
