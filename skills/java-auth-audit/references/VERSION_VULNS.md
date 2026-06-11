# 鉴权组件版本漏洞库

只在检测到鉴权组件依赖或用户明确要求版本风险判断时读取本文件。

## 使用规则

- 版本命中只产生“候选风险”，不能直接判定为已确认漏洞。
- 每条候选风险必须结合触发条件、实际配置、可达路由和运行环境确认。
- 来源优先级：官方安全公告 > GitHub Security Advisory > CVE/NVD > 项目 release notes。
- 本文件不是全量 CVE 数据库；未列出的组件要按来源链接继续核对。

## 版本识别来源

| 来源 | 说明 |
|------|------|
| JAR 文件名 | `shiro-core-1.11.0.jar`, `spring-security-web-6.2.2.jar` |
| Maven/Gradle | `pom.xml`, `build.gradle`, lock 文件 |
| JAR 内元数据 | `META-INF/MANIFEST.MF`, `META-INF/maven/**/pom.properties` |
| 运行配置 | Spring Boot dependency management、容器 lib、WEB-INF/lib |

## 核心条目

| 组件 | CVE/公告 | 影响版本 | 修复版本 | 触发条件 | 配置前提 | 来源 |
|------|----------|----------|----------|----------|----------|------|
| Apache Shiro | CVE-2026-48589 | `2.0-alpha` 到 `2.2.0`, `3.0.0-alpha-1` | `2.2.1`, `3.0.0-alpha-2` | 登录后 Referer redirect 目标可控 | 仅 shiro-jakarta-ee integration module | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2026-44598 | `2.0-alpha` 到 `2.1.0`, `3.0.0-alpha-1` | `2.2.0`, `3.0.0-alpha-2` | 登录后 saved request cookie 可导致 open redirect/SSRF | 仅 shiro-jakarta-ee integration module | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2026-43827 | `1.0` 到 `2.1.0`, `3.0.0-alpha-1` | `2.2.0`, `3.0.0-alpha-2` | 默认配置 session fixation | 使用 Shiro session 登录流程 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2026-43828 | `1.0` 到 `2.1.0`, `3.0.0-alpha-1` | `2.2.0`, `3.0.0-alpha-2` | 默认配置 Cookie 缺 Secure 属性 | Shiro-native session 或 RememberMe 管理器 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2026-23903 | `< 2.1.0` | `2.1.0` | 大小写变体可绕过静态文件过滤 | 静态文件位于大小写不敏感文件系统 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2026-23901 | `< 2.1.0` | `2.1.0` | 登录失败路径差异导致用户名枚举 | 本地或低延迟攻击更现实 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2023-46749 | `< 1.13.0`, `< 2.0.0-alpha-4` | `1.13.0`, `2.0.0-alpha-4` | path traversal 导致认证绕过候选 | 与 path rewriting 组合使用 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2023-46750 | `< 1.13.0`, `< 2.0.0-alpha-4` | `1.13.0`, `2.0.0-alpha-4` | form auth open redirect | 使用 form authentication | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2023-34478 | `< 1.12.0`, `< 2.0.0-alpha-3` | `1.12.0`, `2.0.0-alpha-3` | path traversal 认证绕过候选 | 与非规范化请求路由框架组合 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2023-22602 | `< 1.11.0` | `1.11.0` | 认证绕过 | 受影响的 Web/Spring 路径匹配场景 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2022-32532 | `< 1.9.1` | `1.9.1` | RegexRequestMatcher 绕过 | 使用受影响的正则匹配 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2021-41303 | `< 1.8.0` | `1.8.0` | 路径规范化绕过 | Web 路径鉴权 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2020-17523 | `< 1.7.1` | `1.7.1` | 认证绕过 | Shiro + Spring 集成 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2020-13933 | `< 1.6.0` | `1.6.0` | 认证绕过 | Web 路径鉴权 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2020-11989 | `< 1.5.3` | `1.5.3` | 认证绕过 | Shiro + Spring 集成 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2020-1957 | `< 1.5.2` | `1.5.2` | 认证绕过 | Spring 动态控制器场景 | https://shiro.apache.org/security-reports.html |
| Apache Shiro | CVE-2016-4437 | 默认/硬编码 RememberMe cipherKey | 无单一版本修复 | RememberMe 反序列化 | 使用默认或泄露密钥 | https://shiro.apache.org/security-reports.html |
| Spring Security | CVE-2022-31692 | 见官方公告 | `5.7.5` / `5.6.9` 等分支修复 | forward/include 授权绕过 | 使用受影响请求转发场景 | https://spring.io/security/ |
| Spring Security | CVE-2022-22978 | `5.5.x < 5.5.7`, `5.6.x < 5.6.4`, `5.4.x < 5.4.11` | `5.5.7`, `5.6.4`, `5.4.11` | RegexRequestMatcher 绕过 | 使用正则匹配且 `.` 语义受影响 | https://spring.io/security/ |
| Spring Security | CVE-2018-1199 | 见官方公告 | 见官方公告 | 路径参数处理绕过候选 | 使用受影响路径匹配 | https://spring.io/security/ |
| JJWT | 安全建议 | `< 0.10.0` | `0.10.0+`，建议使用当前稳定版 | 旧 API 易误用 | 代码使用不安全 parse/decode 方式 | https://github.com/jwtk/jjwt |
| Auth0 java-jwt | 安全建议 | 旧版需复核 | 见官方 release/advisory | JWT 算法/验证误用候选 | 使用不安全 verifier 配置 | https://github.com/auth0/java-jwt/security/advisories |
| pac4j | GitHub Advisory | 见项目 advisory | 见项目 advisory | 认证/授权绕过候选 | 取决于客户端和 profile 配置 | https://github.com/pac4j/pac4j/security/advisories |
| Sa-Token | 项目安全公告/Issue | 需按项目公告复核 | 见项目公告 | Token/session 鉴权候选 | 取决于拦截器和路由配置 | https://github.com/dromara/Sa-Token/security/advisories |
| Spring Authorization Server | Spring Security 公告/GitHub Advisory | 需按公告复核 | 见公告 | OAuth2/OIDC 授权候选 | 取决于 authorization server 配置 | https://github.com/spring-projects/spring-authorization-server/security/advisories |
| Keycloak adapters | Keycloak Security Advisories | 需按公告复核 | 见公告 | Adapter/OIDC 认证候选 | 取决于 adapter 版本和部署方式 | https://www.keycloak.org/security |

