# 多入口与多方法追踪规则

本 reference 只解决一个问题：一个用户请求或一个分配项到底对应哪些真实入口方法，应该如何逐个输出。它不负责漏洞判定。

## 1. 入口枚举原则

先确认入口来源，再枚举方法：

1. 优先读取 `route_mapper/` 主索引和模块详情。
2. route mapper 不存在或过期时，读取框架配置和源码注解。
3. 用户明确指定类方法时，仍需标注“用户指定入口”，并说明是否能绑定 Web 路由。
4. 只能枚举真实暴露的方法；内部 helper、getter/setter、Object 方法、未映射重载方法不得算入口。

禁止使用“类里所有 public 方法”替代入口枚举，除非它们确实被 WebService 接口、注解或配置暴露。

## 2. 各框架方法识别

### 2.1 Spring MVC / Spring Boot

入口方法来自以下证据：

- 类级 `@RequestMapping`、`@RestController`、`@Controller`。
- 方法级 `@RequestMapping`、`@GetMapping`、`@PostMapping`、`@PutMapping`、`@DeleteMapping`、`@PatchMapping`。
- 接口上的 mapping 注解和实现类。
- `WebMvcConfigurer`、`PathMatchConfigurer#addPathPrefix` 等前缀配置。

处理规则：

- 类级路径和方法级路径必须组合。
- 同名重载必须按 HTTP method、path、参数绑定区分。
- 没有方法级 mapping 的普通 public 方法不是入口。
- 若只有类级 mapping 且方法无 mapping，除非框架或项目约定证明可达，否则标注“未确认入口”。

### 2.2 Struts2

入口方法来自以下证据：

- `struts.xml`、`struts-*.xml`、package namespace、action name、method。
- 通配符 action 与 method 映射，例如 `{1}`、`{2}`。
- DMI 或 `method:` 前缀只有在项目配置启用且 URL 可达时才纳入。

处理规则：

- 默认 `execute()` 只有在 action 未指定 method 时使用。
- getter/setter、validate、input、prepare、内部 helper 不算业务入口，除非配置明确指向。
- 通配符必须展开到实际 URL/method 实例；不能只写 `*_*`。
- 父类方法只有在 action 配置或通配符实例能调用时才算入口。

### 2.3 Servlet

入口方法来自以下证据：

- `web.xml` servlet mapping。
- `@WebServlet`。
- Servlet registration bean。

处理规则：

- 按 HTTP method 选择 `doGet`、`doPost`、`doPut`、`doDelete` 等。
- 如果类覆盖 `service()`，必须先追 `service()`，再判断是否分派到 `doXxx`。
- `url-pattern` 为 `/api/*` 或 `*.do` 时，继续追 `pathInfo`、`servletPath`、参数分发或反射分发。

### 2.4 JAX-RS

入口方法来自：

- `@ApplicationPath`。
- 类级 `@Path`。
- 方法级 `@Path`。
- HTTP 方法注解：`@GET`、`@POST`、`@PUT`、`@DELETE`、`@PATCH` 等。

处理规则：

- 类级和方法级 `@Path` 必须组合。
- 只有 `@Path` 但没有 HTTP 方法注解时，确认是否由子资源定位器返回资源对象；不确认时标注限制。
- `@PathParam`、`@QueryParam`、`@HeaderParam`、`@BeanParam` 都要纳入参数追踪。

### 2.5 WebService / SOAP

入口方法来自：

- `@WebService`、`@WebMethod`、接口类。
- CXF/JAX-WS/Axis endpoint 配置。
- WSDL 或项目生成的服务接口。

处理规则：

- endpoint address 来自配置或注解，不从实现类名猜测。
- operation 以接口、`@WebMethod`、WSDL 或配置为准。
- `@WebMethod(exclude=true)`、private/protected helper、Object 方法不算 operation。
- 多个 operation 参数结构相同，也必须逐个追踪，不能用“同上”省略。

## 3. 输出策略

### 3.1 单方法入口

若一个路由只对应一个真实入口方法：

- 生成 1 份报告。
- 优先使用 `OUTPUT_TEMPLATE_FULL.md`。
- 文件放在 `route_tracer/{route_slug}/`。

### 3.2 多方法入口

若一个路由、WebService endpoint、Servlet dispatcher 或 Struts 通配符对应多个真实方法：

- 生成 1 份索引报告。
- 每个真实入口方法生成 1 份方法报告。
- 索引必须列出全部方法、参数、sink 摘要、可控性摘要和文件链接。
- 不允许 `...`、`等`、`其他方法相同`、`更多见源码`。

报告模板选择：

- 命中敏感 sink、分支复杂、用户点名、或下游会读取的入口：使用 `OUTPUT_TEMPLATE_FULL.md`。
- 未命中敏感 sink、调用链很短、重复模式明显且证据已足够：可使用 `OUTPUT_TEMPLATE_SIMPLE.md`。
- 即使用简化模板，也必须独立追踪该方法，不能复用另一个方法的结论。

### 3.3 Pipeline worker

在 `agent-5-N` 批次中：

- 以批次清单为边界，不扩展到未分配路由。
- 每条路由使用稳定 `route_slug` 子目录，例如 `/api/user/list` -> `api_user_list`。
- 文件名使用时间戳 `YYYYMMDD_HHMMSS`。
- 如果批次输入带有 route id，报告中保留 route id，便于负责人对账。

## 4. 断点恢复

恢复旧任务时：

1. 读取批次清单或 route mapper 预期路由。
2. 读取已存在的 `route_tracer/{route_slug}/`。
3. 对比索引和方法报告数量。
4. 只补做缺失或自检失败的报告。
5. 新报告必须重新检查源码，不得只复制旧结论。

## 5. 失败与限制记录

无法完成某条入口时仍要写清楚：

- 路由或 method 标识。
- 已检查的证据来源。
- 阻塞原因，例如源码缺失、配置缺失、反编译失败、动态反射目标不可确定。
- 对下游的影响，例如“无法证明参数到达 SQL sink”。

失败项不能悄悄跳过。

## 6. 常见误判

| 误判 | 为什么错 | 正确处理 |
|------|----------|----------|
| Spring 类里所有 public 方法都当接口 | 只有 mapping 方法可达 | 按类级和方法级 mapping 枚举 |
| Struts 通配符只写一个模板路由 | 下游无法定位具体 action | 展开实际 URL/method 实例 |
| WebService 实现类 helper 算 operation | helper 未暴露给 SOAP | 以接口、注解、WSDL 或配置为准 |
| Servlet `/api/*` 只追 `doPost` | 真实业务可能由 pathInfo 分发 | 继续追分发逻辑 |
| 多方法报告用“同上” | 每个方法 sink 和分支可能不同 | 逐个输出证据 |
