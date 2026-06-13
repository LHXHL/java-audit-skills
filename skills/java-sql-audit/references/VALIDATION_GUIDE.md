# SQL 注入授权验证指南

本文件只在 `java-sql-audit` 需要输出“确认漏洞”或“条件成立”风险详情时读取。目标是给开发单位提供可复核材料，而不是生成攻击脚本。

## 输出前提

只有同时满足以下条件，才输出 Burp Suite 请求和 payload：

- 结论状态是确认漏洞或条件成立。
- 已读取真实入口代码或可信上游路由证据。
- 已确认 HTTP 方法、路径、参数名、Content-Type 和鉴权上下文。
- 已确认用户输入到达 SQL sink，且参数绑定、白名单或强类型保护缺失或不足。
- payload 不会修改数据、读取文件、执行命令、外带数据或批量枚举；若使用时间延迟或最小回显/元数据探针，必须限制为授权测试环境、单请求、短延迟和最小数据面。

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

优先选择最小、只读、可观测 payload。基础探针优先；当基础探针无法稳定确认 SQL 结构被用户输入影响时，才加入增强探针。

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

- payload 可以按漏洞形态包含布尔差异、WHERE 改写、注释符或必要的受控堆叠语句；若可能影响写操作范围，必须限定授权测试环境、最小样本、备份或事务回滚。
- payload 不引入命令执行、文件读写、DNS/OOB 外带、批量枚举或业务数据抽取。
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
- 可在必要时使用受控堆叠查询、WHERE 改写或注释符探针来证明 SQL 结构可控；不得业务表枚举或使用会造成服务压力的长延时函数；短时间延迟探针只允许单请求、短延迟、授权测试环境中作为增强验证。

### 标识符位置

适用于表名、列名、排序字段、排序方向等动态标识符缺少白名单的确认风险：

```text
{{allowed_column}}
invalid_column_for_validation
{{allowed_direction}}
invalid_direction_for_validation
```

使用条件：

- payload 用于证明白名单缺失或弱过滤，不用于抽取业务数据。
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
- 注释符只能用于最小化验证 SQL 结构可控；不得拼接业务数据抽取语句或冗长逃逸 payload。

### 增强验证：短时间延迟

适用于错误信息被统一处理、结果差异不可见，但已确认输入能进入可执行 SQL 片段的确认漏洞或条件成立项。

```text
{{baseline_value}}' AND {{short_delay_condition}} AND '1'='1
{{baseline_number}} AND {{short_delay_condition}}
```

写法要求：

- `{{short_delay_condition}}` 必须由开发单位按实际数据库替换为短延迟表达式，建议单次延迟不超过 3 秒。
- 只能单请求验证，不得并发、循环或用于可用性压测。
- 报告必须写明预期观察是短延迟差异，不得写“攻击成功”或伪造响应。
- 若数据库类型未知，写“数据库类型待确认”，不要同时给多种数据库的可复制延迟 payload。

### 增强验证：最小回显或元数据

适用于需要证明查询结构可被控制，且授权测试环境允许观察回显字段、SQL 日志或受控错误的确认漏洞或条件成立项。

```text
{{baseline_value}}' UNION SELECT {{constant_marker}} --
{{baseline_value}}' AND '{{constant_marker}}'='{{constant_marker}}
```

写法要求：

- 优先使用常量回显、当前数据库名、当前用户或版本这类最小元数据；不得读取业务表数据、账号、密码、Token、身份证件、视频/图片路径等敏感数据。
- 不枚举大量系统表，不 dump 表结构，不批量抽取。
- 字段数量、注释符和数据库语法未知时，不输出可复制 `UNION` payload；改写为“需开发单位按实际 SQL 列数构造最小回显探针”。
- 报告必须说明这是增强验证，不是利用链或数据导出步骤。

## 禁止内容

不得输出：

- 缺少授权测试环境、最小样本、备份或事务回滚说明的 `DROP`、`ALTER`、`TRUNCATE`、`INSERT`、`UPDATE`、`DELETE` 等会修改结构或数据的语句。
- 命令执行、文件读写、DNS/OOB、内网探测。
- 业务数据抽取、系统表批量枚举、表结构 dump、账号/密码/Token 等敏感数据读取。
- 长时间延迟、并发延迟、循环延迟或任何可能造成服务压力的探测。
- `xp_cmdshell` 等数据库命令执行能力。
- 自动化扫描脚本、批量验证脚本或未授权目标请求。

## 报告写法

每个确认漏洞或条件成立风险的验证材料必须包含：

- `#### Burp Suite 请求`：一段可复制的原始 HTTP 请求，或说明“非 HTTP 入口，不输出 Burp 请求”。
- `#### Payload`：按“基础探针”和“增强探针（可选）”分组列出当前参数适用的 payload，不混入其它数据库或其它漏洞类型；增强探针必须写明授权、短延迟或最小回显限制。
- `#### 授权验证说明`：说明适用环境、预期观察、回滚/清理和风险限制。

待验证、不可确认和非漏洞项只能写补证建议，例如：

- 补充 route-mapper 或 route-tracer 证据。
- 确认 Mapper statement 是否被入口调用。
- 确认数据库类型、配置分支或白名单来源。
- 打开 SQL 日志或断点观察最终 SQL 结构。
