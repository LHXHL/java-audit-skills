# 文件上传授权验证规则

本文件用于 `java-file-upload-audit` 输出可提交开发单位的验证材料。目标是帮助开发单位在授权测试环境复现风险，不生成后门、持久化、批量利用或不可控破坏内容。

## 何时必须输出

| 结论状态 | Burp Suite 请求 | Payload | 说明 |
|----------|-----------------|---------|------|
| 确认漏洞 | 必须 | 必须 | 入口、参数、写入 sink、校验缺口和执行条件均有证据 |
| 条件成立 | 必须 | 必须 | 必须列明依赖的配置、权限、目录映射或运行条件 |
| 待验证 | 禁止 | 禁止 | 只写证据缺口和补证方向 |
| 不可确认 | 禁止 | 禁止 | 写清缺失证据 |
| 非漏洞 | 禁止 | 禁止 | 写清安全依据 |

## 输出硬规则

1. Burp Suite 请求必须匹配真实入口、HTTP 方法、参数名、Content-Type、鉴权状态和必要 CSRF/业务字段；缺失字段使用 `{{placeholder}}`，不得凭空编造。
2. HTTP 请求行必须是 Burp 可直接识别的格式：`POST /path HTTP/1.1`。不要把 `{{host}}`、协议或完整 URL 写进请求行；主机只写在 `Host: {{host}}` 头。
3. 字段名、业务参数名或路径片段未确认时，必须使用占位符，例如 `name="{{file_field_from_form}}"`、`{{required_business_field}}`、`/{{confirmed_or_placeholder}}.upload`，并在说明中标注待开发单位确认；不得把推测字段写成确定字段。
4. Payload 必须是低破坏验证内容，优先使用纯文本 marker，例如 `upload-validation-{{case_id}}`。
5. 不输出可执行后门内容、持久化脚本、批量上传脚本、横向移动步骤、清理规避技巧或真实攻击者域名。
6. 不声称上传、访问或代码执行已经达成；预期现象只能写“响应中可能出现文件路径/ID”“目录中可观察到测试文件”等待开发单位验证的描述。
7. 不给待验证、不可确认或非漏洞项生成请求；这些状态只写证据缺口、补证方向或安全依据。
8. 若需要证明类型校验缺陷，文件名、扩展名或 Content-Type 必须来自代码证据或授权验证条件；文件内容仍使用无害 marker。
9. 若需要证明路径控制或覆盖风险，路径字段使用 `{{test_path}}`、`{{filename}}` 等占位符，不给系统敏感路径或目录穿越样本。
10. 所有请求都必须标注“仅限授权测试环境”，并写清清理要求。
11. 不为容量阈值、磁盘占用或 DoS 场景生成大文件 Payload；容量问题只作为加固建议，除非用户明确要求授权压测方案。

## Burp Suite 请求模板

用于真实 multipart/form-data 入口；字段名必须替换为源码或 route-mapper 中确认的字段名。

```http
POST /{{upload_path}} HTTP/1.1
Host: {{host}}
Cookie: {{cookie_if_required}}
Content-Type: multipart/form-data; boundary=----audit-boundary

------audit-boundary
Content-Disposition: form-data; name="{{file_field}}"; filename="{{test_filename}}"
Content-Type: {{content_type}}

upload-validation-{{case_id}}
------audit-boundary
Content-Disposition: form-data; name="{{required_field}}"

{{required_value}}
------audit-boundary--
```

用于 Base64、JSON、SOAP 或自定义上传入口时，应保留真实协议结构，只把文件内容替换为 marker：

```http
POST /{{upload_path}} HTTP/1.1
Host: {{host}}
Cookie: {{cookie_if_required}}
Content-Type: application/json

{
  "{{filename_field}}": "{{test_filename}}",
  "{{content_field}}": "{{base64_upload_validation_marker}}"
}
```

## Payload 区块要求

每个风险详情中的 Payload 必须包含：

- 适用入口和参数。
- 文件名来源与建议测试文件名，占位符优先。
- 文件内容 marker。
- 预期现象：文件被写入、返回文件 ID、日志出现写入路径、或后续解析被触发。
- 清理要求：删除测试文件、回滚测试数据、清理临时目录。
- 限制说明：哪些条件未在静态审计中确认。

## 禁止示例类型

- 后门、命令执行、持久化、提权、横向移动或隐藏访问内容。
- 批量扫描、批量上传或自动化利用脚本。
- 未绑定真实路由和参数的通用攻击请求。
- 真实系统敏感路径、目录穿越样本或绕过技巧清单。
- 大文件、资源耗尽或压测型 Payload。
