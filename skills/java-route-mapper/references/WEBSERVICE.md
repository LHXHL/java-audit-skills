# WebService 路由参考

只在项目存在 CXF/JAX-WS/Axis/Axis2/SOAP endpoint，或用户要求列 SOAP 服务和方法时读取本文件。

## 核心原则

WebService URL 必须来自配置和 Servlet 映射，不得根据类名、bean id、endpoint id、服务实现名猜测。

```text
完整 URL = context-path + SOAP servlet mapping + endpoint address
```

## CXF / JAX-WS

优先读取：

- `applicationContext*.xml`
- `cxf*.xml`
- `<jaxws:endpoint ... address="...">`
- `<jaxws:server ... address="...">`
- Spring bean 中的 Endpoint 发布代码。
- `web.xml` 中 CXF Servlet 映射，如 `/services/*`, `/ws/*`。

必须输出：

- 配置文件路径和行号。
- address 原文。
- implementor / service bean。
- 完整 URL。
- 每个暴露方法的方法名、签名、参数、返回类型。

## 方法枚举

方法来源优先级：

1. WSDL/接口类明确暴露的方法。
2. `@WebMethod` 且未 `exclude=true` 的方法。
3. 实现类 public 方法，排除 `Object` 方法、getter/setter、框架生命周期方法。
4. 反编译结果。

如果服务接口和实现类分离，优先以接口暴露方法为准，再用实现类补参数名和类型。

## Axis / Axis2

配置来源：

- Axis: `server-config.wsdd`
- Axis2: `services.xml`, `WEB-INF/services/*/META-INF/services.xml`

URL 常见形式：

```text
context-path + /axis/services/{serviceName}
context-path + /services/{serviceName}
```

以实际 Servlet mapping 和 service name 为准。

## executeInterface / methodId

以下网关式服务必须展开 sub-function：

- `executeInterface(String interfaceId, String json)`
- `execute(String methodId, String payload)`
- `invoke(String code, ...)`
- switch/if-else/Map/反射根据字符串分发。

每个 interfaceId/methodId/code 都作为独立接口块输出，参数结构按该分支实际 JSON/XML/schema/DTO 解析。

## 错误示例

| 错误 | 正确做法 |
|------|----------|
| `UserServiceImpl` -> `/UserService` | 读取 endpoint `address` |
| endpoint id `userService` -> `/userService` | id 只用于定位 bean，不是 URL |
| 只输出 WSDL URL | 列出所有 SOAP 方法 |
| `executeInterface` 只算一条 | 每个 interfaceId 单独计数 |

## Gotchas

- Spring bean `implementor="#beanName"` 需要继续解析 bean class。
- `address="/"` 和 Servlet mapping 的斜杠拼接要去重。
- 多个 endpoint 指向同一实现类时，是多个服务入口，URL 不同。
- `@WebMethod(operationName=...)` 的外部方法名可能不同于 Java 方法名，两个都要记录。
