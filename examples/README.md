# 代码样例目录

本目录存放项目中各类代码的最佳实践示例，供开发者参考和复用。

## 目录结构

```
examples/
├── python/              # Python 脚本示例
│   └── example.py       # 基础 Python 脚本模板
│
├── shell/               # Shell 脚本示例
│   └── example.sh       # 基础 Shell 脚本模板
│
├── sql/                 # SQL 迁移文件示例
│   ├── migration_create_table.sql    # 创建表迁移示例
│   ├── migration_add_column.sql      # 添加列迁移示例
│   └── rollback.sql                  # 回滚脚本示例
│
└── http/                # HTTP 请求文件示例
    ├── apifox-echo.openapi.yaml      # Apifox Echo API OpenAPI 规范
    ├── rest-client/                  # VS Code REST Client 示例
    │   └── rest_client_example.http
    └── hurl/                         # Hurl HTTP 测试工具示例
        ├── README.md                 # Hurl 使用笔记
        ├── sample_requests.hurl      # 完整请求示例
        └── hurl_test_example.hurl    # 测试用例示例
```

## 各目录说明

### python/

Python 脚本示例，包含标准的项目结构、日志配置、命令行参数解析等最佳实践。

### shell/

Shell 脚本示例，包含错误处理、参数校验、日志输出等最佳实践。

### sql/

数据库迁移文件示例，遵循可逆迁移原则：

- 迁移文件命名：`migration_<描述>.sql`
- 每个迁移应有对应的回滚脚本

### http/

HTTP 请求测试文件示例：

| 工具        | 说明                                                 |
| ----------- | ---------------------------------------------------- |
| REST Client | VS Code 插件，`.http` 文件格式，适合快速测试 API     |
| Hurl        | 命令行 HTTP 测试工具，支持断言和变量捕获，适合 CI/CD |

详细使用方法参见 `http/hurl/README.md`。

## 使用方式

每个样例文件都包含详细的注释，说明：

- 适用场景
- 关键设计决策
- 使用注意事项

可以直接复制样例代码到实际项目中，然后根据需求修改。
