# Session / Cookie 鉴权参考

只在项目使用 `JSESSIONID`、自定义 session、RememberMe、Cookie 登录态或服务端会话权限时读取本文件。

## 必查点

- 登录前后 Session ID 是否轮换。
- Session 超时、销毁、退出登录是否清理服务端状态。
- Cookie 属性：HttpOnly、Secure、SameSite、Path、Domain。
- 会话中保存的用户、角色、租户信息是否重新校验。
- RememberMe 是否等同认证、是否允许访问敏感操作。

## 危险模式

| 模式 | 风险 |
|------|------|
| 登录后不换 Session ID | Session fixation |
| 退出只清 Cookie 不清服务端 session | 会话复用 |
| Cookie 缺 HttpOnly/Secure | 劫持风险 |
| Session 中 role 可由请求参数覆盖 | 权限提升 |
| RememberMe 用户可访问敏感接口 | 弱认证绕过 |

## 误报防线

- Cookie 属性缺失通常不是“鉴权绕过”，应按会话安全风险分级。
- Session timeout 过长是加固问题，除非有明确敏感影响。
- RememberMe 风险要结合 Shiro/Spring 配置和具体访问控制。

## Gotchas

- 多节点部署要看 session 存储和同步。
- SSO/CAS/Keycloak 场景下本地 session 可能只是二级状态。
- 并发 session 控制缺失不等于越权，除非能导致账号占用或权限残留。
