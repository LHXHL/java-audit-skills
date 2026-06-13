# JWT 鉴权参考

只在项目存在 JWT 库、Bearer Token、`JwtParser`、`JWTVerifier`、OAuth2 Resource Server 或自定义 token 校验时读取本文件。

## 必查点

- 使用的库和 API：JJWT、Auth0 java-jwt、Nimbus、Spring Security OAuth2。
- 是否验证签名，是否固定允许算法，是否区分 decode 与 verify。
- 是否校验 `exp`、`nbf`、`iss`、`aud`、用户状态和 token 吊销。
- 密钥来源：配置、环境变量、硬编码、弱密钥。
- token 中的用户、角色、权限、租户是否被服务端重新确认。
- 版本只作为链路背景；组件版本风险边界见 `VERSION_VULNS.md`。

## 危险模式

| 模式 | 风险判断 |
|------|----------|
| 只 Base64 decode payload | 若 claim 决定身份或权限，可形成认证绕过 |
| 使用 `parseClaimsJwt` 处理受保护 token | 可能未验证签名 |
| 允许 `alg=none` 或未固定算法 | 可能接受伪造 token |
| RS/HS 混用 | 公钥可能被当作 HMAC 密钥 |
| 只信任 token 内 `userId`、`role`、`tenantId` | 可能权限提升或对象越权 |
| 长期不过期或缺吊销 | 通常写 README 加固建议；除非结合泄露路径或敏感影响 |

## 误报防线

- 老版本 JWT 库不等于 auth 漏洞确认。
- token 中有 role 不代表越权；必须看服务端是否验证签名和权限来源。
- 缺少吊销机制、过期时间过长、密钥轮换不足通常不是主报告风险，除非能证明直接影响认证/授权结果。
- 无真实 token、密钥或运行时配置时，不生成可复制请求。

## 输出要求

- 进入主报告前必须说明 claim 如何影响当前用户、角色、租户或对象范围。
- Burp Suite 请求只使用占位符 token，并说明对照组、测试组和否定结论的响应。
- 不生成签名伪造脚本，不写真实密钥、真实 token 或生产请求。

## Gotchas

- `decode()` 常只是解码，不是验证。
- `parseClaimsJwt` 与 `parseClaimsJws` 语义不同。
- OAuth2 Resource Server 可能在框架层验证签名，不能只看业务代码没有 verify 就下结论。
