# 鉴权反编译策略参考

只在源码缺失、class-only、鉴权配置指向不可读类、或依赖 JAR 中实现鉴权逻辑时读取本文件。

## 何时反编译

必须反编译：

- `Filter`、`Interceptor`、Shiro Realm、JWT 工具类、SecurityConfig 只有 class。
- 自定义权限注解处理器不可读。
- web.xml / Spring XML 指向的鉴权类源码缺失。
- 需要确认路径获取、白名单、权限校验、session/JWT 逻辑。

不需要反编译：

- 源码完整且可读。
- 第三方框架类不是项目自定义鉴权逻辑。
- 只为了生成更漂亮的报告。

## 最小化定位

优先定位这些类：

- `*Filter`, `*AuthFilter`, `*LoginFilter`
- `*Interceptor`, `*PermissionInterceptor`
- `*SecurityConfig*`, `*ShiroConfig*`
- `*Realm`, `*AuthorizingRealm`
- `*Jwt*`, `*Token*`, `*SecurityUtil*`, `*Permission*`
- 自定义注解和对应 AOP/Aspect/Handler。

## 提取内容

- 路径变量来源和匹配逻辑。
- 白名单和排除列表。
- session/currentUser/role/permission 读取方式。
- JWT 解析和验证 API。
- 数据归属校验字段。
- 后续放行或拒绝分支。

## 失败处理

反编译失败时：

1. 尝试从接口、父类、XML、调用点、常量池或配置补证据。
2. 在报告中记录 class/JAR 路径和失败原因。
3. 无法确认的鉴权状态标注 `不确定`，不要编造结论。

## Gotchas

- 反编译可能丢失行号和参数名，证据位置可用 class 路径替代。
- 只反编译目标类和必要父类；不要整包盲反编译。
- 框架默认类不要当项目自定义漏洞点。
