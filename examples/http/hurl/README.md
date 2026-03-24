# Hurl 使用笔记

> 基于 https://hurl.dev/docs 整理 | Hurl 7.1.0

---

## 1. 简介

Hurl 是一个用纯文本格式定义 HTTP 请求的命令行工具。它可以：

- 链式发送多个请求，共享 cookie 会话
- 从响应中提取值（Capture），用于后续请求
- 对响应做断言（Assert），充当 API 测试工具
- 支持 REST / SOAP / GraphQL / JSON / XML / HTML 等任意 HTTP 接口

安装方式：`brew install hurl` / `cargo install hurl` / 各平台包管理器 / GitHub Releases

---

## 2. 文件格式基础

| 规范项       | 要求                                                                   |
| ------------ | ---------------------------------------------------------------------- |
| 字符编码     | 必须为 UTF-8（BOM 可选，Hurl 会忽略 BOM 不报错）                       |
| 文件扩展名   | 官方标准为 `.hurl`                                                     |
| 注释         | 以 `#` 开头，单行生效；可在行尾/独立行使用，支持富文本注释（作为文档） |
| 多个接口分割 | 以 `###` 为接口分割符号                                                |
| 特殊字符处理 | 字符串中特殊字符（\n/\t/"/'/\\）直接书写即可，多行字符串用 ``` 包裹    |

### Entry（入口）

一个 `.hurl` 文件由多个 **Entry** 组成，每个 Entry = 一个 **Request** + 可选的 **Response**：

```hurl
# Entry 1: 带断言
GET https://example.org
HTTP 200
[Asserts]
xpath "//title" == "Hello"

# Entry 2: 纯请求，不需要响应描述
POST https://example.org/api/data
{"key": "value"}
```

---

## 3. Request 详解

### 3.1 基本结构

```
# 固定顺序（必须按此顺序）
METHOD URL → HTTP请求头 → [可选区块（无序）] → 请求体（可选，最后一位）
```

### 3.2 方法 & URL

- **Method**：支持所有 HTTP 标准方法（GET/POST/PUT/DELETE/PATCH 等），必须大写；
- **URL**：支持绝对 URL（推荐），支持变量引用（`{{变量名}}`）；

```hurl
GET https://example.org/api/users?page=1
POST https://example.org/api/users
PUT https://example.org/api/users/42
DELETE https://example.org/api/users/42
PATCH https://example.org/api/users/42
```

### 3.3 Headers

紧跟 URL 之后，格式与 HTTP 头一致：

```hurl
GET https://example.org/api
User-Agent: MyAgent/1.0
Accept: application/json
Authorization: Bearer {{token}}
```

### 3.4 可选区块

以下区块无固定顺序，按需添加，格式为 `[区块名]` 开头 + 键值对：

| 区块名 | 用途 | 示例 |
|--------|------|------|
| [QueryStringParams] | 定义 URL 查询参数（替代 URL 中 `?key=value`，更易维护） | `[QueryStringParams]`<br>`id: 123`<br>`order: newest` |
| [FormParams] | 表单参数（Content-Type 自动为 application/x-www-form-urlencoded） | `[FormParams]`<br>`username: test`<br>`password: 123456` |
| [Multipart] | 文件上传 | `[Multipart]`<br>`field1: value1`<br>`avatar: file,photo.png;` |
| [Cookies] | 请求携带的 Cookie | `[Cookies]`<br>`session_id: abc123` |
| [BasicAuth] | HTTP Basic 认证（等价于 curl -u 用户名:密码） | `[BasicAuth]`<br>`alice: secret` |
| [Options] | 请求级配置（覆盖全局 CLI，如超时/重试/输出） | `[Options]`<br>`retry: 3`<br>`timeout: 10000ms` |

**Query Parameters 示例：**

```hurl
GET https://example.org/search
[QueryStringParams]
q: hello world
page: 1
limit: 20
```

**Form Parameters 示例：**

```hurl
POST https://example.org/login
[FormParams]
username: alice
password: secret123
```

**Multipart Form Data 示例：**

```hurl
POST https://example.org/upload
[Multipart]
field1: value1
avatar: file,photo.png;
document: file,report.pdf; application/pdf
```

> 文件路径相对于 `.hurl` 文件所在目录。

**Cookies 示例：**

```hurl
GET https://example.org
[Cookies]
session: abc123
theme: dark
```

**BasicAuth 示例：**

