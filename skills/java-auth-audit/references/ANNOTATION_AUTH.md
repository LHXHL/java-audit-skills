# 注解式鉴权参考

只在项目使用 Shiro 注解、Spring Security 方法注解或自定义权限注解时读取本文件。

## 必查点

- 注解类型：`@RequiresAuthentication`、`@RequiresRoles`、`@RequiresPermissions`、`@PreAuthorize`、`@PostAuthorize`、自定义注解。
- 注解生效条件：AOP/代理/方法安全是否启用。
- 类级注解和方法级注解的覆盖关系。
- 自定义注解的拦截器、切面或 HandlerMethodArgumentResolver。
- 内部方法调用是否绕过代理。

## 危险模式

| 模式 | 风险 |
|------|------|
| 敏感方法缺注解且无全局规则 | 无鉴权 |
| 类级注解被方法级宽松规则覆盖 | 越权 |
| 私有方法/内部调用依赖注解 | 注解不生效 |
| SpEL 表达式引用可控参数错误 | 权限绕过 |
| 自定义注解只打标不拦截 | 虚假鉴权 |

## 误报防线

- 没有方法注解不代表无鉴权，可能有 URL 层规则。
- 有注解不代表有效，必须确认代理和拦截器生效。
- `@PostAuthorize` 是执行后校验，敏感副作用方法需要谨慎判断。

## Gotchas

- Spring 内部 self-invocation 不经过代理，方法级注解可能失效。
- Shiro 注解需要对应 AOP 配置，否则不会执行。
- 自定义注解要追到处理器，不要只按名字判断。
