---
name: java-route-mapper
description: 当用户要求从源码、WAR/class/JAR 产物中提取、枚举、映射或记录 Java Web 路由、端点和请求参数，尤其是为后续鉴权、调用链、SQL、XXE、上传、文件读取或完整流水线审计提供输入时使用；仅做漏洞判定、调用链追踪、鉴权判断、依赖 CVE 扫描，或不需要路由提取的通用 API 文档润色时不要使用。
---

# Java Route Mapper

## 当前定位

`java-route-mapper` 是 Java 审计技能集的入口面数据底座。它只回答一个问题：项目中有哪些可访问入口，每个入口对应哪个代码位置，以及请求参数从哪里来。

它的输出会被下游技能读取：

- `java-auth-audit`: 对每条路由匹配鉴权规则和绕过风险。
- `java-route-tracer`: 从入口方法继续追踪参数流向。
- `java-sql-audit` / `java-xxe-audit` / `java-file-upload-audit` / `java-file-read-audit` / `java-deserialization-audit`: 以路由和参数清单作为输入来源。
- `java-audit-pipeline`: 阶段 1 的 `agent-1-N` worker 调用本 skill 产出模块路由详情，`agent-1-merge` 再合并主索引。

本 skill 不做漏洞评估、不判断鉴权是否正确、不追踪完整调用链、不扫描组件 CVE、不生成“看起来更漂亮”的 API 文档。

## 何时触发

用户意图包含以下任一项时触发：

- 从 Java Web 源码、WAR、反编译目录、class 或 JAR 中提取路由。
- 梳理 Controller、Action、Servlet、JAX-RS Resource、WebService endpoint。
- 生成 `route_mapper/` 输出，供后续漏洞审计、鉴权审计或调用链追踪使用。
- 要求列出接口路径、HTTP 方法、入口方法、请求参数、SOAP 方法、Struts action 实例。
- 大型多模块项目需要按模块、namespace 或 worker 范围提取入口面。

典型用户说法：

- “帮我把这个 Java 项目的所有接口和参数梳理出来。”
- “先跑 route mapper，给后续 SQL 审计用。”
- “这个 Struts 项目没有接口文档，列出所有 action。”
- “提取 CXF WebService 的服务地址和所有 SOAP 方法。”
- “流水线 agent-1-3 只处理 admin_user 模块的路由。”

## 何时不触发

相似但不应触发的任务：

- 只问某条接口的调用链、参数是否到达 sink：使用 `java-route-tracer`。
- 要判断 SQL 注入、XXE、上传、文件读取、反序列化漏洞：使用对应漏洞审计 skill。
- 要判断鉴权绕过、越权或安全拦截器规则：使用 `java-auth-audit`。
- 只做依赖版本和 CVE 扫描：使用 `java-vuln-scanner`。
- 用户已有完整路由清单，只要求改写成 OpenAPI、Postman 或人类文档：这通常是文档转换任务，不是 route mapper。
- 只分析非 Web Java 程序、CLI、定时任务、消息消费者，且没有 HTTP/WebService 入口。

边界例：

- “这个接口有没有 SQL 注入？”不触发本 skill，除非用户同时要求先补齐入口面。
- “帮我找所有 `@RequestMapping`。”触发，但只输出路由和参数，不扩展到漏洞判断。
- “分析所有 public 方法。”不触发，除非这些方法是 WebService 或 Web 框架入口。

## 成功标准

完成后必须能让下游 agent 精确回答：“从哪个 URL/方法进入，用户可控参数叫什么，入口代码在哪里。”

最低合格输出：

- 覆盖所有发现的 Web 入口，不只列关键接口。
- 每个普通路由都有 HTTP 方法、完整 URL、入口类/方法、源码或反编译位置、参数结构。
- 每个 WebService 服务地址来自配置，不靠类名或 bean id 猜测；每个 SOAP 方法单独列出签名和参数。
- 通配符、网关分发、Struts 动态 action 不以模板代替实例；必须列出实际可达实例或 sub-function。
- 输出文件链接、自检数量、状态 JSON 与实际文件一致。
- pipeline worker 模式下，只写自己的模块目录和自己的反编译目录。
- 所有数量、行数、类数、方法数和覆盖范围都必须是精确可复核值；不能写 `约`、`~`、`大约`、`60+`、`200+`、尾随加号或范围数量。没有精确枚举时写 `不可确认` 或 `未精确统计`。

