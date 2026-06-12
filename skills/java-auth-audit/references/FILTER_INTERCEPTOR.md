# Filter / Interceptor 鉴权参考

只在项目通过 Servlet Filter、Spring HandlerInterceptor、Struts Interceptor、自定义拦截链或网关适配层做登录/权限校验时读取本文件。

## 必查点

- 注册方式：`web.xml`、`@WebFilter`、`FilterRegistrationBean`、`WebMvcConfigurer#addInterceptors`、Struts interceptor stack。
- 覆盖路径、排除路径、执行顺序和 dispatcher type。
- 路径来源：`getRequestURI`、`getServletPath`、`getPathInfo`、Spring best matching pattern、Struts action name。
- 登录检查、角色检查、白名单和业务权限是否分层。
- 放行分支后是否还有 Shiro、Spring Security、方法注解、业务校验或对象归属校验。

## 危险模式

| 模式 | 风险判断 |
|------|----------|
| 白名单使用 `contains`、`endsWith`、原始 URI | 可能路径解析差异绕过 |
| Filter mapping 未覆盖业务路径 | 只有确认目标入口内部也无鉴权时才升格 |
| Interceptor exclude 过宽 | 需确认排除路径对应敏感业务入口 |
| 登录检查和权限检查顺序错误 | 可能低权限用户越权 |
| 直接 Servlet/CXF/SOAP 入口绕过 MVC 拦截器 | 需确认该入口内部是否自带鉴权 |

## 误报防线

- Filter 放行不等于漏洞，后续层可能继续拦截。
- 未覆盖 REST、Servlet、CXF 或 SOAP 入口时，必须继续查入口内部鉴权；内部未知则 `待验证` 或 `不可确认`。
- 独立 Servlet、文件上传 Servlet、长轮询 Servlet、推送 Servlet、框架 Servlet 或自定义业务 Servlet 若只有 class 名而无方法体，必须放入待验证；不能只因 Filter 不覆盖就升格。
- 静态资源白名单必须证明会落到业务入口，不能只凭后缀判断。
- `session != null` 只证明存在会话，不证明角色、权限或对象归属。

## 输出要求

- 主报告必须展示拦截链：请求入口、匹配规则、放行条件、后续层结论。
- 路径绕过 payload 只有在确认到达敏感入口且无后续有效拦截时生成。
