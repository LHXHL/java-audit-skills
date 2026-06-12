# Apache Shiro 鉴权参考

只在项目存在 Shiro 依赖、`shiro.ini`、`shiro-spring.xml`、`SecurityUtils`、`@Requires*` 注解、Realm 或 Shiro Filter 时读取本文件。

## 必查点

- 集成方式：Servlet Filter、Spring Bean、INI、XML、注解、Realm。
- Filter chain 定义顺序，尤其 `anon`、`authc`、`user`、`roles`、`perms`。
- Shiro 路径匹配与 Spring MVC、Struts、Servlet 路由解析是否一致。
- 自定义 Realm 的认证、授权、缓存和角色/权限加载逻辑。
- RememberMe 是否等同认证，cipherKey 或序列化问题交由反序列化/组件专项复核。
- 版本只作为链路背景；版本风险边界见 `VERSION_VULNS.md`。

## 危险模式

| 模式 | 风险判断 |
|------|----------|
| 宽泛 `anon` 早于敏感规则 | 可能让敏感路径公开，需确认后续无有效拦截 |
| `authc` 覆盖管理接口但无 `roles/perms` | 可能仅认证不授权，需确认敏感功能和角色缺口 |
| `user` 用于敏感操作 | RememberMe 用户可能被当作已识别用户 |
| Realm 只按用户名加载权限且不刷新 | 权限变更可能不生效，需结合业务影响 |
| 自定义 Filter 使用原始 URI 白名单 | 可能出现路径解析差异绕过 |

## 误报防线

- Shiro 版本旧不等于 auth 漏洞确认。
- `anon`、登录页、静态资源、健康检查先判断是否应公开。
- `authc` 可以阻止未登录；若报告越权，必须证明缺角色、权限或对象归属校验。
- 注解鉴权依赖 AOP/代理；未确认代理生效时标 `待验证`。

## 输出要求

- 只有具体入口因 Shiro chain、Realm、注解或路径解析问题形成认证/授权缺口时，才进入主报告。
- 需要 Burp Suite 请求时，路径和参数必须来自真实 route 或配置，不按 chain pattern 猜业务路径。
