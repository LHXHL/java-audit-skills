# 组件与 Gadget 条件

组件命中只是风险信号，必须结合触发点、输入可控性和环境条件确认可利用性。

## 常见组件条件

| 组件/链 | 风险条件 | 必查前提 |
|---------|----------|----------|
| CommonsCollections CC1 | `commons-collections` 3.x，依赖 `AnnotationInvocationHandler` 链，常受 JDK 版本影响 | JDK 版本、是否存在原生反序列化入口、是否可加载 gadget 类 |
| CommonsCollections CC6 | `commons-collections` 3.2.1 常见，`HashMap`/`TiedMapEntry`/`LazyMap` 链 | 入口可控、gadget 类存在、是否被安全补丁/类过滤阻断 |
| CC4/TemplatesImpl | `commons-collections4`、`TemplatesImpl`、`TrAXFilter`、`PriorityQueue` 相关链 | JDK 模块限制、类加载条件、是否能加载字节码 |
| Fastjson | `fastjson` 低版本、autoType 可用或可绕过、危险类可达 | `@type` 是否进入解析，是否固定目标类，ParserConfig 配置 |
| XStream | 多个 1.4.x 低版本 CVE，默认宽松类型权限 | 是否调用 `fromXML`，是否启用 `setupDefaultSecurity` 和 `allowTypes` |
| XMLDecoder | JDK 内置，无需第三方依赖 | XML 输入是否可控，是否直接调用 `readObject()` |
| JDBC/MySQL | MySQL Connector/J 5.1.x、8.0 低版本等 | JDBC URL/属性是否可控，是否存在测试连接/动态数据源 |
| PostgreSQL JDBC | `socketFactory` / `sslfactory` 等参数相关代码执行风险 | URL 参数是否可控，驱动版本，类是否在 classpath |
| H2/DB2/JNDI | H2 Console/JNDI、DB2 JNDI 注入等 | 数据源配置是否可控，JNDI 是否可达 |
| Shiro RememberMe | Shiro 低版本、默认或泄露 AES key、gadget 存在 | Cookie 可控、key 是否可得、rememberMe 是否启用 |
| Log4j/JNDI | Log4j2 2.0-2.14.1 等，JNDI lookup 可触发 | 可控日志输入、JNDI 是否启用、出网/RMI/LDAP 条件 |

## Gadget 链审计要点

Gadget 链成立必须同时满足：可控入口、自动触发点、可达危险原语、组件/JDK 条件、防护未阻断。不要把依赖存在等同于 RCE。

### 触发方法

重点扫描并追踪这些反序列化后可能自动执行的方法：

```text
readObject
readResolve
readExternal
hashCode
equals
compareTo
toString
finalize
writeReplace
validateObject
```

### 危险原语

链条终点优先确认是否到达：

```text
Runtime.exec
ProcessBuilder
Method.invoke
Constructor.newInstance
ClassLoader#defineClass
URLClassLoader
TemplatesImpl
newTransformer
InitialContext.lookup
ScriptEngine.eval
Expression.getValue
Ognl.getValue
MVEL.eval
JexlExpression.evaluate
```

### 容器与自动触发点

这些类型常把对象方法自动触发出来，但必须确认对象会被实际放入该容器或反序列化流程：

```text
HashMap
HashSet
Hashtable
PriorityQueue
TreeMap
TreeSet
BadAttributeValueExpException
AnnotationInvocationHandler
EventListenerList
SignedObject
Proxy
Comparator
InvocationHandler
```

### 第三方 gadget 组件

命中以下依赖时，记录版本和链条条件，但不要单独判漏洞：

| 组件 | 关注点 |
|------|--------|
| CommonsCollections 3/4 | `Transformer`、`InvokerTransformer`、`LazyMap`、`TiedMapEntry`、`ChainedTransformer` |
| CommonsBeanutils | `BeanComparator`、`PropertyUtils`，通常需要排序/比较触发点 |
| Groovy | `ConvertedClosure`、`MethodClosure`、动态方法调用 |
| Spring AOP/Core | 代理、反射调用、SpEL、BeanFactory 相关链 |
| C3P0 | `ReferenceIndirector`、JNDI/URLClassLoader 条件 |
| Rome | `ToStringBean`、`EqualsBean`、`ObjectBean` |
| Vaadin | 反射/属性访问相关链 |
| Hibernate | `TypedValue`、getter/equals/hashCode 触发面 |
| Javassist | 字节码生成和类加载条件 |
| AspectJ | `AspectJWeaver` 文件写入链条件 |
| Xalan/TemplatesImpl | `TemplatesImpl.newTransformer`，受 JDK 和模块限制影响 |

### 自定义 gadget 审计流程

1. 先确认入口：谁执行反序列化或允许类型声明。
2. 再确认候选类：classpath 中哪些应用类或第三方类可被实例化。
3. 再确认触发方法：反序列化后是否自动调用 `readObject/hashCode/compareTo/toString` 等。
4. 再确认危险原语：是否可到反射、命令、JNDI、类加载、模板、脚本/表达式执行。
5. 最后确认阻断条件：白名单、黑名单、`ObjectInputFilter`、JDK 模块限制、组件补丁、签名/HMAC。

## JDBC 反序列化审计要点

JDBC 场景不要误判成普通 SQL 注入。重点是攻击者是否能控制连接串或连接属性：

- 数据源管理后台：新增/测试连接/编辑 JDBC URL。
- 报表系统：用户配置外部数据库。
- 多租户动态数据源：租户参数影响 URL、driverClass、properties。
- 配置导入：上传配置后自动连接数据库。

危险关键词：

```text
jdbc:mysql://
autoDeserialize
queryInterceptors
statementInterceptors
detectCustomCollations
socketFactory
sslfactory
dataSourceName
```

## 误报排除

- 只有依赖版本命中，但项目没有对应 sink 或入口：报告为组件风险待确认，不作为代码漏洞。
- 只有 CommonsCollections/Beanutils 等 gadget 组件，但没有可控反序列化入口：列为组件风险或安全摘要，不判 RCE。
- 有 `readObject/hashCode/toString` 等方法，但没有容器触发点或反序列化流程：列为自定义 gadget 线索，不判完整链。
- 有危险原语，但输入不可控或参数不能影响危险调用：降低风险并说明断点。
- 只有内部管理员配置可控：按认证和权限降低可达性，不要直接判无认证 RCE。
- 只有测试代码、样例代码、不可部署模块：列为不可达或低风险说明。
- 已启用类型白名单、对象过滤器、禁用 JNDI/autoType：必须说明防护证据。