## 输入与模式判断

先判断执行模式：

| 模式 | 触发条件 | 输出责任 |
|------|----------|----------|
| Standalone | 用户直接要求对整个项目做路由映射 | 生成主索引、模块详情、README |
| Pipeline worker | prompt 中出现 `agent-1-{N}`、指定 `module_name`、指定状态文件 | 只生成该模块详情和 `.status/agent-1-{N}.json`，不写主索引或项目 README |
| Pipeline merge | prompt 中出现 `agent-1-merge` 或只要求合并 worker 产物 | 不重新扫描源码，只合并 worker 输出为主索引 |

如果输入范围不明确：

- 可以从用户给出的源码路径、输出路径、模块路径推导时，直接执行。
- 缺少源码路径或没有可访问项目文件时，先询问。
- 在 pipeline worker 模式下，缺少 `module_name`、`module_paths`、`output_path` 或状态文件路径时，停止并要求负责人补齐；不要自行扩大范围。

## 工作流

1. 确认模式、源码路径、输出目录、可写范围。
2. 识别框架和入口类型。只读取与当前项目实际框架相关的 reference。
3. 提取上下文路径、Servlet 映射、框架前缀、类级路径、方法级路径，组合完整 URL。
4. 枚举入口方法和参数结构；源码不完整时按需反编译。
5. 对通配符、dispatch 网关、WebService 动态方法做实例化展开。
6. 按模板写入输出文件。
7. 执行完整性自检；失败时补查源码或反编译结果，直到数量和文件对账通过。

## 按需读取的 references

只在需要时读取，避免把主上下文变成框架教程：

- 框架识别不确定：`references/FRAMEWORK_PATTERNS.md`
- Spring MVC / Spring Boot：`references/SPRING_MVC.md`
- Struts2：`references/STRUTS.md`
- Servlet：`references/SERVLET.md`
- JAX-RS：`references/JAXRS.md`
- CXF/JAX-WS/Axis：`references/WEBSERVICE.md`
- 注解参数提取：`references/ANNOTATIONS.md`
- 需要反编译：`references/DECOMPILE_STRATEGY.md`
- 输出文件：`references/OUTPUT_TEMPLATE_INDEX.md`、`references/OUTPUT_TEMPLATE_MODULE.md`、`references/OUTPUT_TEMPLATE_README.md`
- 通用输出规范：`../java-shared/OUTPUT_STANDARD.md`

## CRITICAL 1: 完整输出零省略

禁止用摘要替代枚举：

- 禁止 `...`、`等`、`其他`、`更多`、`部分`、`主要接口`、`关键接口`。
- 禁止 `共 N 个，列出部分`。
- 禁止 `001 ~ 050` 这类范围代替逐项列表。
- 禁止只列类名、WSDL 地址、namespace 名而不列具体入口。
- 数量字段必须是精确数字，禁止 `200+`、`约 50`、`大量`。
- 如果只知道某类 Action/Servlet/WebService 存在但未反编译出全部方法，不得写“剩余约 N 个”或“已知约 N 个”；应写精确已枚举数，并把未枚举部分写为 `不可确认`。

如果输出太大，拆分文件；不要压缩为摘要。

## CRITICAL 2: 动态路由必须实例化

需要展开的情况：

- Struts2 通配符 action，如 `*_*`、`user_*`、`*`。
- Servlet `/api/*`、`*.do` 内部根据 `pathInfo`、参数、反射或 switch 分发到不同方法。
- 网关方法，如 `executeInterface(String code, String json)`、`dispatch(String action, ...)`、`invoke(String type, ...)`。
- WebService 中通过 `interfaceId`、`methodId`、`code` 执行业务方法。