## 年度复核提醒

- Spring Security 2026 新公告不得凭二手资料写入本地条目；实现时需打开 `https://spring.io/security/` 或具体 CVE 页面确认影响版本、修复版本和触发配置。
- Apache Shiro 2026 条目已按官方 `security-reports.html` 页面列入，但仍需结合项目是否使用对应模块或默认配置判断。

## 判断模板

对每个命中版本，输出时必须补齐：

```markdown
组件: {component}
当前版本: {version}
候选风险: {CVE/公告}
影响版本: {range}
修复版本: {fixed}
触发条件: {condition}
项目是否满足触发条件: 是/否/未知 + 证据
受影响入口: {route 或 "未确认"}
结论: 已确认 / 待验证 / 环境依赖 / 不可利用
来源: {url}
```

## 误报防线

- Shiro/Spring Security 的路径绕过类 CVE 必须确认项目确实使用对应 Web 集成和路径匹配器。
- JWT 库旧版本通常是“误用风险”，必须看代码 API 调用。
- Keycloak adapter 与 Keycloak server 漏洞不要混淆。
- Sa-Token/Spring Authorization Server 若没有本地条目，按官方 advisory 复核，不要凭组件名编 CVE。
- 同一组件多个 JAR 版本冲突时，以实际运行 classpath 为准。
