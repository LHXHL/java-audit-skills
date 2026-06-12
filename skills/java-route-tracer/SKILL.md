---
name: java-route-tracer
description: 当用户要求从已知 Java Web 路由、入口方法或 pipeline 批次追踪参数调用链到 SQL/FILE/XML/COMMAND/HTTP/LDAP/EXPRESSION/DESERIALIZE/RESPONSE 等 sink，并输出可控性、分支条件和证据时使用；只提取路由、判断具体漏洞、鉴权审计或依赖 CVE 扫描时不要使用。
---

# Java Route Tracer

## 当前定位

`java-route-tracer` 是 Java 审计技能集中的“调用链证据层”。它从一个已知 Web 入口出发，回答：

- 请求从哪个路由或入口方法进入。
- 用户参数在 Controller/Action/Servlet/WebService、Service、DAO、Util、Mapper 等层之间如何传递、改名、转换或覆盖。
- 参数是否到达敏感 sink，sink 类型和代码位置是什么。
- 到达 sink 前需要满足哪些分支条件。
- 参数在 sink 处是完全可控、条件可控、受限可控、不可控还是未知。

它输出的是下游专项审计的证据，不直接下漏洞结论。

上游通常来自：

- `java-route-mapper` 的路由、参数、入口位置。
- `java-auth-audit` 或 pipeline `cross_analysis/` 提供的鉴权状态和风险等级。
- 用户直接指定的路由、类方法、批次清单。

下游通常由以下 skill 或 pipeline 阶段读取：

- `java-sql-audit`
- `java-xxe-audit`
- `java-file-upload-audit`
- `java-file-read-audit`
- `java-deserialization-audit`
- `java-audit-pipeline` 阶段4的 agent-6x

## 何时触发

用户意图包含以下任一项时触发：

- 追踪某个 Java Web 路由从入口到 DAO、文件、XML、反序列化、命令、HTTP 请求、响应输出等 sink 的调用链。
- 基于 route mapper 输出继续分析某条或一批路由的参数流向。
- 判断某个请求参数是否到达指定 sink，或在到达前是否被覆盖、过滤、白名单限制。
- 需要为 SQL/XXE/上传/文件读取/反序列化等专项审计准备可复用调用链证据。
- pipeline 中 `agent-5-N` 被分配一批高危路由，需要生成 `route_tracer/` 报告。

典型说法：

- “追踪 `/api/order/list` 的 `pageJson.orderBy` 到 SQL 执行点。”
- “基于 route_mapper，对这批 P0 路由生成调用链报告。”
- “这个上传接口的 `fileName` 经过哪些方法传到 `transferTo`？”
- “只看调用链和可控性，不要先判漏洞。”
- “agent-5-2 处理 trace_batch_plan 里的这些路由。”

## 何时不触发

相似但不应触发的任务：

- 只要求提取全部路由、参数或 WebService 方法清单：使用 `java-route-mapper`。
- 只要求判断 SQL 注入、XXE、上传、文件读取或反序列化漏洞是否成立：使用对应专项 skill；本 skill 可作为其上游证据。
- 只要求鉴权覆盖、越权、认证绕过：使用 `java-auth-audit`。
- 只扫描依赖版本和 CVE：使用 `java-vuln-scanner`。
- 用户没有给出路由、入口方法、route mapper 输出或可定位范围，只说“分析整个项目所有调用链”：先切换到 route mapper 或要求明确范围。
- 纯内部方法、定时任务、MQ/RPC 入口的追踪，除非用户明确要求把它作为非 HTTP 入口证据；默认不把它伪装成 Web 路由。

边界例：

- “这个接口有没有 SQL 注入？”不直接触发本 skill；若缺少调用链证据，先说明应由 `java-route-tracer` 产出证据，再交给 `java-sql-audit` 判定。
- “列出 `/api/**` 所有接口。”不触发本 skill，使用 `java-route-mapper`。
- “追踪 `/ws/userService` 下所有 SOAP 方法参数流向。”触发本 skill，但只追踪配置真实暴露的方法，不把实现类所有 public helper 都当入口。

