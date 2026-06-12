---
name: java-auth-audit
description: 当用户要求审计 Java Web 认证、授权、路由鉴权覆盖、Filter/Interceptor/Shiro/Spring Security/JWT/Session 规则、鉴权绕过、权限提升、IDOR 或水平/垂直越权时使用；只做路由提取、依赖 CVE、SQL/XXE/上传/文件读取/反序列化、Cookie 加固或通用安全基线时不要使用。
---

# Java Auth Audit

## 当前定位

`java-auth-audit` 判断 Java Web 项目的入口是否被正确认证、授权是否可绕过、对象访问是否越权。它可以消费 `java-route-mapper` 的路由清单，也可以在没有上游输出时独立扫描配置、Controller/Action/Servlet/WebService 和鉴权类，但必须说明覆盖限制。

本 skill 不做全量路由提取、不做组件 CVE 扫描、不把 Cookie 属性、session timeout、密码策略、CSRF/CORS、`global-allowed-methods` 等加固项包装成漏洞结论。确认漏洞或条件成立的认证/授权风险必须能给开发单位复核：真实入口、证据链、Burp Suite 请求、payload/角色/对象变体和限制说明都要完整。

## 触发条件

- 用户要求审计认证、授权、登录绕过、未授权访问、权限提升、IDOR、水平/垂直越权。
- 用户要求判断路由是公开、仅认证、受保护、无鉴权还是不确定。
- 用户要求分析 Shiro、Spring Security、JWT、Session、Filter、Interceptor、方法注解、自定义权限逻辑。
- 用户提供 route mapper 输出，要求生成路由-鉴权映射。

## 不触发条件

- 只提取路由和参数：交给 `java-route-mapper`。
- 只查依赖版本、CVE、修复版本或组件升级：交给 `java-vuln-scanner`。
- SQL 注入、XXE、上传、文件读取、反序列化：交给对应专项 skill。
- 只追踪参数到 sink、不判断认证/授权：交给 `java-route-tracer` 或专项 skill。
- Cookie 属性、明文记住密码、session timeout、CSRF/CORS、限流、日志审计、密码策略：默认写 README 加固建议；除非它们直接造成认证绕过、授权绕过或对象越权。

## 成功标准

- 识别完整鉴权链路：网关/Filter/Interceptor/框架配置/方法注解/业务权限/对象归属校验。
- 每条已知路由都有鉴权状态和证据位置；没有 route mapper 时说明覆盖限制。
- 风险结论只基于完整证据链：入口可达、鉴权缺口、后续拦截缺失、敏感影响或对象归属校验缺失。
- `确认漏洞` 和 `条件成立` 项包含可复核 Burp Suite 请求与 payload/角色/对象变体；`待验证`、`不可确认`、`非漏洞` 不输出可复制请求。
- 输出三文件互链，且不包含 CVE、CVSS、修复版本、输出自检、技能源校验、Claude 运行状态或测试提示词。

## 输入和输出

优先读取 `route_mapper/` 主索引和模块详情。缺失时可以独立扫描，但必须在 README 标注“未使用 route mapper，路由覆盖可能不完整”。

必须输出三份文件：

- `{project_name}_auth_audit_{YYYYMMDD_HHMMSS}.md`
- `{project_name}_auth_mapping_{YYYYMMDD_HHMMSS}.md`
- `{project_name}_auth_README_{YYYYMMDD_HHMMSS}.md`

文件名必须包含完整 `YYYYMMDD_HHMMSS`。主报告只写确认漏洞/条件成立风险详情；映射表写路由鉴权状态；README 写方法、范围、局限、待验证项和加固建议。

## 工作流

