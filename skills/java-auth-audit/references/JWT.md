# JWT 鉴权参考

只在项目存在 JWT 库、Bearer Token、`JwtParser`、`JWTVerifier`、OAuth2 Resource Server 或自定义 token 校验时读取本文件。

## 必查点

- 使用的库和版本：JJWT、Auth0 java-jwt、Nimbus、Spring Security OAuth2。
- 是否验证签名，是否固定允许算法。
- 是否校验 `exp`、`nbf`、`iss`、`aud`、用户状态和 token 吊销。
- 密钥来源：配置、环境变量、硬编码、弱密钥。
- token 中的角色/权限是否可信，是否与服务端状态二次确认。

## 危险模式

| 模式 | 风险 |
|------|------|
| 只 Base64 decode payload | 完全未验证签名 |
| 允许 `alg=none` 或未固定算法 | algorithm none/confusion |
| RS/HS 混用 | 公钥可能被当作 HMAC 密钥 |
| 长期不过期 token | 失窃后长期有效 |
| 只信任 token 内 userId/role | 权限变更不生效或可伪造 |

## 误报防线

- 老版本 JWT 库不等于漏洞；需看代码是否使用危险 API。
- token 中有 role 不代表越权，需看服务端是否校验签名和权限来源。
- 缺少吊销机制通常是中低风险，除非有明确敏感场景或泄露路径。

## Gotchas

- `parseClaimsJwt` 与 `parseClaimsJws` 语义不同，前者不验证签名。
- `decode()` 常只是解码，不是验证。
- 共享密钥短、硬编码、复用默认值时要记录证据位置。