输出方式：

- Struts2 通配符可用“模式族 + URL 实例列表”，模式族头部只写一次，实例列表必须逐行列出全部 URL 到方法映射。
- dispatch / executeInterface / methodId 分支必须把每个 sub-function 作为独立接口计数，并写清参数结构。
- Spring MVC `{id}`、JAX-RS `@PathParam` 是路径变量，不展开具体值；按普通路由输出并标注 Path 参数。

## CRITICAL 3: URL 只能由真实配置组合

完整 URL 按真实来源组合，不凭命名猜测：

- context path
- web.xml / `@WebServlet` / Servlet registration
- Spring `server.servlet.context-path`、类级和方法级 mapping
- `WebMvcConfigurer#configurePathMatch` / `PathMatchConfigurer#addPathPrefix`
- JAX-RS `ApplicationPath`、类级 `@Path`、方法级 `@Path`
- Struts package namespace、action name、extension
- CXF/JAX-WS endpoint `address`
- Axis/Axis2 service name

WebService 特别规则：

- CXF/JAX-WS 地址必须从 XML、Spring bean、endpoint 配置或注解配置读取。
- `UserServiceImpl` 不能推断为 `/UserService`。
- endpoint id 或 bean id 不能替代 `address`。
- 只给 WSDL URL 不合格，必须列出服务下所有 public SOAP 方法或配置暴露的方法。

## CRITICAL 4: 参数结构必须可用于下游追踪

每个入口至少标注：

- Path 参数：名称、类型。
- Query/Form 参数：名称、类型、是否明显必填。
- Body 参数：Content-Type、对象类型、关键字段；对象字段过多时仍要列出字段，不用“对象见源码”替代。
- Header/Cookie 参数：只有自定义鉴权头、业务头或代码显式读取时列出；标准 `Authorization` 可按项目实际需要标注。
- File 参数：文件字段、文件名字段、保存路径相关参数。
- SOAP 参数：方法签名、参数名、类型、返回类型。

类型未知时：

- 先查源码类型、DTO、字段、getter/setter、XML/schema、反编译结果。
- 仍无法确定时标注 `unknown` 和证据位置；不能编造类型。

## CRITICAL 5: Pipeline worker 隔离

在 `agent-1-N` worker 模式下：

- 只扫描负责人分配的 `module_paths`，但可只读访问同 WAR 的公共配置、公共基类和依赖 jar。
- 只写 `{output_path}/route_mapper/{module_name}/`。
- 只写 `{output_path}/decompiled/agent-1-{N}/`。
- 禁止写主索引、项目 README、其他 worker 子目录、共享 `webservice/` 目录。
- 完成后必须原子写入 `.status/agent-1-{N}.json`，数字字段使用 JSON number。
- 若实际路由数超过侦查单预估 1.5 倍且大于 100，写 `status="overflow"` 并停止，等待重新拆分。

状态 JSON 至少包含：

```json
{
  "schema_version": 1,
  "agent_id": "agent-1-N",
  "recon_id": "from_recon_file",
  "module_name": "module",
  "module_paths": [],
  "status": "success",
  "attempt": 1,
  "actual_route_count": 0,
  "estimated_route_count": 0,
  "frameworks": [],
  "output_files": [],
  "output_file_sha256": {},
  "completed_at": "ISO8601",
  "error_message": null
}
```

## CRITICAL 6: 输出校验

写完前后都要检查：

- 主索引链接的所有详情文件真实存在。
- 模块详情里的总接口数等于逐条列出的接口数，通配符实例和 sub-function 计入总数。
- WebService 方法数等于配置暴露方法和反编译 public 方法核对后的数量。
- 文件中不含占位符 `【填写】`。
- 文件中不含省略词和数量后缀。
- pipeline worker 的 `.status` 中 `output_files` 均存在且 hash 匹配。