1. 确认源码路径、输出目录、是否存在 route mapper 输出。
2. 扫描入口：`web.xml`、`struts*.xml`、Spring MVC 配置、`jaxws:endpoint`、Controller/Action/Servlet/Filter/Listener、注解、JSP/静态映射。
3. 串联鉴权链路：Filter、Interceptor、框架配置、方法注解、业务权限和对象归属校验。
4. 建立路由鉴权映射：公开、受保护、仅认证、无鉴权、待验证、不可确认、非漏洞。
5. 只对完整证据链风险写主报告；证据缺口写映射表/README，不写 Burp 请求。
6. 确认/条件成立项读取 `references/VALIDATION_MATERIALS.md`，生成 Burp Suite 请求和 payload/角色/对象变体。
7. 生成三文件后，可运行 `scripts/validate_auth_output.py <输出目录>` 做硬边界检查，再人工检查风险证据。

## 按需读取的 references

- Shiro：`references/SHIRO.md`
- Spring Security：`references/SPRING_SECURITY.md`
- JWT：`references/JWT.md`
- Filter/Interceptor：`references/FILTER_INTERCEPTOR.md`
- 注解式鉴权：`references/ANNOTATION_AUTH.md`
- Session/Cookie：`references/SESSION_AUTH.md`
- 路径和协议绕过：`references/BYPASS_PATTERNS.md`、`references/URI_PARSING_BYPASS.md`
- 组件版本边界：`references/VERSION_VULNS.md`
- 反编译策略：`references/DECOMPILE_STRATEGY.md`
- 验证材料和 payload：`references/VALIDATION_MATERIALS.md`
- 交付检查：`references/VULNERABILITY_CHECKLIST.md`
- 输出模板：`references/OUTPUT_TEMPLATE_MAIN.md`、`references/OUTPUT_TEMPLATE_MAPPING.md`、`references/OUTPUT_TEMPLATE_README.md`

不要为本 skill 读取 `../java-shared/OUTPUT_STANDARD.md` 或 `../java-shared/SEVERITY_RATING.md` 生成报告；它们的旧 CVSS/自检结构与本 skill 新版模板冲突。

## Hard Rules

### 1. 完整链路优先

不要只看一层。必须判断请求是否经过网关/Filter/Interceptor/Shiro/Spring Security/JWT/注解/业务代码/对象归属校验。绕过单层后若还有后续有效拦截，不得写成漏洞。

### 2. 状态定义

- `确认漏洞`：静态代码证据或授权测试证据完整，入口、鉴权缺口、后续拦截缺失和影响均成立。
- `条件成立`：代码证据完整，只剩明确外部条件，例如部署路径、网络暴露面、角色/对象数据或配置开关；不得用来承载“内部实现未知”。
- `待验证`：存在候选模式，但缺方法体、父类/AOP、运行时映射、角色或对象归属证据。
- `不可确认`：关键源码/配置/反编译结果缺失，无法判断。
- `非漏洞`：已确认有有效认证、授权或对象归属校验，或入口不可达/应公开且无敏感影响。

### 3. 主报告升格门槛

`确认漏洞` 和 `条件成立` 项必须同时具备：

- 真实 HTTP/SOAP/RPC 入口和方法。
- 证据位置：配置、源码、反编译文件或 class/JAR 来源。
- 鉴权链路和后续拦截层结论。
- 敏感影响，或对象归属/角色校验缺失证据。
- Burp Suite 请求、payload/角色/对象变体、授权验证说明和修复建议。

出现 `需反编译`、`未反编译`、`待补证`、`内部实现未知`、`后续拦截未知`、`BaseController/AOP 是否鉴权未知`、`可能`、`候选`、`无法确认` 时，不能写进主报告风险详情。

`条件成立` 只允许承载外部条件已经明确的风险，例如部署路径、网络暴露面、测试账号角色、对象数据或配置开关。它不是“待验证”的替代状态；如果风险成立依赖某个未反编译类、父类、AOP、Interceptor、Filter、网关或运行时路由的内部实现，必须写为 `待验证` 或 `不可确认`，并放入映射表/README。

### 4. Burp 和 Payload 边界

