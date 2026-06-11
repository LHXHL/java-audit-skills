---
name: java-auth-audit
description: Use when the user asks to audit Java Web authentication or authorization behavior: route auth coverage, Shiro/Spring Security/JWT/session/filter/interceptor rules, auth bypass, privilege escalation, IDOR, or auth-related component versions. Do not use for route extraction only, dependency-only CVE scanning, SQL/XXE/upload/file-read/deserialization bugs, or generic security hardening.
---

# Java Auth Audit

## 当前定位

`java-auth-audit` 判断 Java Web 项目的“入口是否被正确鉴权、权限是否可绕过、对象访问是否越权”。它消费 `java-route-mapper` 的路由与参数清单，也可以在没有 route mapper 输出时独立扫描，但必须标注覆盖限制。

本 skill 不负责提取全量路由、不追踪非鉴权 sink、不把依赖版本命中直接判成可利用漏洞、不做泛化安全加固建议。

## 何时触发

用户意图包含以下任一项时触发：

- 审计 Shiro、Spring Security、JWT、Session、Filter、Interceptor、自定义鉴权。
- 判断路由是否公开、仅认证、受角色/权限保护、无鉴权或不确定。
- 分析鉴权绕过、路径匹配绕过、权限提升、水平/垂直越权、IDOR。
- 基于 route mapper 输出生成路由-鉴权映射。
- 检查鉴权组件版本是否命中已知认证/授权绕过条件。

典型说法：

- “检查这个项目有没有鉴权绕过。”
- “基于 route_mapper 给所有接口标注鉴权状态。”
- “分析 Shiro / Spring Security 配置是否能被绕过。”
- “看这些 `{id}` 接口有没有越权。”
- “检查 JWT 校验逻辑和 session 管理问题。”

## 何时不触发

相似但不应触发的任务：

- 只提取接口路径和参数：使用 `java-route-mapper`。
- 只扫描依赖 CVE：使用 `java-vuln-scanner`。
- SQL 注入、XXE、上传、文件读取、反序列化：使用对应专项 skill。
- 只追踪参数到 DAO/文件/XML/parser sink：使用 `java-route-tracer` 或专项 skill。
- 只问业务上“某功能应不应该开放”：没有代码层鉴权证据时不直接判漏洞。
- 密码策略、日志审计、限流、CORS/CSRF 通用加固：除非它直接影响认证/授权绕过。

## 成功标准

完成后必须能回答：

- 项目用了哪些鉴权层：网关/Filter/Interceptor/Shiro/Spring Security/方法注解/业务代码。
- 每条路由的鉴权状态是什么，依据来自哪条配置或代码。
- 每个风险是否有可达入口、绕过路径、后续拦截层分析和可利用前置条件。
- 越权结论是否有对象归属校验缺失证据。
- 组件版本命中是否满足配置和运行环境前提。
- 输出三文件是否完整互链：主报告、路由鉴权映射表、说明文档。

## 输入依赖

优先读取现有 `route_mapper/` 主索引和模块详情。缺失时：

- 可以独立扫描 Controller/Action/Servlet/WebService 和鉴权配置。
- 必须在 README 或主报告中标注“未使用 route_mapper，路由覆盖可能不完整”。
- 不得凭单个鉴权配置推断“全部路由均已覆盖”。

## 工作流

1. 确认源码路径、输出目录、是否存在 `route_mapper/`。
2. 识别鉴权组件和版本，按需读取 `VERSION_VULNS.md`。
3. 识别完整鉴权链路：Filter、Interceptor、框架配置、方法注解、业务权限校验。
4. 建立路由-鉴权映射：公开、受保护、仅认证、无鉴权、不确定。
5. 对可疑绕过点做数据流和多层拦截分析。
6. 对 IDOR/越权点确认对象归属校验是否缺失。
7. 生成三份输出文件并执行交付前校验。

## 按需读取的 references

- Shiro：`references/SHIRO.md`
- Spring Security：`references/SPRING_SECURITY.md`
- JWT：`references/JWT.md`
- Filter/Interceptor：`references/FILTER_INTERCEPTOR.md`
- 注解式鉴权：`references/ANNOTATION_AUTH.md`
- Session/Cookie：`references/SESSION_AUTH.md`
- 路径和协议绕过模式：`references/BYPASS_PATTERNS.md`
- URI 解析差异：`references/URI_PARSING_BYPASS.md`
- 鉴权组件版本库：`references/VERSION_VULNS.md`
- 需要反编译：`references/DECOMPILE_STRATEGY.md`
- 交付前检查：`references/VULNERABILITY_CHECKLIST.md`
- 输出模板：`references/OUTPUT_TEMPLATE_MAIN.md`、`references/OUTPUT_TEMPLATE_MAPPING.md`、`references/OUTPUT_TEMPLATE_README.md`
- 通用严重度：`../java-shared/SEVERITY_RATING.md`
- 通用输出规范：`../java-shared/OUTPUT_STANDARD.md`

## Hard Rules

### 1. 完整鉴权链路

不要只看一层。必须识别并串联：