```hurl
GET https://example.org/protected
[BasicAuth]
bob: secret
```

**Options 示例：**

```hurl
GET https://example.org/api
[Options]
location: true          # 跟随重定向
insecure: true          # 跳过 SSL 验证
max-time: 30s           # 超时时间
retry: 3                # 重试次数
retry-interval: 1s      # 重试间隔
verbose: true           # 详细输出
delay: 2s               # 请求前延迟
skip: false             # 跳过此请求
repeat: 5               # 重复执行次数
variable: env=prod      # 定义变量（对后续请求也生效）
output: response.json   # 响应输出到文件
compressed: true        # 请求压缩响应
proxy: 127.0.0.1:8080   # 代理
```

### 3.5 Body 类型

请求体必须是 Request 最后一部分，支持多格式：

| 类型 | 语法 | 说明 |
|------|------|------|
| JSON | 直接写 JSON | 自动设 `Content-Type: application/json` |
| XML | 直接写 XML | 需手动设 `Content-Type` |
| GraphQL | ` ```graphql ... ``` ` | 支持 GraphQL variables |
| 多行文本 | ` ``` ... ``` ` | 通用文本 body |
| 单行文本 | `` `text` `` | 不含换行的文本 |
| Base64 | `base64,...;` | 二进制数据 |
| Hex | `hex,...;` | 二进制数据 |
| 文件 | `file,data.bin;` | 文件内容作为 body |

**JSON body 示例（支持模板变量）：**

```hurl
POST https://example.org/api/users
Content-Type: application/json
{
  "name": "{{username}}",
  "age": {{age}},
  "active": true
}
```

**GraphQL 示例：**

```hurl
POST https://example.org/graphql
{
  human(id: "1000") {
    name
    height(unit: FOOT)
  }
}
```

---

## 4. Response 详解

Response 是可选的。如果写了，用于断言和捕获值。结构如下：

```
HTTP 状态码 → 响应头断言 → [Captures] → [Asserts]
```

### 4.1 隐式断言

**版本 + 状态码：**

```hurl
GET https://example.org
HTTP 200              # 精确匹配状态码
HTTP/2 200            # 同时检查 HTTP 版本
HTTP *                # 通配，不检查版本和状态码
```

**Headers（隐式精确匹配）：**

```hurl
POST https://example.org/login
[FormParams]
user: alice
password: 123
HTTP 302
Location: https://example.org/home
```

### 4.2 Body 隐式断言

直接把期望的 body 写在 response 区域：

```hurl
GET https://example.org/api/user/1
HTTP 200
{
  "id": 1,
  "name": "Alice"
}
```

---

## 5. Captures（值提取）

从响应中提取值，供后续请求使用。定义在 `[Captures]` 段。

### 5.1 常用 Capture Query

```hurl
GET https://example.org
HTTP 200
[Captures]
status_code: status                           # 状态码
http_ver: version                             # HTTP 版本
location: header "Location"                   # 响应头
sid: cookie "SESSION"                         # Cookie 值
body_text: body                               # 整个 body（文本）
raw_bytes: bytes                              # 整个 body（原始字节）
title: xpath "string(//title)"               # XPath 提取
user_id: jsonpath "$.user.id"                # JSONPath 提取
token: regex "token:([a-z]+)"               # 正则提取
hash: sha256                                  # body 的 SHA-256
final_url: url                                # 最终 URL（跟随重定向后）
resp_time: duration                           # 响应时间(ms)
ip_addr: ip                                   # 服务器 IP
cert_sub: certificate "Subject"               # SSL 证书属性
```

### 5.2 Cookie 属性捕获

```hurl
[Captures]
val: cookie "SID"
expires: cookie "SID[Expires]"
domain: cookie "SID[Domain]"
path: cookie "SID[Path]"
secure: cookie "SID[Secure]"
http_only: cookie "SID[HttpOnly]"
```

### 5.3 重定向链捕获

```hurl
GET https://example.org/r
[Options]
location: true
HTTP 200
[Captures]
step1: redirects nth 0 location
step2: redirects nth 1 location
final: url
```

### 5.4 Secret（脱敏捕获）

```hurl
[Captures]
password: header "X-Token" redact   # 在日志和报告中脱敏
```

CLI 方式：`hurl --secret token=xxx file.hurl`

---

## 6. Asserts（断言）

### 6.1 谓词函数

