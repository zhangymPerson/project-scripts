# Hurl 测试示例文件
# 安装：https://hurl.dev/docs/installation.html
# 运行：hurl --test hurl_test_example.hurl
# 运行（带变量）：hurl --test --variable baseUrl=https://echo.apifox.com hurl_test_example.hurl

# =============================================================================
# 变量定义
# =============================================================================
# 可以通过 --variable 参数传入，或在命令行定义
# baseUrl = https://echo.apifox.com
# token = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# =============================================================================
# GET 请求测试
# =============================================================================

GET {{baseUrl}}/get?q1=value1&q2=value2
[Options]
retry: 3
HTTP 200
[Asserts]
header "Content-Type" == "application/json"
jsonpath "$.args.q1" == "value1"
jsonpath "$.args.q2" == "value2"
jsonpath "$.url" contains "/get"

###

# =============================================================================
# POST 请求测试
# =============================================================================

POST {{baseUrl}}/post
Authorization: Bearer {{token}}
Content-Type: application/json
[Options]
retry: 3
{
    "name": "testuser",
    "email": "test@example.com",
    "data": {
        "field1": "value1",
        "field2": 123
    }
}
HTTP 200
[Asserts]
header "Content-Type" == "application/json"
jsonpath "$.json.name" == "testuser"
jsonpath "$.json.email" == "test@example.com"
jsonpath "$.json.data.field1" == "value1"
jsonpath "$.json.data.field2" == 123
jsonpath "$.headers.Authorization" contains "Bearer"

###

# =============================================================================
# PUT 请求测试
# =============================================================================

PUT {{baseUrl}}/put?q1=update_value
Authorization: Bearer {{token}}
Content-Type: application/json
[Options]
retry: 3
{
    "id": 1,
    "username": "updated_user",
    "email": "updated@example.com",
    "status": "active"
}
HTTP 200
[Asserts]
header "Content-Type" == "application/json"
jsonpath "$.json.id" == 1
jsonpath "$.json.username" == "updated_user"
jsonpath "$.json.email" == "updated@example.com"
jsonpath "$.args.q1" == "update_value"

###

# =============================================================================
# DELETE 请求测试
# =============================================================================

DELETE {{baseUrl}}/delete?q1=delete_value
Authorization: Bearer {{token}}
Content-Type: application/json
[Options]
retry: 3
{
    "id": 1,
    "reason": "user_request"
}
HTTP 200
[Asserts]
header "Content-Type" == "application/json"
jsonpath "$.json.id" == 1
jsonpath "$.json.reason" == "user_request"
jsonpath "$.args.q1" == "delete_value"

###

# =============================================================================
# 健康检查测试
# =============================================================================

GET {{baseUrl}}/get
HTTP 200
[Asserts]
jsonpath "$.url" isString

###

# =============================================================================
# 带分页参数的请求测试
# =============================================================================

GET {{baseUrl}}/get?page=1&pageSize=20&status=active
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.args.page" == "1"
jsonpath "$.args.pageSize" == "20"
jsonpath "$.args.status" == "active"

###

# =============================================================================
# 认证测试 - 登录并捕获 Token
# =============================================================================

POST {{baseUrl}}/post
Content-Type: application/json
{
    "username": "testuser",
    "password": "SecurePass123!"
}
HTTP 200
[Asserts]
jsonpath "$.json.username" == "testuser"

###

# =============================================================================
# 错误处理测试 - 测试 404 响应
# =============================================================================

GET {{baseUrl}}/status/404
HTTP 404

###

# =============================================================================
# 错误处理测试 - 测试 500 响应
# =============================================================================

GET {{baseUrl}}/status/500
HTTP 500

###

# =============================================================================
# 响应时间测试
# =============================================================================

GET {{baseUrl}}/get
HTTP 200
[Asserts]
duration < 1000

###

# =============================================================================
# 复杂断言测试
# =============================================================================

POST {{baseUrl}}/post
Content-Type: application/json
{
    "items": [1, 2, 3],
    "metadata": {
        "version": "1.0",
        "count": 3
    }
}
HTTP 200
[Asserts]
jsonpath "$.json.items" count == 3
jsonpath "$.json.items[0]" == 1
jsonpath "$.json.metadata.version" == "1.0"
jsonpath "$.json.metadata.count" == 3
header "Content-Type" startsWith "application/json"
jsonpath "$.headers" exists
jsonpath "$.origin" exists
