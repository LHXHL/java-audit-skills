# 注解与参数绑定参考

只在需要从注解判断路由、HTTP 方法、参数来源或 Content-Type 时读取本文件。

## 路由注解

| 技术 | 注解 | 提取内容 |
|------|------|----------|
| Spring | `@RequestMapping` | path/value、method、consumes、produces |
| Spring | `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping` | HTTP 方法由注解决定，path/value 同步读取 |
| Spring | `@Controller`, `@RestController` | 标记类为 Spring Web 入口候选 |
| JAX-RS | `@Path` | 类级和方法级路径 |
| JAX-RS | `@GET`, `@POST`, `@PUT`, `@DELETE`, `@PATCH` | HTTP 方法 |
| JAX-RS | `@Consumes`, `@Produces` | 请求和响应媒体类型 |
| Servlet | `@WebServlet` | urlPatterns/value/name/loadOnStartup |
| JAX-WS | `@WebService`, `@WebMethod` | SOAP 服务和暴露方法；URL 仍优先来自配置 |

## 参数来源映射

| 来源 | Spring | JAX-RS | Servlet 代码模式 |
|------|--------|--------|------------------|
| Path | `@PathVariable` | `@PathParam` | `getPathInfo()` 后解析 |
| Query/Form | `@RequestParam`, 未注解简单类型 | `@QueryParam`, `@FormParam` | `request.getParameter*` |
| Body JSON/XML | `@RequestBody` | 无注解实体参数、`@Consumes` | `getInputStream()`, `getReader()` |
| Header | `@RequestHeader` | `@HeaderParam` | `getHeader()` |
| Cookie | `@CookieValue` | `@CookieParam` | `getCookies()` |
| File | `MultipartFile`, `Part` | multipart provider | `getPart()`, Commons FileUpload |
| Bean wrapper | `@ModelAttribute`, DTO | `@BeanParam` | 手动 set 到对象 |

## 参数类型解析优先级

1. 方法签名类型。
2. 注解属性，如 `required`, `defaultValue`, `name`, `value`。
3. DTO 字段、getter/setter、构造器绑定。
4. Bean validation 注解，如 `@NotNull`, `@Size`, `@Pattern`，只用于辅助必填/格式判断。
5. 反编译结果。

## 注解组合规则

- 类级路径 + 方法级路径共同组成最终路径。
- 多个 path/value 要展开为多条 route。
- 多个 HTTP method 要展开为多条 route，或在同一块中明确列出多个方法；计数必须一致。
- `consumes` 影响 Body 类型和 Content-Type。
- 自定义组合注解需要追到其 meta-annotation，例如自定义 `@AdminApi` 上的 `@RequestMapping`。

## Gotchas

- Spring 未注解的复杂对象常来自 Query/Form 绑定，不要默认当作 JSON body。
- `@RequestBody(required=false)` 仍是 Body 参数，只是可选。
- `@WebMethod(exclude=true)` 不应列为 SOAP 方法。
- Lombok 不改变 HTTP 参数来源，但会影响字段可见性；字段仍要从源码或反编译解析。
