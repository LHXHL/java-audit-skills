# Session / Cookie 鉴权参考

只在项目使用 `JSESSIONID`、自定义 session、RememberMe、Cookie 登录态或服务端会话权限时读取本文件。

## 必查点

- 登录前后 Session ID 是否轮换。
- 退出登录是否清理服务端 session。
- Cookie 中保存的是 opaque session id，还是用户、角色、租户、权限等可影响鉴权的数据。
- 服务端是否在每次敏感操作重新确认用户状态、角色、租户和对象归属。
- RememberMe 是否允许访问敏感操作。

## 风险边界

| 情况 | 处理方式 |
|------|----------|
| Cookie 缺 HttpOnly/Secure/SameSite | README 加固建议，除非直接造成认证绕过 |
| 明文密码 Cookie / 浏览器记住密码 | README 加固建议，除非该 Cookie 本身被服务端当作登录态并可伪造/复用 |
| session timeout 过长 | README 加固建议 |
| 登录后不换 Session ID | 只有攻击者可设置并复用受害者登录后的 session 时，才按会话固定风险处理 |
| 退出只清 Cookie 不清服务端 session | 需要证明旧 session 可继续访问敏感入口 |
| Cookie 中 role/userId 可被客户端篡改 | 若服务端信任该值，可进入主报告 |
| RememberMe 可访问敏感操作 | 需结合框架配置和具体入口判断 |

## 误报防线

- Cookie 属性缺失通常不是认证绕过或越权。
- 明文保存密码是凭据暴露/客户端加固问题，不等于认证绕过；不要为它生成 Burp Suite 请求。
- 并发 session 控制缺失不是越权，除非导致权限残留或账号占用。
- SSO/CAS/Keycloak 场景下本地 session 可能只是二级状态，要确认真实鉴权源。

## 输出要求

- 主报告必须证明会话问题如何影响认证或授权结果。
- 只有可复核的会话固定、会话复用、客户端可篡改身份或 RememberMe 弱认证，才生成 Burp Suite 请求。
