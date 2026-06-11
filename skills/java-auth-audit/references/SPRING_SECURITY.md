# Spring Security 鉴权参考

只在项目存在 Spring Security 依赖、`SecurityFilterChain`、`WebSecurityConfigurerAdapter`、`@EnableMethodSecurity`、`@PreAuthorize` 或 `BearerToken` 配置时读取本文件。

## 必查点

- Spring Security 版本，配合 `VERSION_VULNS.md` 判断候选风险。
- 多个 `SecurityFilterChain` 的 matcher 和 order。
- `requestMatchers` / `mvcMatchers` / `antMatchers` / `regexMatchers` 的匹配语义。
- `permitAll`、`authenticated`、`hasRole`、`hasAuthority`、`access` 的覆盖路径。
- 方法级安全是否启用，注解是否通过代理生效。
- CSRF、CORS、RememberMe、OAuth2 Resource Server/JWT 配置是否影响认证链路。

## 危险模式

| 模式 | 风险 |
|------|------|
| 宽泛 `permitAll` 在敏感 matcher 之前 | 敏感路径公开 |
| `authenticated()` 保护管理接口 | 仅登录，无角色限制 |
| `regexMatchers` 使用不严谨正则 | 换行/编码绕过 |
| `web.ignoring()` 忽略业务路径 | 绕过整个过滤链 |
| 方法级注解未启用或内部调用 | 注解不生效 |

## 误报防线

- 新版 DSL 中 matcher 顺序和 filter chain order 都要看，不能只看单行配置。
- `permitAll` 可能用于登录、健康检查、静态资源；需要路由敏感性。
- 组件 CVE 需确认使用了受影响 matcher、filter 或配置。

## Gotchas

- `web.ignoring()` 比 `permitAll()` 更危险，因为它绕过整个 Security Filter Chain。
- MVC 路径匹配和 Servlet 原始路径可能不同，路径绕过要比较两边解析结果。
- `ROLE_` 前缀会影响 `hasRole` 与数据库权限值匹配。
