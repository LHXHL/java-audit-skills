# XXE 授权验证指南

本文件只在 `java-xxe-audit` 需要输出“确认漏洞”或“条件成立”风险详情时读取。目标是给开发单位提供可复核材料，而不是生成未授权攻击请求。

## 输出前提

只有同时满足以下条件，才输出 Burp Suite 请求和 payload：

- 结论状态是确认漏洞或条件成立。
- 已读取真实入口代码或可信上游路由证据。
- 已确认 HTTP 方法、路径、参数位置、Content-Type 和鉴权上下文。
- 已确认用户可控 XML 到达真实 XML parser/transformer/unmarshaller/fromXML sink。
- 已确认外部实体、外部 DTD、XInclude、外部资源访问或 resolver 防护缺失或不完整。
- 对 `XStream.fromXML`，已确认底层 driver/parser 支持外部实体解析，且已掌握目标对象 XML 结构。
- payload 不读取真实敏感文件、不访问内网地址、不访问云元数据、不外带敏感数据、不触发实体扩展 DoS、不做批量探测。

不满足任一条件时，把该项留在报告第 4 节，写补证路径，不输出可复制请求。
如果只能给 `DOCTYPE` 片段，但无法嵌入目标对象结构，不能输出 `#### Payload`，该项应降为待验证或不可确认。

## Burp Suite 请求格式

SOAP/XML 请求：

```http
POST /actual/xml-or-soap/path HTTP/1.1
Host: {{host}}
Content-Type: text/xml; charset=UTF-8
Cookie: {{cookie_if_required}}

{{payload}}
```

REST XML 请求：

```http
POST /actual/path HTTP/1.1
Host: {{host}}
Content-Type: application/xml
Cookie: {{cookie_if_required}}

{{payload}}
```

表单字段中的 XML：

```http
POST /actual/path HTTP/1.1
Host: {{host}}
Content-Type: application/x-www-form-urlencoded
Cookie: {{cookie_if_required}}

xml={{url_encoded_payload}}
```

要求：

- 首行只能包含路径和查询串，不能写 `POST {{host}}/path HTTP/1.1`。
- `Host`、`Cookie`、CSRF token 等环境相关值使用占位符。
- 路径、方法、参数位置、Content-Type 必须来自源码、配置、WSDL、route-mapper 或可信上游证据；不能猜。
- 如果入口是 MQ、定时任务、内部 RPC 或文件导入流程，不输出 HTTP Burp 请求；改写为“非 HTTP 入口，需由开发单位在授权测试环境构造调用 harness”。
- 不伪造响应包、文件内容、resolver 日志或外带成功结果。

## Payload 选择

优先选择最小、可观测、低破坏 payload。所有 payload 必须使用占位符，不能写真实敏感路径、内网地址或云元数据地址。

### 受控 canary 探测

适用于无回显但可能允许外部 DTD 或外部实体解析的确认风险：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "{{xxe_canary_url}}">
]>
<root>&xxe;</root>
```

使用条件：

- `{{xxe_canary_url}}` 必须是开发单位或授权测试环境控制的 canary 地址。
- 预期观察只能写“受控 canary 请求”或“resolver 拒绝日志”，不得声称已回连成功。
- 不使用内网地址、云元数据地址或真实第三方域名。

### 安全测试文件探测

适用于有回显路径且开发单位可在测试环境创建无敏感测试文件的确认风险：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file://{{safe_test_file_path}}">
]>
<root>&xxe;</root>
```

使用条件：

- `{{safe_test_file_path}}` 必须由开发单位在测试环境创建，内容为无敏感 marker。
- 不写 `/etc/passwd`、`/etc/hostname`、`C:\Windows\win.ini`、应用配置文件、密钥文件或任何真实敏感路径。
- 预期观察写“marker 是否被返回或进入日志”，不得写真实文件内容。

### 外部 DTD 加载探测

适用于需要验证 `load-external-dtd` 或 `ACCESS_EXTERNAL_DTD` 的确认风险：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root SYSTEM "{{controlled_test_dtd_url}}">
<root>xxe-test</root>
```

使用条件：

- `{{controlled_test_dtd_url}}` 必须是授权测试环境控制的 DTD URL。
- DTD 内容不得包含文件读取、内网探测、数据外带或实体扩展 DoS。

## 禁止内容

不得输出：

- 真实敏感文件路径、系统文件路径、应用配置路径、密钥路径。
- 内网 IP、localhost、云元数据地址、管理端口、第三方目标。
- 参数实体链式外带文件内容、HTTP/DNS/OOB 数据外带模板。
- Billion Laughs、指数实体扩展、压缩炸弹或其它 DoS payload。
- 自动化扫描脚本、批量验证脚本或未授权目标请求。
- 伪造响应包、文件内容、外带日志或验证成功断言。

## 报告写法

每个确认漏洞或条件成立风险的验证材料必须包含：

- `#### Burp Suite 请求`：一段可复制的原始 HTTP 请求，或说明“非 HTTP 入口，不输出 Burp 请求”。
- `#### Payload`：列出当前入口适用的低风险 XML payload，不混入 SSRF、文件读取、DoS 或反序列化链。
- `#### 授权验证说明`：说明适用环境、预期观察、回滚/清理和风险限制。

待验证、不可确认和非漏洞项只能写补证建议，例如：

- 补充 route-mapper 或 route-tracer 证据。
- 确认 SOAP/CXF/JAX-WS 真实入口地址和 Content-Type。
- 反编译 XML 工具类、resolver 或 WebService handler。
- 确认 parser/factory feature 是否在实际解析实例上生效。
