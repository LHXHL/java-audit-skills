# Filter / Interceptor 鉴权参考

只在项目通过 Servlet Filter、Spring HandlerInterceptor、Struts Interceptor 或自定义拦截链做登录/权限校验时读取本文件。

## 必查点

- 注册方式：`web.xml`、`@WebFilter`、`FilterRegistrationBean`、`WebMvcConfigurer#addInterceptors`、Struts interceptor stack。
- 覆盖路径、排除路径、执行顺序。
- 获取路径的方法：`getRequestURI`、`getServletPath`、`getPathInfo`、Spring best matching pattern。
- 登录检查、角色检查、白名单和业务权限是否分层。
- 放行分支后是否还有后续鉴权层。

## 危险模式

| 模式 | 风险 |
|------|------|
| 白名单用 `contains` / `endsWith` | 路径穿越、分号、后缀绕过 |
| 使用原始 URI 但路由使用规范化路径 | 解析差异绕过 |
| Filter mapping 未覆盖业务路径 | 无鉴权 |
| Interceptor exclude 过宽 | 敏感路径绕过 |
| 登录检查和权限检查顺序错误 | 已登录用户越权 |

## 误报防线

- Filter 放行不一定漏洞，后续 Interceptor/框架配置可能继续拦截。
- 静态资源白名单要确认实际路由不会落到业务 Controller/Action。
- 只看到 `session != null` 不够，需分析后续角色/权限校验。

## Gotchas

- `chain.doFilter` 前后的分支含义要分清；有些项目未登录也先放行给后续组件处理。
- 多个 Filter 的 order 会改变结论。
- Struts/Spring 路由和 Servlet path 的解析差异是绕过高发点。
