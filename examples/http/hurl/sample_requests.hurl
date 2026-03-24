#!/usr/bin/env hurl
# Hurl 完整示例文件（正确版）
# 基于 Hurl 7.1.0 语法
# 运行: hurl --test sample_requests.hurl

# ==================== GET 请求示例 ====================
# 获取用户列表
GET https://jsonplaceholder.typicode.com/users
HTTP 200
[Asserts]
header "Content-Type" == "application/json; charset=utf-8"
jsonpath "$" count > 0
jsonpath "$[0].id" exists
jsonpath "$[0].name" exists
jsonpath "$[0].email" exists

###
# 获取单个用户信息
GET https://jsonplaceholder.typicode.com/users/1
HTTP 200
[Asserts]
header "Content-Type" contains "application/json"
jsonpath "$.id" == 1
jsonpath "$.username" exists
jsonpath "$.email" contains "@"

###
# ==================== POST 请求示例 ====================
# 创建新用户
POST https://jsonplaceholder.typicode.com/users
Content-Type: application/json
Body:
{
  "name": "John Doe",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "address": {
    "street": "123 Main St",
    "suite": "Apt. 4B",
    "city": "New York",
    "zipcode": "10001",
    "geo": {
      "lat": "40.7128",
      "lng": "-74.0060"
    }
  },
  "phone": "555-1234",
  "website": "johndoe.com",
  "company": {
    "name": "ACME Corp",
    "catchPhrase": "Quality is our priority",
    "bs": "synergize scalable solutions"
  }
}
HTTP 201
[Asserts]
header "Content-Type" == "application/json; charset=utf-8"
jsonpath "$.name" == "John Doe"
jsonpath "$.username" == "johndoe"
jsonpath "$.email" == "john.doe@example.com"
jsonpath "$.id" exists

###
# ==================== PUT 请求示例 ====================
# 更新用户信息（全量更新）
PUT https://jsonplaceholder.typicode.com/users/1
Content-Type: application/json
Body:
{
  "id": 1,
  "name": "Jane Doe Updated",
  "username": "janedoe_updated",
  "email": "jane.updated@example.com",
  "address": {
    "street": "456 Oak Ave",
    "suite": "Suite 200",
    "city": "Los Angeles",
    "zipcode": "90001",
    "geo": {
      "lat": "34.0522",
      "lng": "-118.2437"
    }
  },
  "phone": "555-5678",
  "website": "janedoe-updated.com",
  "company": {
    "name": "Updated Corp",
    "catchPhrase": "Innovation drives success",
    "bs": "leverage cutting-edge technologies"
  }
}
HTTP 200
[Asserts]
header "Content-Type" == "application/json; charset=utf-8"
jsonpath "$.name" == "Jane Doe Updated"
jsonpath "$.username" == "janedoe_updated"
jsonpath "$.email" == "jane.updated@example.com"
jsonpath "$.address.city" == "Los Angeles"

###
# ==================== PATCH 请求示例 ====================
# 部分更新用户信息
PATCH https://jsonplaceholder.typicode.com/users/1
Content-Type: application/json
Body:
{
  "email": "jane.patch@example.com",
  "phone": "555-9999"
}
HTTP 200
[Asserts]
header "Content-Type" == "application/json; charset=utf-8"
jsonpath "$.email" == "jane.patch@example.com"
jsonpath "$.phone" == "555-9999"

###
# ==================== DELETE 请求示例 ====================
# 删除用户
DELETE https://jsonplaceholder.typicode.com/users/1
HTTP 200

###
# ==================== 带查询参数的 GET 请求 ====================
# 获取用户的帖子
GET https://jsonplaceholder.typicode.com/posts?userId=1&_limit=5
HTTP 200
[Asserts]
jsonpath "$" count <= 5
jsonpath "$[0].userId" == 1

###
# ==================== 错误处理示例 ====================
# 请求不存在的资源
GET https://jsonplaceholder.typicode.com/users/99999
HTTP 404

###
# ==================== 带变量的示例 ====================
# 使用变量（可以通过 --variable 参数传入）
# 运行: hurl --variable baseUrl=https://jsonplaceholder.typicode.com sample_requests.hurl

GET {{baseUrl}}/users
HTTP 200
[Asserts]
jsonpath "$" count > 0

###
# ==================== 带认证头的示例 ====================
# 使用变量传入认证 Token
# 运行: hurl --variable token="Bearer your-token" sample_requests.hurl

GET https://jsonplaceholder.typicode.com/users
Authorization: {{token}}
HTTP 200
[Asserts]
jsonpath "$" count > 0

###
# ==================== 响应时间测试 ====================
GET https://jsonplaceholder.typicode.com/users
HTTP 200
[Asserts]
duration < 5000