# Burp Suite 与 Payload 验证材料

只在某条风险已经达到 `确认漏洞` 或 `条件成立` 门槛时读取本文件。它用于给开发单位提供可复核材料，不用于把候选风险包装成漏洞。

## 何时生成

必须同时满足：

- 入口真实存在，HTTP 方法、路径、协议和参数名来自源码、配置、route mapper 或反编译结果。
- 鉴权缺口已经定位，且后续 Filter、Interceptor、框架规则、注解、业务权限或对象归属校验不会补救。
- 影响明确，例如未登录访问敏感功能、低权限访问高权限功能、非所有者访问对象、JWT 伪造后被接受。
- 请求只验证当前结论，不包含批量枚举、破坏性动作或无关漏洞变体。

以下情况不得生成 Burp Suite 请求或 payload：

- `待验证`、`不可确认`、`非漏洞`。
- 只有 `{id}`、`userId`、`tenantId` 参数，但未确认缺 owner/tenant/currentUser 校验。
- 只发现 Cookie 属性、session timeout、CSRF/CORS、密码策略、日志审计、限流等加固项。
- 只发现明文密码 Cookie、浏览器“记住密码”或自动填充密码，且 Cookie 不能直接充当服务端登录态。
- 只有父类、AOP、网关或运行时配置未知。
- 只有自定义 Filter、Interceptor、HandlerInterceptor、Servlet 或框架适配层的内部实现未知。
- 只命中组件版本或公告，缺本项目触发路径。

## 请求写法

- 使用 Burp Repeater 可直接粘贴的 HTTP 请求块。
- Host、Cookie、JWT、CSRF、Session、用户 ID、对象 ID、租户 ID、文件名等敏感值使用占位符。
- 保留真实路径、参数名、Content-Type 和必要 header。
- 请求体只保留触发当前鉴权判断的最小字段。
- 不写真实账号、密码、token、生产域名、内网 IP 或客户数据。

## 常用验证场景

### 未登录访问

适用：入口应要求登录，但静态证据显示未进入有效认证层。

```http
GET /real/path HTTP/1.1
Host: {host}
Accept: application/json
```

变体：

- 无 Cookie 与无 Authorization。
- 过期或随机 `JSESSIONID={invalid_session}`。
- 如果项目要求 CSRF token，说明“未登录状态下无法取得合法 token，需开发在测试环境验证”。

### 垂直越权

适用：入口只校验登录，未校验角色或权限。

```http
POST /admin/realAction HTTP/1.1
Host: {host}
Cookie: JSESSIONID={low_privilege_session}
Content-Type: application/x-www-form-urlencoded

id={object_id}&action={safe_action}
```

变体：

- 管理员/合法角色请求作为对照组。
- 普通用户/低权限角色请求作为测试组。
- 预期观察必须说明：`403/401/跳转登录` 是否会否定结论，`200 + 敏感数据/动作成功` 是否支持结论。

### 水平越权或 IDOR

适用：代码证据已经确认没有 owner、tenant、department、currentUser 等归属校验。

```http
GET /orders/{other_user_order_id} HTTP/1.1
Host: {host}
Cookie: JSESSIONID={user_a_session}
Accept: application/json
```

变体：

- user A 访问 user A 对象作为对照组。
- user A 访问 user B 对象作为测试组。
- 对象 ID 使用占位符，禁止批量遍历。

### JWT 校验缺陷

适用：代码证据确认只 decode 不 verify，或签名、算法、过期时间、issuer、audience 校验缺失足以影响认证。

```http
GET /api/protected HTTP/1.1
Host: {host}
Authorization: Bearer {jwt_with_placeholder_claims}
Accept: application/json
```

payload 说明只描述 claim 差异，例如：

| 目的 | 变体 | 预期观察 |
|------|------|----------|
| 角色提升 | `{role: "admin"}` | 若服务端接受并返回管理数据，则支持结论 |
| 用户切换 | `{userId: "{other_user_id}"}` | 若服务端未校验服务端状态，则支持结论 |

不要生成可直接伪造签名的脚本；如果缺密钥或真实 token，只写占位符和验证思路。

### 路径解析绕过

适用：已确认鉴权层和路由层解析不一致，payload 会到达同一敏感入口且后续无有效拦截。

```http
GET /public;/../admin/realPath HTTP/1.1
Host: {host}
Cookie: JSESSIONID={optional_session}
Accept: application/json
```

payload 表必须说明：

- 原始路径。
- 鉴权层看到的路径。
- 路由层最终匹配的入口。
- 哪一层缺失后续拦截。

## 写入主报告的最小材料

每个 `确认漏洞` 或 `条件成立` 风险至少包含：

- `Burp Suite 请求`：一个最小请求。
- `Payload / 变体`：对照组和测试组，或路径/JWT/对象变体。
- `授权验证说明`：预期支持结论和否定结论的响应。
- `安全限制`：不使用真实凭据，不批量枚举，不执行破坏性动作。