## 成功标准

合格输出必须让下游审计员可以不重新猜入口，直接回答“哪个参数、经过哪条链、到达哪个 sink、受什么条件限制”。

最低要求：

- 每条被分配路由或入口都有报告；多方法入口必须有索引。
- 入口定位有证据：来自 route mapper、配置、注解、web.xml、struts.xml、JAX-RS、WebService endpoint 或用户指定方法。
- HTTP 请求模板、参数结构、入口类方法、调用层级、变量名变化、关键代码位置完整。
- sink 类型、sink 位置、参数到达关系、可控性结论和分支条件清楚。
- pipeline 输入中带有鉴权状态时，报告必须原样透传；未提供时明确写“未提供”，不得自行鉴权。
- 不把“参数到达危险 sink”写成“漏洞已确认”；漏洞结论交给下游专项 skill。
- 输出文件不含 `【填写】`、`${...}`、`...` 省略占位或臆造代码位置。
- 如果只追到 Manager/Service/DAO 接口调用，但实现类源码或反编译结果缺失，不得把该调用推断成 SQL/FILE/XML 等 sink；只能标记为 `UNCONFIRMED` 并列入“仍需确认”。
- 每个报告文件本身必须包含 `## 输出自检` 章节；终端最终响应里的自检不能替代文件内自检。

## 输入与模式判断

先判断执行模式：

| 模式 | 触发条件 | 输出责任 |
|------|----------|----------|
| Standalone single-route | 用户指定一个路由或入口方法 | 为该路由生成单方法报告，必要时生成多方法索引 |
| Standalone batch | 用户给出多个路由、route mapper 文件或清单 | 逐条生成报告，最后写批次覆盖摘要 |
| Pipeline worker | prompt 中出现 `agent-5-N`、`trace_batch_plan`、`batch_id`、已创建输出目录 | 只处理本批次路由，只写指定 `route_tracer/` 子目录 |
| Evidence refresh | 用户要求复查某个旧报告 | 读取旧报告与源码，更新该路由报告并标注变化 |

如果缺少源码路径、输出目录或入口定位信息，且无法从当前仓库或 route mapper 输出推导，先停止并要求补齐。不要自行扩大到全项目扫描。

## 工作流

1. 确认模式、源码路径、输出根目录、分配路由清单和是否存在 route mapper 输出。
2. 优先读取 route mapper 主索引和模块详情；没有时按实际框架配置定位入口，必须标注覆盖限制。
3. 识别入口真实方法。多方法或动态入口按 `references/multi-method-tracing.md` 处理。
4. 从入口开始逐层追踪参数传递、变量改名、DTO/JSON/XML 映射、封装方法、继承和接口实现。
5. 标记 sink 类型与位置。sink 类型和可控性判定按 `references/CONTROLLABILITY_ANALYSIS.md`。
6. 分析参数覆盖、校验、白名单、黑名单、规范化、提前返回和异常路径。
7. 分支条件按 `references/BRANCH_TRACING.md` 输出到报告。
8. 按模板写入报告和索引文件，并执行输出自检。

## 按需读取的 references

- 多入口和多方法展开：`references/multi-method-tracing.md`
- 参数可控性、sink 分类：`references/CONTROLLABILITY_ANALYSIS.md`
- 分支和提前退出：`references/BRANCH_TRACING.md`
- 完整报告模板：`references/OUTPUT_TEMPLATE_FULL.md`
- 简化报告模板：`references/OUTPUT_TEMPLATE_SIMPLE.md`
- 多方法索引模板：`references/OUTPUT_TEMPLATE_INDEX.md`
- 需要反编译：`../java-shared/DECOMPILE_STRATEGY.md`
- 通用输出规范：`../java-shared/OUTPUT_STANDARD.md`

## Hard Rules

### 1. 只给证据，不替专项 skill 下结论

允许写：

- “`pageJson.orderBy` 到达 `AbstractDao.findSql` 的 SQL 拼接点。”
- “参数在非空时完全可控；为空时被默认值覆盖。”
- “该路径需要满足 `status == enabled` 分支。”