- 只有确认漏洞和条件成立项输出 Burp Suite 请求与 payload/变体。
- Burp 请求必须来自真实路由、HTTP 方法、参数名、Content-Type、Cookie/Token/CSRF 位置；不能按类名或方法名猜路径。
- 请求中的 Cookie、JWT、CSRF、用户 ID、对象 ID、租户 ID 使用占位符。
- 不输出真实凭据、真实用户数据、生产环境请求、批量利用脚本、暴力枚举或破坏性操作。
- payload 只验证当前风险，不夹带尚未证实的 IDOR、方法绕过、路径绕过或批量遍历变体。

### 5. 组件和加固项边界

- 组件版本、CVE、CVSS、修复版本交给 `java-vuln-scanner`，auth 报告最多写“建议交给组件扫描专项复核”。
- 明文记住密码、Cookie 属性、session timeout、CSRF/CORS、限流、日志审计、密码策略、`global-allowed-methods regex:.*` 默认放 README 加固建议。
- 只有这些问题直接导致登录绕过、授权绕过、会话固定可被攻击者设置并复用，或对象越权时，才按 auth 风险处理。
- 明文密码 Cookie、浏览器“记住密码”、Cookie 缺 `HttpOnly/Secure/SameSite` 不能作为主报告风险；除非 Cookie 本身就是服务端认可的登录态且可被攻击者伪造/复用绕过认证。

### 6. 分组规则

同一 AUTH 编号只能合并同根因、同证据等级、同修复点的入口。已反编译确认入口和未反编译/待补证入口必须拆开；后者放映射表或 README。

REST Controller 继承父类、Servlet 入口只定位到 class 文件、自定义 Servlet/Filter/Interceptor 只有类名但没有方法体时，必须先反编译父类或目标类。未反编译前不得把该入口写入主报告，也不得和已确认入口合并。

## Gotchas

- `permitAll`、`anon`、登录页、健康检查和静态资源不是天然漏洞；先判断敏感性。
- `authenticated()` 只代表登录，不代表角色/对象权限。
- Filter mapping 不覆盖某路径，不等于目标 Servlet/Controller 内部无鉴权。
- Spring MVC REST 要确认 HandlerInterceptor、AOP、父类和注解是否生效。
- Shiro/Spring Security 路径匹配器与 MVC/Servlet 解析不一致时，才有路径绕过价值。
- 有 `{id}`、`userId`、`orderId` 不等于 IDOR；必须查 owner/tenant/currentUser 校验。
- 方法级注解可能因内部调用/AOP 代理失效。
- 反编译证据要标注来源；反编译失败只说明待验证，不是漏洞。

## Evals

### 正例

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “检查这个项目有没有鉴权绕过。” | 触发 | 认证/授权风险 |
| “基于 route_mapper 标注所有接口鉴权状态。” | 触发 | 路由-鉴权映射 |
| “这个订单接口传 userId，会不会水平越权？” | 触发 | IDOR |
| “JWT 只 decode 没验签，审一下。” | 触发 | 认证机制缺陷 |

### 反例

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “提取所有 Controller 路由和参数。” | 不触发 | route mapper 职责 |
| “pom 里有哪些 CVE？” | 不触发 | 组件扫描 |
| “这个参数会不会 SQL 注入？” | 不触发 | SQL 专项 |
| “上传接口能不能传 JSP？” | 不触发 | 文件上传专项 |

### 边界例和失败案例

| 场景 | 正确处理 |
|------|----------|
| Spring Security 版本旧 | 交给组件扫描；auth 只记录链路事实 |
| 只有外层 Filter 不覆盖 REST，但父类/AOP 未确认 | 待验证，不输出 Burp |
| 明文密码 Cookie | README 加固建议，除非能证明直接认证绕过 |
| `global-allowed-methods regex:.*` | 攻击面建议，找到具体敏感 public 方法和鉴权缺口后再升级 |
| 确认漏洞缺少 Burp/payload | 不合格，补齐验证材料 |
| 待验证项输出 Burp 请求 | 不合格，会把候选包装成漏洞 |