| 谓词 | 说明 | 示例 |
|------|------|------|
| `==` | 等于 | `jsonpath "$.name" == "Alice"` |
| `!=` | 不等于 | `jsonpath "$.status" != "error"` |
| `>` `>=` `<` `<=` | 数值/日期比较 | `jsonpath "$.year" > 2020` |
| `startsWith` | 开头匹配 | `jsonpath "$.title" startsWith "Hello"` |
| `endsWith` | 结尾匹配 | `jsonpath "$.file" endsWith ".pdf"` |
| `contains` | 包含 | `body contains "welcome"` |
| `matches` | 正则匹配 | `jsonpath "$.phone" matches /\d{11}/` |
| `exists` | 存在 | `jsonpath "$.email" exists` |
| `not exists` | 不存在 | `jsonpath "$.deleted" not exists` |
| `isString` | 类型检查 - 字符串 | `jsonpath "$.name" isString` |
| `isInteger` | 类型检查 - 整数 | `jsonpath "$.count" isInteger` |
| `isFloat` | 类型检查 - 浮点数 | `jsonpath "$.price" isFloat` |
| `isBoolean` | 类型检查 - 布尔值 | `jsonpath "$.active" isBoolean` |
| `isNumber` | 类型检查 - 数字 | `jsonpath "$.total" isNumber` |
| `isList` | 类型检查 - 数组 | `jsonpath "$.data" isList` |
| `isObject` | 类型检查 - 对象 | `jsonpath "$.meta" isObject` |
| `isEmpty` | 空集合 | `jsonpath "$.items" isEmpty` |
| `isIsoDate` | ISO 日期 | `jsonpath "$.created" isIsoDate` |
| `isUuid` | UUID v4 | `jsonpath "$.id" isUuid` |
| `isIpv4` / `isIpv6` | IP 地址 | `ip isIpv4` |

所有谓词都可以加 `not` 前缀取反。

### 6.2 常用断言示例

```hurl
GET https://example.org/api/users
HTTP 200
[Asserts]
# 状态码
status == 200
status < 300

# Headers
header "Content-Type" contains "application/json"
header "X-Request-Id" exists

# JSON body
jsonpath "$.users" count == 10
jsonpath "$.users[0].name" == "Alice"
jsonpath "$.users[*].role" contains "admin"

# Cookie
cookie "session" exists
cookie "session[HttpOnly]" exists
cookie "session[Secure]" exists

# 响应时间
duration < 2000

# body 文本
body contains "success"

# bytes 长度
bytes count > 100

# 类型检查
jsonpath "$.data" isList
jsonpath "$.total" isInteger
```

### 6.3 XPath 断言（HTML/XML）

```hurl
GET https://example.org
HTTP 200
[Asserts]
xpath "//h1" exists
xpath "normalize-space(//title)" == "Home Page"
xpath "//li" count == 5
xpath "string(//article/@data-id)" startsWith "post"
```

---

## 7. Filters（过滤器）

Filters 可以链式使用，对 query 结果做变换：

```hurl
GET https://example.org/api
HTTP 200
[Asserts]
# 拆分 header 值并检查
header "X-Servers" split "," count == 2
header "X-Servers" split "," nth 0 == "rec1"

# 数组操作
jsonpath "$.books" first == "Dune"
jsonpath "$.books" last == "1984"
jsonpath "$.books" nth 2 == "Foundation"
jsonpath "$.books" count == 12

# 字符串操作
jsonpath "$.name" replace "Mr." "Dr." == "Dr. Smith"
jsonpath "$.id" replaceRegex /\d/ "x" == "xxx"
jsonpath "$.csv" split "," first == "hello"

# 类型转换
jsonpath "$.price" toFloat == 19.99
jsonpath "$.count" toInt == 42
jsonpath "$.pi" toString == "3.14"

# 编码/解码
jsonpath "$.token" base64Decode utf8Decode == "hello"
bytes base64Encode == "SGVsbG8="
jsonpath "$.url" urlDecode == "https://example.org/?q=hello world"

# 日期操作
header "Expires" toDate "%a, %d %b %Y %H:%M:%S GMT" daysBeforeNow > 1000
certificate "Expire-Date" daysAfterNow > 30
jsonpath "$.published" toDate "%+" dateFormat "%A" == "Monday"

# 其他
jsonpath "$.url" urlQueryParam "page" == "1"
bytes toHex == "48656c6c6f"
bytes decode "gb2312"    # 指定编码解码
```

