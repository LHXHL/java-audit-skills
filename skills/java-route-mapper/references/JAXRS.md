# JAX-RS 路由参考

只在项目存在 `@Path`、Jersey、RESTEasy、CXF JAX-RS、`Application` 子类或 `@ApplicationPath` 时读取本文件。

## URL 组成

```text
context-path + servlet/application path + class @Path + method @Path
```

常见 base path 来源：

- `@ApplicationPath`
- `web.xml` servlet mapping
- Jersey/RESTEasy/CXF 配置
- Spring bean 注册的 JAX-RS server address

## 路由识别

- 类上有 `@Path` 的 Resource。
- 方法上有 HTTP method 注解：`@GET`, `@POST`, `@PUT`, `@DELETE`, `@PATCH`, 自定义 `@HttpMethod`。
- 子资源 locator：有 `@Path` 但无 HTTP method 的方法，需要继续追踪返回 Resource 类型。

## 参数来源

| 注解/模式 | 参数来源 |
|-----------|----------|
| `@PathParam` | Path |
| `@QueryParam` | Query |
| `@FormParam` | Form |
| `@HeaderParam` | Header |
| `@CookieParam` | Cookie |
| `@MatrixParam` | Matrix |
| `@BeanParam` | 展开 bean 内部参数注解 |
| 无注解实体参数 + `@Consumes` | Body |

## 展开规则

- 类级和方法级 `@Path` 必须组合。
- `@Path("{id}")` 是路径模板，不展开具体值。
- 同一方法多个媒体类型只影响 Content-Type，不创造不同业务入口，除非输出模板需要按 Content-Type 拆分。
- 子资源 locator 要继续解析返回类型的 `@Path` 和 HTTP method。

## 不要误列

- `ContainerRequestFilter`、`ExceptionMapper`、`MessageBodyReader/Writer` 不是路由。
- 只有类级 `@Path` 但没有 HTTP method 且不是子资源终点时，不算最终接口。

## Gotchas

- `@BeanParam` 很容易漏参数，必须展开其字段和 setter 上的参数注解。
- CXF 同时支持 JAX-RS 和 JAX-WS，二者 URL 来源不同，不能混用规则。
- Resource 接口和实现类可能分离，注解可能在接口上。
