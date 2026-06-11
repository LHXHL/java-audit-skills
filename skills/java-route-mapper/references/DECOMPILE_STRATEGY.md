# 反编译策略参考

只在源码不完整、入口类/DTO 只有 `.class`、依赖 JAR 中包含 Web 入口、或动态路由需要枚举方法时读取本文件。

## 何时反编译

必须反编译：

- Controller/Action/Servlet/Resource/WebService 实现类只有 class。
- Struts 通配符需要枚举 Action 业务方法。
- WebService 需要方法签名和参数类型。
- DTO/POJO 类型源码缺失，参数字段无法确定。
- dispatch 网关通过 switch/Map/反射分发，源码不可读。

不需要反编译：

- 源码已完整且可读。
- 仅为了美化输出或确认普通 Java 语法。
- 第三方框架类，不是项目暴露入口或参数类型。

## 输出目录规则

| 模式 | 反编译目录 |
|------|------------|
| Standalone | `{output_path}/decompiled/` 或用户指定目录 |
| Pipeline worker | `{output_path}/decompiled/agent-1-{N}/`，禁止写其他 worker 目录 |
| Pipeline later stages | 可读写 `{output_path}/decompiled/cache/`，按流水线约束执行 |

## 最小化原则

1. 先反编译入口类。
2. 从入口类发现 DTO、父类、接口、分发目标。
3. 只继续反编译这些必要类。
4. 记录反编译来源路径，方便下游复核。

不要一上来反编译整个项目，除非 class-only 且无法定位入口。

## 需要提取的信息

| 类型 | 提取内容 |
|------|----------|
| 入口类 | 注解、方法签名、HTTP 方法、路径、参数 |
| Action | public 业务方法、字段、setter、ModelDriven 类型、父类字段 |
| DTO | 字段名、类型、嵌套对象、集合泛型、枚举 |
| WebService | public 暴露方法、`@WebMethod`、参数名、返回类型 |
| Dispatch 网关 | switch case、字符串常量、Map key、反射目标 |

## 反编译失败时

1. 尝试从接口、父类、XML、WSDL、schema、调用处补充。
2. 记录失败的 class/JAR 路径和错误原因。
3. 对无法确认的类型标注 `unknown`，不要编造。
4. 如果失败导致无法枚举入口，停止并说明阻塞，不要输出不完整清单冒充完整。

## Gotchas

- 反编译可能丢失参数名；优先用 debug info、接口、注解、WSDL/schema 或调用构造字段恢复。
- Lombok 生成方法不等于 HTTP 参数，字段本身才是 DTO 参数来源。
- 框架继承方法要排除，不要把 `Object`、getter/setter、生命周期方法列为入口。
- class-only 项目仍要遵守 route count 精确数字，不允许 `N+`。