---

## 8. Templates（模板/变量）

### 8.1 使用变量

用 `{{variable_name}}` 插值：

```hurl
GET https://{{host}}/api/users/{{user_id}}
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.id" == {{user_id}}
jsonpath "$.name" == "{{expected_name}}"
```

> 加引号 `"{{var}}"` → 字符串比较；不加 `{{var}}` → 保留原始类型。

### 8.2 内置函数

```hurl
POST https://example.org/api
{
  "id": "{{newUuid}}",
  "created": "{{newDate}}"
}
```

- `newUuid` — 生成 UUID v4
- `newDate` — 生成当前 UTC 时间 (RFC 3339)

### 8.3 注入变量的方式

**重要：Hurl 不支持在文件内直接定义变量，必须通过外部方式注入。**

| 方式 | 示例 |
|------|------|
| CLI `--variable` | `hurl --variable host=api.example.com --variable id=42 test.hurl` |
| CLI `--variables-file` | `hurl --variables-file vars.env test.hurl` |
| 环境变量 | `HURL_VARIABLE_host=api.example.com hurl test.hurl` |
| `[Options]` 段 | `variable: host=api.example.com` |

`vars.env` 文件格式：

```
host=api.example.com
id=42
token=abc123
```

---

## 9. Entry 控制流

```hurl
# 延迟执行
GET https://example.org
[Options]
delay: 3s
HTTP 200

# 重复执行
GET https://example.org/loop
[Options]
repeat: 5
HTTP 200

# 跳过
GET https://example.org/skip-me
[Options]
skip: true
HTTP 200

# 重试（轮询场景）
GET https://example.org/job/{{job_id}}
[Options]
retry: 10
retry-interval: 500ms
HTTP 200
[Asserts]
jsonpath "$.status" == "COMPLETED"
```

---

## 10. CLI 常用选项

```bash
# 基本用法
hurl file.hurl                         # 执行，输出最后响应 body
hurl file.hurl -o output.json          # 输出到文件
echo 'GET https://httpbin.org/get' | hurl  # stdin 输入

# 测试模式
hurl --test *.hurl                     # 测试模式，输出测试报告
hurl --test --jobs 1 *.hurl            # 串行执行
hurl --test --parallel *.hurl          # 并行执行（默认）

# 调试
hurl -v file.hurl                      # verbose 输出
hurl --very-verbose file.hurl          # 更详细（含 body）
hurl --test --error-format long *.hurl # 错误时打印完整 HTTP 响应
hurl --color file.hurl                 # 彩色输出
hurl --curl file.hurl                  # 导出为 curl 命令

# 跟随重定向
hurl --location file.hurl
hurl --location-trusted file.hurl      # 传递认证信息到重定向目标
hurl --max-redirs 10 file.hurl

# 超时
hurl --connect-timeout 5s --max-time 30s file.hurl

# SSL
hurl --insecure file.hurl              # 跳过证书验证
hurl --cacert /path/to/ca.pem file.hurl
hurl --cert client.pem --key client.key file.hurl

# Cookie 持久化
hurl --cookie-jar cookies.txt a.hurl   # 保存 cookie
hurl --cookie cookies.txt b.hurl       # 读取 cookie

# 范围执行
hurl --from-entry 2 --to-entry 5 file.hurl

# 重试
hurl --retry 3 --retry-interval 2s file.hurl

# 压缩
hurl --compressed file.hurl            # 请求并自动解压

# 输出格式
hurl --json file.hurl                  # JSON 格式输出（类 HAR）
hurl --include file.hurl               # 包含响应头
hurl --no-output file.hurl             # 不输出 body

# 重复执行（压测）
hurl --test --repeat 100 --jobs 10 perf.hurl

# 选择文件
hurl --test --glob "test/**/*.hurl"
hurl --test test/integration/          # 递归查找 .hurl 文件

# 报告生成
hurl --test --report-html report/ *.hurl
hurl --test --report-json report/ *.hurl
hurl --test --report-junit junit.xml *.hurl
```

### 退出码

| 码 | 含义 |
|----|------|
| 0 | 成功 |
| 1 | 命令行参数解析失败 |
| 2 | 输入文件解析错误 |
| 3 | 运行时错误（连接失败等） |
| 4 | 断言错误 |

### 环境变量