禁止写：

- “确认 SQL 注入高危漏洞。”
- “CVSS 9.8。”
- “可直接 RCE。”
- 没有下游专项审计支持的 PoC、payload 或修复版本。

### 2. 入口必须真实可达

每条调用链都必须先绑定真实入口：

- Spring MVC: 类级和方法级 mapping 组合。
- Struts2: package namespace、action name、method、通配符实例。
- Servlet: web.xml 或 `@WebServlet` 的 url-pattern 与 `doGet`/`doPost` 等方法。
- JAX-RS: `ApplicationPath`、类级和方法级 `@Path`、HTTP 方法注解。
- WebService: 配置或注解暴露的 endpoint address 与 operation。

找不到入口时，报告为“入口未定位”，不要把内部 helper 方法写成 Web 路由。

### 3. 调用链不能跳层

必须记录每一层的文件位置、类名、方法签名、关键调用语句和参数传递关系。接口、抽象类、父类、Mapper XML、工具类、反射分发都要追到真实实现或明确标注无法确认原因。

关键代码片段必须是真实片段或准确摘录，不得用 `...`、`省略`、`同上`、`后续代码` 代替。若代码太长，只摘录与参数传递或分支相关的真实语句，并在说明列用自然语言交代上下文。

### 4. 可控性必须考虑覆盖和校验

不要只因为参数名出现在 sink 附近就判完全可控。必须检查：

- 是否被硬编码覆盖。
- 是否被默认值覆盖。
- 是否只允许白名单值。
- 是否经过类型转换、路径规范化、SQL 标识符白名单、XML 安全配置等限制。
- 是否有 return/throw 阻断路径。

### 5. 鉴权信息只透传

如果上游批次提供鉴权状态、P0/P1/P2 分级或鉴权绕过编号，报告中原样写入并注明来源。若没有上游信息，写“未提供上游鉴权信息”。不得自行判断无鉴权、越权或绕过。

### 6. Pipeline worker 隔离

在 `agent-5-N` 模式下：

- 只处理批次清单中的路由。
- 只写负责人指定的 `route_tracer/{route_slug}/` 或批次输出目录。
- 可只读访问 route mapper、auth audit、cross analysis 和源码。
- 不修改 route mapper、auth audit、vuln report、专项漏洞报告或其他 worker 目录。
- 发现批次输入无法定位时，写失败原因和未完成清单，不自行替换路由。

### 7. 反编译最小化

源码完整时优先读源码。只有入口、实现类、Mapper、工具方法或 sink 位于 class/JAR 且源码不可读时，才按共享反编译策略最小化反编译相关类。报告中必须标注反编译来源和限制。

### 8. Sink 必须有代码证据

只有看到真实危险 API、Mapper XML、注解 SQL、框架调用或反编译代码时，才能写具体 sink 类型：

- 看到 `Statement.execute`、MyBatis `${}`、HQL/native SQL 拼接，才能写 `SQL`。
- 看到 `Files.read*`、`FileInputStream`、`transferTo`、`FileItem.write`，才能写文件类 sink。
- 看到 XML parser、反序列化 API、命令执行、HTTP client、LDAP、表达式执行等真实调用，才能写对应 sink。

以下情况不得推断为具体 sink：

- `userManager.getUserBean(loginName)` 这类接口/Manager/DAO 方法名。
- `save()`、`add()`、`query()`、`delete()` 等业务语义方法。
- 类名包含 `Dao`、`ManagerImpl`、`Repository`。
- 只有 `.class` 文件但未反编译或未读到方法体。

这类情况在报告中写 `UNCONFIRMED` 或“下游候选调用”，并说明需要反编译/补源码确认；不要写 `SQL SELECT`、`SQL INSERT`、`Hibernate session.save` 等未经证实的细节。

## Gotchas

