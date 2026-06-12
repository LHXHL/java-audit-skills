# 注解式鉴权参考

只在项目使用 Shiro 注解、Spring Security 方法注解或自定义权限注解时读取本文件。

## 必查点

- 注解类型：`@RequiresAuthentication`、`@RequiresRoles`、`@RequiresPermissions`、`@PreAuthorize`、`@PostAuthorize`、自定义注解。
- 注解生效条件：AOP/代理、方法安全开关、切面注册、拦截器注册。
- 类级注解和方法级注解的覆盖关系。
- 自定义注解是否真的连接到鉴权逻辑。
- 内部方法调用、私有方法、final 方法是否绕过代理。

## 危险模式

| 模式 | 风险判断 |
|------|----------|
| 敏感 public 方法缺注解且无 URL 层规则 | 可能无鉴权，需确认入口可达 |
| 方法级宽松规则覆盖类级严格规则 | 可能权限降低 |
| 自定义注解只打标不拦截 | 虚假鉴权 |
| SpEL 表达式信任可控参数 | 可能权限绕过或对象越权 |
| 内部 self-invocation 依赖注解 | 方法级注解可能不生效 |

## 边界

- `global-allowed-methods regex:.*`、全局暴露 public 方法或宽泛 action method 规则默认写 README 攻击面建议。
- 只有找到具体敏感方法、真实入口、鉴权缺口和后续拦截缺失，才进入主报告。
- 没有方法注解不代表无鉴权，必须继续看 URL 层、Filter、Interceptor、业务校验。
- Controller 继承父类或抽象基类时，父类未反编译/未确认不得升格；只能写待验证或不可确认。

## 输出要求

- 注解风险必须写清注解为什么生效或为什么不生效。
- AOP、父类、代理或运行时映射未知时标 `待验证`，不生成 Burp Suite 请求。
