# Apache Shiro 鉴权参考

只在项目存在 Shiro 依赖、`shiro.ini`、`shiro-spring.xml`、`SecurityUtils`、`@Requires*` 注解、Realm 或 Shiro Filter 时读取本文件。

## 必查点

- Shiro 版本和集成方式，配合 `VERSION_VULNS.md` 判断候选风险。
- Filter chain 定义顺序，尤其 `anon`、`authc`、`user`、`roles`、`perms`。
- Spring 集成时 Shiro 路径匹配与 Spring MVC 路由解析是否一致。
- 自定义 Realm 的认证、授权、缓存和角色/权限加载逻辑。
- RememberMe 配置、cipherKey、反序列化风险。

## 危险模式

| 模式 | 风险 |
|------|------|
| `/** = anon` 或宽泛 anon 在前 | 后续保护规则失效 |
| `/** = authc` 但敏感接口无 roles/perms | 仅认证，可能越权 |
| 自定义 Filter 使用原始 URI 做白名单 | 路径解析差异绕过 |
| Realm 只按用户名加载权限且缓存不刷新 | 权限变更不生效 |
| RememberMe 默认/硬编码密钥 | 反序列化或伪造风险 |

## 误报防线

- Shiro 版本命中 CVE 不等于漏洞确认；必须匹配官方公告的触发条件。
- `authc` 已能阻止未登录访问；若报告越权，需证明缺角色/权限/对象归属校验。
- `anon` 公开接口需结合敏感性，不是天然漏洞。

## Gotchas

- Filter chain 第一条匹配生效，顺序错误比单条规则更关键。
- `user` 与 `authc` 语义不同，RememberMe 用户可能被视为已识别但未完全认证。
- 注解鉴权依赖 AOP/代理，内部方法调用可能绕过注解。