- Controller 方法同名重载时，必须依据 mapping、HTTP 方法和参数绑定选择真实入口。
- Spring 接口注解和实现类注解可能拆开；只看实现类会漏 route。
- Struts2 通配符和 `method:` 动态方法不能把所有 public 方法都算入口，必须由配置和 URL 实例证明。
- Servlet 覆盖 `service()` 时，`doGet`/`doPost` 可能不被调用。
- WebService 实现类 public helper 很多，但只有接口、注解或 WSDL 暴露的方法才是 operation。
- 参数常在 JSON 字符串、DTO setter、BeanUtils、Map、ThreadLocal、父类字段中改名。
- `StringUtils.defaultIfBlank`、空值默认值和无条件赋值会改变可控性。
- `PreparedStatement`、MyBatis `#{}`、路径 canonical 校验、XML 禁用外部实体等是下游判定的重要限制，不能在追踪报告里省略。
- Mapper XML、注解 SQL、HQL/JPQL、文件工具类、XML 工具类、反序列化封装方法经常是 sink 真实位置。
- “无敏感 sink”也是有效结论，但必须说明扫描到哪里以及为什么认为未到达 sink。
- Manager/DAO 方法名不是 sink 证据；看不到实现时，宁可写 `UNCONFIRMED`，不要猜 SQL/Hibernate。
- 请求模板中不要使用 `${param}` 变量格式；模板占位只允许 `{{param}}`，安全样例请求必须填入实际低风险值。
- 报告文件必须把自检清单写入文件尾部；只在 Claude 终端回复里说“自检通过”不合格。

## 停止、确认或切换条件

- 缺少源码路径且当前环境无法访问时，停止询问。
- 用户只给项目路径但要求全量路由调用链，先切换到 `java-route-mapper` 或要求提供 route mapper 输出。
- 用户要求漏洞判定、风险评级、PoC 或修复建议时，先完成必要调用链证据，再切换到对应专项 skill。
- 批次路由数量明显超出单 worker 可完成范围时，记录待拆分建议，等待负责人重新分批。
- 入口定位和源码实现冲突时，以源码和部署配置为准，并在报告中说明 route mapper 可能过期。

## Evals

### 正例：应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “追踪 `/api/user/list` 的 `orderBy` 到 DAO 的调用链。” | 触发 | 明确路由参数流向 |
| “对 trace_batch_plan 的 P0 路由生成 route_tracer 报告。” | 触发 | pipeline worker 场景 |
| “这个 SOAP operation 的 `searchJson` 最后有没有进入 SQL 拼接？” | 触发 | WebService operation 参数追踪 |
| “只输出可控性和分支条件，不做漏洞结论。” | 触发 | 调用链证据层职责 |

### 反例：不应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “提取项目所有接口和参数。” | 不触发 | route mapper 职责 |
| “判断这个接口是否 SQL 注入。” | 不直接触发 | 应由 SQL audit 下结论 |
| “检查 Shiro 配置有没有绕过。” | 不触发 | auth audit 职责 |
| “pom 里有没有 Log4j CVE？” | 不触发 | vuln scanner 职责 |

### 边界例

| 用户输入 | 预期 | 处理 |
|----------|------|------|
| “这个内部 `UserService.query` 会不会被用户控制？” | 视上下文触发 | 若能绑定 Web 入口则追踪；否则标注非 Web 入口限制 |
| “先看 `/download` 的文件路径流向，再判断任意文件读取。” | 触发本 skill 后切换 | 本 skill输出证据，文件读取 skill 判漏洞 |
| “所有 WebService 方法都追踪一下。” | 触发 | 只追踪真实暴露 operation，生成索引 |

### 失败案例

| 失败表现 | 风险 | 修复方式 |
|----------|------|----------|
| 把 sink 可达写成漏洞已确认 | 越界和误报 | 改为证据描述，交给专项 skill |
| 只写 Controller -> DAO，中间省略 Service/Util | 下游无法复核 | 补齐每层关键调用和位置 |
| 把所有 public WebService 方法都当接口 | 多报入口 | 按配置、接口或注解确认暴露 operation |
| 参数被默认值覆盖仍写完全可控 | 误导专项审计 | 按覆盖条件重新判定 |
| pipeline 报告自行写无鉴权 | 越界 | 只透传上游鉴权信息 |
