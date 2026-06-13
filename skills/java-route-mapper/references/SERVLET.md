# Servlet 路由参考

只在项目存在 `web.xml` servlet mapping、`@WebServlet`、`HttpServlet` 子类、Servlet registration bean 时读取本文件。

## URL 来源

| 来源 | 提取内容 |
|------|----------|
| `web.xml` `<servlet>` | servlet-name 到 class |
| `web.xml` `<servlet-mapping>` | servlet-name 到 url-pattern |
| `@WebServlet` | value/urlPatterns/name |
| Spring `ServletRegistrationBean` | servlet 实例和 mappings |
| ServletContainerInitializer | 动态注册，需要代码追踪 |

## URL pattern 规则

| pattern | 含义 | 处理 |
|---------|------|------|
| `/api/user` | 精确路径 | 普通路由 |
| `/api/*` | 前缀匹配 | 检查是否内部 dispatch |
| `*.do` | 扩展匹配 | 检查 action 参数、pathInfo 或反射分发 |
| `/` | 默认 servlet | 只在业务 servlet 时列出 |

## 方法映射

- `doGet` -> GET。
- `doPost` -> POST。
- `doPut` -> PUT。
- `doDelete` -> DELETE。
- `service` 重写时需要分析内部 method 分发。

## 内部分发必须展开

以下情况不能只输出 servlet pattern：

- `switch(request.getParameter("action"))`
- `if ("save".equals(cmd))`
- `request.getPathInfo()` 分发。
- `Map<String, Handler>`。
- 反射 `getMethod(action).invoke(...)`。
- `RequestDispatcher` 前端控制器分发到业务方法。

每个分支作为独立入口或 pattern 实例列出，并计入总数。

## 参数来源

| 代码模式 | 参数来源 |
|----------|----------|
| `getParameter`, `getParameterValues`, `getParameterMap` | Query/Form |
| `getInputStream`, `getReader` | Body |
| `getPart`, `getParts` | multipart file |
| Commons FileUpload | multipart file/form |
| `getHeader` | Header |
| `getCookies` | Cookie |
| `getPathInfo` | Path |

## Gotchas

- Filter 不是路由，但可能改变 path 或做 auth；本 skill 只记录必要上下文，不判断安全。
- JSP 跳转不是新入口，除非 JSP 被直接映射为 servlet 并处理请求参数。
- `/api/*` 如果没有内部 dispatch，可作为一个模式路由；有 dispatch 时必须展开分支。
