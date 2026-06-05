# 反序列化 Sink 识别规则

只在命中 sink 后做局部追踪；不要按固定类型优先级盲扫。若已有 `route_tracer` 输出，以 `Sink类型 = DESERIALIZE` 为最高可信证据。

## 全类型覆盖要求

反序列化审计不能只扫 `.java`。以下任一条件存在时，必须同时检查源码、字节码字符串、配置入口和按需反编译结果：

- 项目包含 `WEB-INF/classes`、`WEB-INF/lib`、war 解包目录、只给 `.class` 无源码的模块。
- 存在 WebService、Struts 通配 Action、Spring MVC/REST、Servlet/Filter/Listener、MQ/RPC/Dubbo/Hessian/RMI、上传/导入/配置同步入口。
- 组件命中 XStream、Fastjson、Shiro、Log4j、JDBC、ActiveMQ/JMS、CommonsCollections/BeanUtils/Javassist 等反序列化相关依赖。

禁止用这些结论结束审计：

- “`rg --type java` 无命中，所以无 sink。”
- “只发现 DTO 注解/配置项，所以没有调用。”
- “只发现组件版本，未继续追调用链。”
- “只扫了已反编译的少量类，未覆盖部署包中的 `.class`。”

命中以下任一线索必须继续追踪使用类并按需反编译：

- XStream: `@XStreamAlias`、`XStreamImplicit`、`XStreamAsAttribute`、`fromXML`、`XmlUtil.fromXML`。
- 原生/JMS: `ObjectInputStream`、`readObject`、`readUnshared`、`readExternal`、`ObjectMessage`、`getObject`、`ActiveMQObjectMessage`。
- Fastjson/Jackson/YAML: `JSON.parse*`、`@type`、`ParserConfig`、`enableDefaultTyping`、`activateDefaultTyping`、`Yaml.load`。
- JDBC: 动态 `DriverManager.getConnection`、可控 `DataSource`、连接测试接口、外部导入的 JDBC URL/Properties。
- Shiro/Log4j/JNDI: rememberMe 配置、`CookieRememberMeManager`、`cipherKey`、`JndiLookup`、可控输入进入 logger。
- Gadget: `InvokerTransformer`、`LazyMap`、`TiedMapEntry`、`BeanComparator`、`TemplatesImpl`、`Method.invoke`、`PriorityQueue`、`BadAttributeValueExpException`、自定义 `readObject/hashCode/compareTo/toString`。

## Sink 表

| 类型 | 关键词 | 高危输入来源 | 重点判断 |
|------|--------|--------------|----------|
| 原生 Java | `ObjectInputStream`, `readObject`, `readUnshared`, `readExternal` | HTTP Body、Cookie、Header、上传文件、MQ/RPC、缓存导入 | 输入是否用户可控，是否有 `ObjectInputFilter` 或类白名单 |
| 自定义对象钩子 | `private void readObject`, `readResolve`, `readExternal` | 间接被原生反序列化触发 | 钩子中是否调用命令、JNDI、反射、文件、网络、模板等危险逻辑 |
| XMLDecoder | `java.beans.XMLDecoder`, `new XMLDecoder`, `readObject()` | XML 导入、配置恢复、表单/流程设计器、上传 XML | XML 是否可控，是否直接实例化对象和调用方法 |
| Fastjson | `JSON.parse`, `JSON.parseObject`, `@type`, `SupportAutoType`, `ParserConfig` | JSON Body、参数中的 JSON 字符串、接口转发数据 | 是否启用 autoType，是否有危险类可达，是否限定目标类型 |
| XStream | `new XStream`, `fromXML`, `XStream.setupDefaultSecurity` | XML Body、导入接口、Struts2 REST | 是否使用白名单 `allowTypes`，是否是危险版本，XML 是否可控 |
| JDBC | `DriverManager.getConnection`, `DataSource.getConnection`, 动态 JDBC URL, `socketFactory`, `sslfactory`, `dataSourceName` | 数据源测试、报表系统、配置接口、租户动态数据源 | URL/属性是否可控，驱动版本和参数是否满足反序列化/JNDI/代码执行条件 |
| Shiro RememberMe | `rememberMe`, `CookieRememberMeManager`, `AesCipherService`, `cipherKey` | Cookie | Shiro 版本、AES key 是否默认/泄露、gadget 是否存在 |
| Log4j/JNDI | `${jndi:`, `JndiLookup`, `lookup`, `logger.*` | 可控日志字段、User-Agent、参数、异常消息 | Log4j 版本、JNDI 是否启用、出网/RMI/LDAP 条件 |
| Gadget 链 | `commons-collections`, `commons-beanutils`, `InvokerTransformer`, `LazyMap`, `TiedMapEntry`, `BeanComparator`, `TemplatesImpl`, `PriorityQueue`, `BadAttributeValueExpException` | 原生反序列化、JMS ObjectMessage、Shiro RememberMe、XStream/Fastjson/Jackson 类型构造入口 | 是否同时具备可控入口、自动触发方法、危险原语、组件/JDK 条件和未被过滤的链条 |

## 命令扫描建议

以下只是起点，不是完整证明。命令必须结合入口枚举、字节码扫描、反编译和调用链追踪使用。

```bash
rg -n "ObjectInputStream|readObject\\(|readUnshared\\(|readExternal\\(" .
rg -n "XMLDecoder|new XMLDecoder|\\.readObject\\(" .
rg -n "JSON\\.parse|JSON\\.parseObject|SupportAutoType|@type|ParserConfig" .
rg -n "new XStream|fromXML|setupDefaultSecurity|allowTypes" .
rg -n "DriverManager\\.getConnection|DataSource|getConnection\\(|socketFactory|sslfactory|dataSourceName" .
rg -n "rememberMe|CookieRememberMeManager|AesCipherService|cipherKey" .
rg -n "JndiLookup|\\$\\{jndi:|lookup\\(|logger\\.(info|error|warn|debug)" .
rg -n "InvokerTransformer|LazyMap|TiedMapEntry|BeanComparator|TemplatesImpl|newTransformer|Method\\.invoke|PriorityQueue|BadAttributeValueExpException" .
rg -n "readObject\\(|readResolve\\(|readExternal\\(|hashCode\\(|compareTo\\(|toString\\(|writeReplace\\(" .
rg -a -n "ObjectInputStream|readObject\\(|XMLDecoder|fromXML|ObjectMessage|getObject\\(|JndiLookup|\\$\\{jndi:" . -g "*.class"
rg -n "jaxws:endpoint|CXFServlet|StrutsPrepareAndExecuteFilter|MessageListener|Hessian|RMI|Dubbo|JmsTemplate" . -g "*.xml" -g "*.properties"
```

## 可控性判断

高危可控来源包括：
- `request.getInputStream()`, `getReader()`, `getParameter()`, `@RequestBody`, `MultipartFile`
- Cookie/Header，尤其 `rememberMe`、`User-Agent`、自定义 token
- 管理后台的配置导入、数据源测试、报表连接、流程/表单设计
- MQ/RPC/Dubbo/HTTP 客户端回调中的外部消息

降低风险或排除条件：
- 输入来自固定本地文件且路径不可控。
- 反序列化前有签名校验、HMAC、加密完整性校验。
- 明确类白名单或 `ObjectInputFilter` 生效。
- Fastjson 禁用 autoType 且目标类型固定为安全 DTO。
- XStream 启用严格白名单，且危险类型不可达。
