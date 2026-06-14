# 令牌鉴权参考

本文件不列具体令牌库或 API。统一检查 `TOKEN_CONTEXT`。

## 检查点

- token 是否验签或完整性校验。
- issuer、audience、过期时间、使用范围是否被校验。
- 用户、角色、租户和权限声明是否可信。
- 服务端是否允许客户端覆盖 `AUTH_CONTEXT`。
- 高风险操作是否重新校验 `POLICY_RULE`。