```bash
http_proxy=http://proxy:8080            # HTTP 代理
https_proxy=http://proxy:8080           # HTTPS 代理
no_proxy=localhost,127.0.0.1            # 不走代理的主机
HURL_VARIABLE_host=api.example.com      # 注入变量
HURL_SECRET_token=xxx                   # 注入密钥（日志脱敏）
NO_COLOR=1                              # 禁用彩色输出
```

---

## 11. 完整实战示例

### 11.1 登录 → 获取 Token → 调用 API

```hurl
# Step 1: 登录获取 token
POST https://api.example.com/login
Content-Type: application/json
{
  "username": "alice",
  "password": "secret"
}
HTTP 200
[Captures]
auth_token: jsonpath "$.token"
[Asserts]
jsonpath "$.token" exists

# Step 2: 用 token 获取用户信息
GET https://api.example.com/me
Authorization: Bearer {{auth_token}}
HTTP 200
[Asserts]
jsonpath "$.username" == "alice"
jsonpath "$.role" == "admin"
duration < 1000
```

### 11.2 CSRF Token 场景

```hurl
# 获取 CSRF token
GET https://example.org/login
HTTP 200
[Captures]
csrf: xpath "normalize-space(//meta[@name='_csrf_token']/@content)"

# 提交登录
POST https://example.org/login
X-CSRF-TOKEN: {{csrf}}
[FormParams]
user: alice
password: 1234
HTTP 302
Location: /dashboard
```

### 11.3 轮询等待任务完成

```hurl
# 创建任务
POST https://api.example.com/jobs
{"task": "export"}
HTTP 201
[Captures]
job_id: jsonpath "$.id"

# 轮询直到完成
GET https://api.example.com/jobs/{{job_id}}
[Options]
retry: 20
retry-interval: 1s
HTTP 200
[Asserts]
jsonpath "$.status" == "COMPLETED"
```

### 11.4 文件上传

```hurl
POST https://api.example.com/upload
[Multipart]
description: My report
file: file,report.pdf; application/pdf
HTTP 200
[Asserts]
jsonpath "$.success" == true
```

### 11.5 GraphQL 查询

```hurl
POST https://api.example.com/graphql
query Hero($episode: Episode) {
  hero(episode: $episode) {
    name
    friends { name }
  }
}

variables {
  "episode": "JEDI"
}
HTTP 200
[Asserts]
jsonpath "$.data.hero.name" == "Luke Skywalker"
jsonpath "$.data.hero.friends" count > 0
```

---

## 12. 压测技巧

```hurl
GET https://my-app/health
HTTP 200
[Asserts]
duration < 500
```

```bash
# 10 个 worker × 每个 10 请求 = 100 请求
hurl --test --repeat 10 --jobs 10 perf.hurl
```

> 文件间并行，文件内串行。合理拆分避免端口耗尽。

---

## 13. hurlfmt（格式化工具）

```bash
hurlfmt file.hurl                      # 格式化输出
hurlfmt --out json file.hurl           # 转 JSON (AST)
hurlfmt --out curl file.hurl           # 转 curl 命令
hurlfmt --in curl --out hurl           # curl → hurl 格式
```

---

## 14. 常见错误避坑

1. **请求体位置错误**：请求体必须是 Request 最后一部分，若写在 [QueryStringParams]/[Cookies] 之前会报错；
2. **区块顺序错误**：[QueryStringParams]/[FormParams] 等可选区块无顺序，但必须在请求头之后、请求体之前；
3. **注释位置错误**：注释只能以 `#` 开头，不能嵌套在 JSON/XML 体中；
4. **变量引用错误**：捕获的变量需用 `{{变量名}}` 包裹，且只能在后续 Entry 中使用；
5. **断言语法错误**：JSONPath/XPath 语法需符合标准，如 `$.name` 而非 `name`；
6. **响应时间断言错误**：使用 `duration < 1000` 而非 `response-time < 1000ms`；
7. **变量定义错误**：Hurl 不支持文件内定义变量，必须使用命令行参数或环境变量。

---

## 速查表

```
请求：   METHOD URL
头：     Header-Name: value
段：     [QueryStringParams] [FormParams] [Multipart] [Cookies] [BasicAuth] [Options]
Body：   JSON / XML / ``` ... ``` / `text` / base64,...; / hex,...; / file,...;
响应：   HTTP STATUS
断言：   [Asserts]  query predicate value
捕获：   [Captures] varname: query
变量：   {{name}}
注释：   # ...
```