自检失败时不要交付“待补充”版本；继续补查缺口。只有源码缺失、配置不可读、反编译失败且无法恢复时，才在输出中标注阻塞原因。

## 输出文件

Standalone 模式：

- `route_mapper/{project_name}_route_mapper_{YYYYMMDD_HHMMSS}.md`
- `route_mapper/{module_name}/{project_name}_module_{module_name}_{YYYYMMDD_HHMMSS}.md`
- `route_mapper/{project_name}_route_README_{YYYYMMDD_HHMMSS}.md`
- WebService 可按实际服务放入模块子目录或 `route_mapper/webservice/`，但主索引链接必须准确。

Pipeline worker 模式：

- 只写 `{output_path}/route_mapper/{module_name}/...md`
- 只写 `{output_path}/route_mapper/.status/agent-1-{N}.json`

Pipeline merge 模式：

- 读取 recon、status、worker 输出。
- 不重新扫描源码。
- 只写主索引和 README。

## Gotchas

- `addPathPrefix` 会改变 Spring Controller 最终 URL；漏掉会导致下游鉴权和调用链全部错位。
- Struts2 `*_*` 不是一个接口；它是一组可达 action/method 实例。
- 网关式 `executeInterface` 不是一个业务接口；每个 code/interfaceId/methodId 都是独立入口。
- WebService URL 的真实来源是配置 `address` 和 Servlet 映射，不是实现类名。
- 只读公共基类很重要；很多 Action 参数来自父类字段或 setter。
- “参数对象 FooRequest”不够，下游需要字段名和类型。
- pipeline worker 不得为了补全上下文写入其他模块产物；只能读取必要公共上下文。
- 大项目发现数量异常增长时要 overflow 停止，而不是继续写一个失控的大文件。
- 空模块也要有明确输出或 status 说明，否则 merge 无法区分“无路由”和“漏扫”。

## Evals

### 正例：应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “提取这个 Spring Boot 项目的所有接口和参数，输出 route_mapper。” | 触发 | 明确要求路由和参数映射 |
| “这个 Struts2 项目 action 都是 `*_*`，帮我列完整 URL。” | 触发 | 动态路由实例化是核心职责 |
| “agent-1-4 只处理 biz_order 模块，生成状态 JSON。” | 触发 | pipeline worker 场景 |
| “列出 CXF 服务地址和每个 SOAP 方法参数。” | 触发 | WebService endpoint 映射 |

### 反例：不应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “判断 `/api/user/{id}` 是否存在越权。” | 不触发 | 应使用 auth audit 或 tracer |
| “扫描 pom 里的 CVE。” | 不触发 | 依赖漏洞扫描不是路由映射 |
| “把这份接口文档润色成 Markdown。” | 不触发 | 没有源码路由提取需求 |
| “追踪这个参数到 SQL 拼接点。” | 不触发 | 应使用 route tracer / SQL audit |

### 边界例

| 用户输入 | 预期 | 处理 |
|----------|------|------|
| “找所有 `@RequestMapping`。” | 触发 | 输出路由和参数，不做漏洞判断 |
| “分析所有 public 方法。” | 视上下文 | 只有 WebService 暴露方法才纳入 |
| “接口太多，列关键的就行。” | 触发但拒绝省略 | 说明本 skill 必须完整输出，可拆分文件 |

### 失败案例

| 失败表现 | 风险 | 修复方式 |
|----------|------|----------|
| 用 `/UserService` 代替配置中的 `/UserApi` | 下游请求路径错误 | 读取 endpoint `address` 和 Servlet 映射 |
| 把 `*_*` 输出成 `{action}_{method}.action` | 漏掉实际入口 | 反编译 Action 类并逐行列出实例 |
| 输出 `UserRequest` 但不列字段 | 下游无法追踪参数 | 展开 DTO 字段或标注无法确定原因 |
| worker 写了 `route_mapper/README.md` | 覆盖 merge 产物 | worker 只写模块目录和 status |
| `actual_route_count` 写成 `"200+"` | merge 无法对账 | 查清精确数字，使用 JSON number |
