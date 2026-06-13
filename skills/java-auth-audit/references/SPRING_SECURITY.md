# Spring Security 鉴权参考

只在项目存在 Spring Security 依赖、`SecurityFilterChain`、`WebSecurityConfigurerAdapter`、`@EnableMethodSecurity`、`@PreAuthorize`、OAuth2 Resource Server 或 Bearer Token 配置时读取本文件。

## 必查点

- 多个 `SecurityFilterChain` 的 matcher、order 和覆盖范围。
- `requestMatchers`、`mvcMatchers`、`antMatchers`、`regexMatchers` 的匹配语义。
- `permitAll`、`authenticated`、`hasRole`、`hasAuthority`、`access` 的路径范围。
- `web.ignoring()` 是否排除了业务路径。
- 方法级安全是否启用，注解是否通过代理生效。
- CSRF、CORS、RememberMe、OAuth2/JWT 只在影响认证/授权链路时作为风险证据。
- 版本只作为链路背景；版本风险边界见 `VERSION_VULNS.md`。

## 危险模式

| 模式 | 风险判断 |
|------|----------|
| 宽泛 `permitAll` 覆盖敏感路径 | 可能公开敏感入口，需确认敏感性和后续拦截 |
| `authenticated()` 保护管理接口 | 仅登录，不代表有角色/权限控制 |
| `web.ignoring()` 忽略业务路径 | 绕过整个 Security Filter Chain，需确认后续鉴权 |
| 方法级注解未启用 | 注解可能只是标记，不产生拦截 |
| `regexMatchers` 正则过宽 | 可能因路径解析差异绕过 |

## 误报防线

- `permitAll` 常用于登录、静态资源、健康检查，不是天然漏洞。
- `authenticated()` 不能直接写成越权；必须证明入口需要更高权限或对象归属校验。
- `ROLE_` 前缀、权限命名和数据库角色映射要一起看。
- 组件版本风险交给专项扫描，不在 auth 报告里写修复版本或公告结论。

## 输出要求

- 进入主报告前必须说明命中的 filter chain、matcher、入口和后续方法级/业务层校验。
- 如果 BaseController、AOP、父类或运行时 matcher 未确认，写入映射表或 README，不生成 Burp Suite 请求。
