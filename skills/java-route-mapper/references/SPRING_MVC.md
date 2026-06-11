# Spring MVC / Spring Boot 路由参考

只在项目使用 Spring Web 注解、Spring Boot Web、或存在 `WebMvcConfigurer` 路径前缀时读取本文件。

## URL 组成

最终 URL 按以下顺序组合：

```text
context-path + servlet-path + addPathPrefix + class-level mapping + method-level mapping
```

来源优先级：

| 片段 | 常见来源 |
|------|----------|
| context-path | `server.servlet.context-path`, `server.context-path`, WAR context |
| servlet-path | `spring.mvc.servlet.path`, `DispatcherServlet` registration |
| addPathPrefix | `WebMvcConfigurer#configurePathMatch` |
| class mapping | 类上的 `@RequestMapping` 或组合注解 |
| method mapping | 方法上的 mapping 注解 |

## 必查项

- `@Controller`, `@RestController` 类。
- `@RequestMapping` 及 `@GetMapping` 等组合注解。
- 自定义组合注解上的 meta-annotation。
- `WebMvcConfigurer#configurePathMatch` / `PathMatchConfigurer#addPathPrefix`。
- `WebMvcRegistrations`, `ServletRegistrationBean`, 自定义 `DispatcherServlet`。
- properties/yml 中的 context path 和 servlet path。

## addPathPrefix 规则

遇到 `addPathPrefix(prefix, predicate)` 时：

1. 记录 prefix、predicate、源码位置。
2. 判断 predicate 匹配哪些 Controller。
3. 将 prefix 加到匹配 Controller 的最终 URL。
4. 无法静态判断 predicate 时，在路由详情中标注“前缀需人工确认”，不能静默忽略。

示例：

```java
configurer.addPathPrefix("/admin", c -> c.isAnnotationPresent(AdminController.class));
```

匹配类上的 `/users` 和方法上的 `/{id}` 后，最终 URL 是 `/admin/users/{id}`。

## 参数规则

| 参数形态 | 输出来源 |
|----------|----------|
| `@PathVariable` | Path |
| `@RequestParam` | Query/Form |
| `@RequestBody` | Body |
| `@RequestHeader` | Header |
| `@CookieValue` | Cookie |
| `MultipartFile`, `Part` | File/Body multipart |
| `@ModelAttribute` 或复杂对象无注解 | Query/Form 对象绑定 |

## 路由展开

- `@RequestMapping(path={"/a","/b"})` 计为两条路径。
- `method={GET,POST}` 计为两个 HTTP 方法。
- `/{id}`、`/**` 是路径模板，不展开具体值。
- `params`、`headers` 条件要记录，因为它们影响可达性。

## 不要误列

- `@ControllerAdvice` 不是路由。
- `HandlerInterceptor` / Filter 不是路由。
- 静态资源 handler 一般不列为业务接口。
- Actuator 端点只在用户明确要求框架端点时列出。

## Gotchas

- 类继承和接口默认方法可能携带 mapping，要检查父类/接口。
- Kotlin/record/constructor binding 的 DTO 字段可能不在传统 getter/setter 中。
- Spring Security 的 URL 规则只影响鉴权，不在本 skill 中判断是否安全。
