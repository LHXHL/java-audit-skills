# Payload 与验证规则

允许输出完整 payload，但必须绑定授权测试语境和前置条件。优先选择可观测、低破坏验证，不生成破坏性、持久化、横向移动或批量利用 payload。

## 输出要求

每个 payload 区块必须说明：

- 适用 sink/组件。
- 前置条件：组件版本、JDK 版本、gadget、鉴权、出网。
- 预期现象：DNS 回连、命令输出、错误回显、日志痕迹。
- 回滚/清理要求，如无状态 payload 填“无”。

## 推荐验证方式

| 场景 | 推荐 payload | 预期 |
|------|--------------|------|
| 原生入口探测 | URLDNS / DNS OOB | DNS 请求证明 `readObject` 触发 |
| 本地命令验证 | `id`, `whoami`, `calc` | 低破坏命令执行证明 |
| Fastjson | `@type` 指向受控验证类或 JNDI 测试链 | LDAP/DNS 回连或受控错误 |
| XStream | 版本对应 CVE 的最小化验证 XML | 回显、DNS、异常或受控命令 |
| XMLDecoder | 调用低破坏命令或 DNS 解析 | 命令/DNS 触发 |
| JDBC | 可控 JDBC URL 参数触发测试连接 | DNS/JNDI/驱动行为可观测 |

## Burp 请求要求

Burp 请求必须来自真实路由和参数结构：

```http
POST /actual/path HTTP/1.1
Host: {{host}}
Content-Type: application/json
Cookie: {{cookie_if_required}}

{"field":"{{payload}}"}
```

不要凭空编造参数名、路径或 Content-Type；若 route_mapper 未提供，请从源码入口推导并标注“待确认”。

## 禁止

- 删除文件、写入 webshell、持久化后门、提权、横向移动。
- 默认使用真实攻击者域名；使用 `{{oob_domain}}`、`{{ldap_host}}`、`{{rmi_host}}` 占位。
- 批量扫描或自动化利用脚本。
- 未说明前置条件就给 payload。
