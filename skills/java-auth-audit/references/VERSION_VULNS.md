# 组件版本边界

只在鉴权审计过程中识别到 Shiro、Spring Security、JWT、OAuth2、SSO、Sa-Token、Keycloak adapter 等组件版本时读取本文件。本文件不是漏洞库，不维护本地 CVE 表。

## 边界

- 版本风险、公告匹配、修复版本和组件升级建议属于 `java-vuln-scanner`。
- `java-auth-audit` 只记录组件如何参与认证/授权链路，以及它的配置是否影响当前入口。
- 不凭版本号生成 `确认漏洞`、`条件成立`、Burp Suite 请求或 payload。
- 不编造 CVE、CVSS、修复版本、受影响范围或利用链。

## 在 auth 报告中的写法

可以写：

| 内容 | 示例 |
|------|------|
| 链路事实 | `WEB-INF/lib/shiro-web-*.jar` 存在，`shiroFilter` 覆盖 `/api/*` |
| 配置事实 | `SecurityFilterChain` 中 `/admin/**` 使用 `authenticated()` |
| 待复核事项 | 组件版本较旧，建议交给组件扫描专项按官方公告复核 |

不要写：

| 禁止内容 | 原因 |
|----------|------|
| “命中某 CVE，确认漏洞” | 版本命中缺项目触发条件 |
| “修复到 x.y.z” | auth skill 不维护修复版本 |
| “CVSS 分数” | 需要漏洞公告和环境评分，不能编造 |
| “组件版本 payload” | 组件公告不等于本项目可复现请求 |

## 何时仍可进入 auth 主报告

只有当组件配置或用法在本项目中形成认证/授权缺陷时，才按普通 auth 风险处理。例如：

- Spring Security 规则明确把敏感业务路径 `permitAll`。
- Shiro chain 顺序导致敏感路径命中 `anon`，且后续无有效拦截。
- JWT 代码只 decode claim 不 verify 签名，且 claim 决定当前用户或角色。
- Session fixation 由本项目登录流程造成，且攻击者可设置并复用受害者登录后的 session。

这类结论必须基于本项目代码或配置，不基于组件版本表。
