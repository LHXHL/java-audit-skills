# SQL 注入授权验证指南

本文件只在 `java-sql-audit` 需要输出“确认漏洞”或“条件成立”风险详情时读取。目标是给开发单位提供可复核材料，而不是生成攻击脚本。

## 输出前提

只有同时满足以下条件，才输出 Burp Suite 请求和 payload：

- 结论状态是确认漏洞或条件成立。
- 已读取真实入口代码或可信上游路由证据。
- 已确认 HTTP 方法、路径、参数名、Content-Type 和鉴权上下文。
- 已确认用户输入到达 SQL sink，且参数绑定、白名单或强类型保护缺失或不足。
- payload 不会修改数据、拖慢服务、读取文件、执行命令、外带数据或批量枚举。

不满足任一条件时，把该项留在报告第 4 节，写补证路径，不输出可复制请求。

## Burp Suite 请求格式

Burp 请求必须是合法原始 HTTP 请求：

```http
GET /actual/path?keyword={{payload}} HTTP/1.1
Host: {{host}}
Cookie: {{cookie_if_required}}
```

或：

```http
POST /actual/path HTTP/1.1
Host: {{host}}
Content-Type: application/x-www-form-urlencoded
Cookie: {{cookie_if_required}}

keyword={{payload}}&page={{baseline_value}}
```

JSON 请求：

```http
POST /actual/path HTTP/1.1
Host: {{host}}
Content-Type: application/json
Cookie: {{cookie_if_required}}

{"keyword":"{{payload}}","page":1}
```

要求：

- 首行只能包含路径和查询串，不能写 `GET {{host}}/path HTTP/1.1`。
- `Host`、`Cookie`、CSRF token 等环境相关值使用占位符。
- 路径、方法、参数名、Content-Type 必须来自源码或可信上游证据；不能猜。
- 如果入口是 RPC、MQ、定时任务或内部调用，不输出 HTTP Burp 请求；改写为“非 HTTP 入口，需由开发单位在授权测试环境构造调用 harness”。
- 不伪造响应包、数据库错误、SQL 日志或验证成功截图。

## Payload 选择

优先选择最小、只读、可观测 payload。

### 值位置

适用于字符串值直接拼接进 SQL 的确认风险：

```text
{{baseline_value}}
'
''
{{baseline_value}}' AND '1'='1
{{baseline_value}}' AND '1'='2
```

使用条件：

- payload 不引入 DML/DDL、延时、外带或数据抽取。
- 预期观察是受控错误、结果数量差异或 SQL 日志结构差异。
- 若项目使用强类型解析或参数绑定，不要给字符串 payload。

### 数值位置

适用于数值参数未强类型化、以字符串方式拼接的确认风险：

```text
{{baseline_number}}
{{baseline_number}} AND 1=1
{{baseline_number}} AND 1=2
```

使用条件：

- 已确认该参数未被 `parseInt`、`parseLong`、枚举或绑定保护。
- 不使用 `UNION SELECT`、子查询枚举、延时函数或堆叠查询。

### 标识符位置

适用于表名、列名、排序字段、排序方向等动态标识符缺少白名单的确认风险：

```text
{{allowed_column}}
invalid_column_for_validation
{{allowed_direction}}
invalid_direction_for_validation
```

使用条件：

- payload 用于证明白名单缺失或弱过滤，不用于抽取数据。
- 预期观察是非法标识符被拼入 SQL、受控错误或未被拒绝。

### LIKE 场景

适用于 `LIKE '%${keyword}%'` 或等价拼接：

```text
{{baseline_keyword}}
'
%' AND '1'='1
%' AND '1'='2
```

使用条件：

- 仅用于授权测试环境观察受控错误、结果差异或 SQL 日志结构。
- 不拼接数据抽取语句或注释符逃逸长 payload。

## 禁止内容

不得输出：

- `DROP`、`ALTER`、`TRUNCATE`、`INSERT`、`UPDATE`、`DELETE` 等修改结构或数据的语句。
- 堆叠查询、`UNION SELECT` 数据抽取、系统表枚举。
- `SLEEP`、`BENCHMARK`、`WAITFOR` 等时间延迟探测。
- `xp_cmdshell`、命令执行、文件读写、DNS/OOB、内网探测。
- 自动化扫描脚本、批量验证脚本或未授权目标请求。

## 报告写法

每个确认漏洞或条件成立风险的验证材料必须包含：

- `#### Burp Suite 请求`：一段可复制的原始 HTTP 请求，或说明“非 HTTP 入口，不输出 Burp 请求”。
- `#### Payload`：列出当前参数适用的低风险 payload，不混入其它数据库或其它漏洞类型。
- `#### 授权验证说明`：说明适用环境、预期观察、回滚/清理和风险限制。

待验证、不可确认和非漏洞项只能写补证建议，例如：

- 补充 route-mapper 或 route-tracer 证据。
- 确认 Mapper statement 是否被入口调用。
- 确认数据库类型、配置分支或白名单来源。
- 打开 SQL 日志或断点观察最终 SQL 结构。
