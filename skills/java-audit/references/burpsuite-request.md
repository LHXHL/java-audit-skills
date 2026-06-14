# BurpSuite 原始 HTTP 请求包规范

## 基本要求

确认漏洞必须提供可放入 BurpSuite Repeater 的原始 HTTP 请求包：

```http
GET /path?name=value HTTP/1.1
Host: target.example
User-Agent: Mozilla/5.0
Accept: */*

```

## 必须满足

- 请求方法、路径、参数名、Content-Type 必须来自代码证据或用户提供的运行环境信息。
- 需要认证时，使用占位符，例如 `Cookie: SESSION=<AUTHORIZED_TEST_SESSION>`，不要写真实凭据。
- JSON、XML、multipart、表单请求体必须和目标代码绑定方式一致。
- multipart 请求必须包含边界和字段名；不能只写“上传恶意文件”。
- payload 必须和触发条件匹配，不能套用通用 payload。

## 禁止

- 不要编造 Host、Cookie、Token、路径、参数名或 body 结构。
- 不要包含真实生产域名、真实凭据、真实敏感数据。
- 不要输出批量利用脚本、持久化 payload、横向移动步骤或破坏性操作。
- 高风险线索缺少可复现证据时，不要写原始 HTTP 请求包。