- 容器/网关层路径处理。
- Filter 层登录检查和白名单。
- Interceptor 层 session/权限检查。
- Shiro/Spring Security/JWT 配置。
- 方法注解和业务代码中的对象归属校验。

绕过单层后若还有后续层有效拦截，不得报成“完全绕过”。

### 2. 路由映射覆盖

- 有 `route_mapper/` 时，映射表必须覆盖 route mapper 主索引中的全部路由。
- 没有 `route_mapper/` 时，必须标注覆盖限制和扫描依据。
- `无鉴权`、`公开`、`仅认证`、`受保护`、`不确定` 必须有证据位置。

### 3. 数据流确认

发现 `contains`、`startsWith`、后缀白名单、分号绕过、编码绕过等模式后，必须继续回答：

- 用于鉴权判断的 path 变量从哪里来。
- 绕过 payload 会进入哪个分支。
- 后续是否还有登录、角色、权限或对象归属校验。
- 绕过的是登录检查、权限检查、静态资源白名单还是业务校验。

只凭模式匹配不得直接定高危。

### 4. 越权证据

IDOR/水平越权必须至少有以下证据之一：

- 用户可控对象 ID 进入查询、更新、删除或下载。
- 缺少 owner/tenant/userId/role 校验。
- 校验使用了可控参数而非 session/currentUser。
- 管理接口只认证不鉴权。

仅出现 `{id}`、`userId`、`orderId` 不能直接判越权。

### 5. 组件版本条件

版本命中只说明“存在候选风险”。报告漏洞前必须确认：

- 实际加载组件和版本。
- 漏洞触发所需集成方式、匹配器、配置或运行环境。
- 受影响路由或鉴权链路是否使用该组件能力。

无法确认触发条件时标注“环境依赖/待验证”，不要写成已确认漏洞。

### 6. 反编译只在需要时做

源码完整时优先读源码。源码缺失、class-only、鉴权逻辑位于 JAR/class、或配置指向不可读类时，再按 `DECOMPILE_STRATEGY.md` 最小化反编译。

### 7. 三文件输出

必须生成：

- `{project_name}_auth_audit_{YYYYMMDD_HHMMSS}.md`
- `{project_name}_auth_mapping_{YYYYMMDD_HHMMSS}.md`
- `{project_name}_auth_README_{YYYYMMDD_HHMMSS}.md`

主报告写漏洞和修复；映射表写完整路由鉴权状态；README 写方法、范围、局限和验证说明。

## Gotchas

- `permitAll` 不总是漏洞，可能是公开接口；需要看敏感性。
- `authenticated()` 只代表登录，不代表角色/对象权限。
- Shiro/Spring Security 路径匹配器和 MVC 路由解析不一致时才有路径绕过价值。
- JWT 校验必须确认签名、算法白名单、过期时间、用户状态和吊销策略。
- 方法级注解可能因内部调用/AOP 代理失效。
- Filter 顺序错误可能让后续鉴权永远无法执行。
- `RememberMe`、Session、普通登录 Cookie 的安全问题要区分认证绕过、会话劫持和反序列化风险。
- 组件 CVE 与代码层鉴权绕过要分开编号，除非它们共享同一根因和修复点。

## Evals

### 正例：应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “基于 route_mapper 检查所有接口鉴权状态。” | 触发 | 明确是路由-鉴权映射 |
| “分析 Shiro `/** = authc` 和 `/admin/** = roles[admin]` 是否可绕过。” | 触发 | 鉴权配置和绕过判断 |
| “JWT 只解析 token 没校验签名，帮我审计。” | 触发 | 认证机制缺陷 |
| “这个订单接口传 userId，会不会水平越权？” | 触发 | IDOR/对象归属校验 |

### 反例：不应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “提取所有 Controller 路由和参数。” | 不触发 | route mapper 职责 |
| “pom 里有哪些 CVE？” | 不触发 | dependency-only 扫描 |
| “这个参数会不会 SQL 注入？” | 不触发 | SQL audit / tracer |
| “上传接口能不能传 JSP？” | 不触发 | file upload audit |

### 边界例

| 用户输入 | 预期 | 处理 |
|----------|------|------|
| “Spring Security 版本旧，有没有漏洞？” | 触发但不直接定漏洞 | 先查版本库，再确认配置和可达路径 |
| “接口没有角色注解。” | 触发但需分析 | 可能由 Filter/Shiro/全局规则保护 |
| “所有 `/api/**` 都 authenticated。” | 触发 | 标注仅认证，继续看敏感接口是否需要角色/归属校验 |

### 失败案例

| 失败表现 | 风险 | 修复方式 |
|----------|------|----------|
| 只看 Controller 注解，漏掉 Filter/Shiro 全局规则 | 大量误报无鉴权 | 先建完整鉴权链路 |
| 发现 `contains("/public")` 就报高危 | 误报 | 做变量流和后续拦截层分析 |
| 有 `{id}` 就报 IDOR | 误报 | 查 owner/currentUser/tenant 校验 |
| Shiro 版本命中 CVE 就报已确认 | 误报 | 确认 Spring 集成、路径匹配器和受影响路由 |
| 映射表缺少 route mapper 中的模块 | 漏审 | 以 route_mapper 主索引为覆盖基准 |
