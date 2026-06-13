# URI 解析差异参考

只在鉴权代码使用请求路径做白名单、权限 key、静态资源判断或路由匹配时读取本文件。

## 核心比较

| 获取方式 | 常见风险 | 审计要点 |
|----------|----------|----------|
| `getRequestURI()` | 保留分号/编码细节，可能与路由层不同 | 继续看是否规范化 |
| `getRequestURL()` | 同上且包含协议主机 | 通常不适合权限匹配 |
| `getServletPath()` | 更接近 Servlet 映射 | 仍需看 pathInfo |
| `getPathInfo()` | 前缀映射后的剩余路径 | 常用于内部 dispatch |
| Spring best matching pattern | 与 Controller 匹配结果一致 | 最适合做路由权限 key |

## 高危代码形态

- 用 `getRequestURI()` 后直接 `contains`、`startsWith`、`endsWith`。
- 静态后缀白名单，如 `.js`、`.css`、`.png`。
- 白名单先执行，规范化后再路由到业务入口。
- 鉴权层和 Controller/Action 使用不同路径变量。

## 判断流程

1. 记录鉴权层 path 变量来源。
2. 记录路由层最终匹配路径来源。
3. 对比分号、编码、`..`、双斜杠、后缀、大小写处理。
4. 追踪白名单命中后的后续拦截层。
5. 只有 payload 到达敏感入口且后续无有效拦截时，才确认绕过。

## Gotchas

- Tomcat、Spring、Shiro、Struts 对分号和编码的处理可能不同。
- `requestURI` 看似完整，但不一定是应用最终路由。
- 修复建议优先使用框架已匹配的 pattern 或统一规范化后的路径。
