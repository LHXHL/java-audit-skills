# 框架识别参考

只在项目入口框架不明确、存在多框架共存、或 recon/worker 需要确认扫描范围时读取本文件。

## 识别目标

识别“会产生 HTTP/WebService 入口”的框架，不要把 DAO、任务调度、消息队列、普通 Service 层当作路由来源。

## 快速锚点

| 框架 | 文件锚点 | 代码锚点 | 依赖锚点 |
|------|----------|----------|----------|
| Spring MVC / Boot | `application.properties/yml`, `web.xml`, `*-servlet.xml` | `@Controller`, `@RestController`, `@RequestMapping`, `WebMvcConfigurer` | `spring-webmvc`, `spring-boot-starter-web` |
| Struts2 | `struts.xml`, `struts-*.xml`, `web.xml` filter | `ActionSupport`, `execute`, action setters | `struts2-core` |
| Servlet | `web.xml` | `@WebServlet`, `HttpServlet`, `doGet`, `doPost` | `javax.servlet`, `jakarta.servlet` |
| JAX-RS | `web.xml`, `Application` subclass | `@Path`, `@GET`, `@POST`, `@ApplicationPath` | Jersey, RESTEasy, CXF JAX-RS |
| CXF/JAX-WS | `applicationContext*.xml`, `cxf*.xml`, `web.xml` | `@WebService`, `@WebMethod` | `cxf-rt-frontend-jaxws`, `jaxws` |
| Axis/Axis2 | `server-config.wsdd`, `services.xml`, `WEB-INF/services` | service implementation classes | `axis`, `axis2` |

## 建议扫描命令

在大项目中优先用锚点缩小范围：

```bash
find . -name WEB-INF -type d -not -path '*/target/*' -not -path '*/build/*'
find . \( -name 'web.xml' -o -name 'struts*.xml' -o -name 'application*.yml' -o -name 'application*.properties' -o -name '*cxf*.xml' -o -name 'server-config.wsdd' -o -name 'services.xml' \)
rg -n '@(RestController|Controller|RequestMapping|GetMapping|PostMapping|Path|WebServlet|WebService|WebMethod|ApplicationPath)' .
rg -n 'extends +(HttpServlet|ActionSupport|Application)' .
```

## 多框架共存

同一个 WAR 可能同时存在多套入口：

- Spring MVC + Struts2: 两者都要提取，不能用 Spring 覆盖 Struts。
- Spring + CXF/JAX-WS: REST Controller 和 SOAP endpoint 分开计数。
- Servlet + 前端控制器: Servlet pattern 只是入口，若内部 dispatch 到业务方法，继续展开 dispatch 分支。
- 旧项目多个 `struts-*.xml`: 每个配置文件都要纳入，不只读取 `struts.xml`。

## 不纳入 route mapper 的内容

- Mapper、DAO、Repository。
- 普通 Service 方法，除非被 WebService 配置直接暴露。
- 定时任务、消息监听器、CLI main。
- 静态资源目录，除非 Servlet 或 Controller 显式处理上传/下载。

## 识别失败时

如果无法确认框架：

1. 先查 `WEB-INF/web.xml` 的 Filter/Servlet 配置。
2. 再查依赖和注解锚点。
3. 对 WAR/class-only 项目按需反编译入口类。
4. 仍无法确认时输出“未识别到 Web 入口”的证据，不要编造框架。

## Gotchas

- Maven 多模块中只有部分模块是 WAR；不要扫描全部子模块后把非 Web 模块写进路由清单。
- Spring Boot actuator、Swagger、静态资源一般不是业务入口，除非用户明确要求列框架自带端点。
- `@ControllerAdvice`、Filter、Interceptor 是辅助组件，不是独立路由。
