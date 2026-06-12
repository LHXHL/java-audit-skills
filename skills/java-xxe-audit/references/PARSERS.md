# XML 解析器 XXE 审计规则

本文件用于 `java-xxe-audit` 已触发后加载。结论必须回到真实项目证据：入口或输入来源、XML 解析 sink、防护配置、执行路径和限制说明。

## 证据模型

| 证据 | 必须回答的问题 | 不足时结论 |
|------|----------------|------------|
| XML 输入来源 | XML 是否来自 HTTP/SOAP/RPC/MQ/上传/数据库外部字段 | 待验证或不可确认 |
| 解析 sink | 具体哪个 parser/transformer/unmarshaller 执行解析 | 不得下 XXE 结论 |
| 防护配置 | 是否在实际 parser/factory 上禁用 DOCTYPE 或外部实体 | 不得下确认漏洞 |
| 执行路径 | 输入是否能到达该解析器，分支是否成立 | 待验证或不可确认 |
| 入口地址 | Web/SOAP/MQ 入口是否来自配置、注解、WSDL 或 route-mapper 证据 | 入口写“未确认”，不得按类名推断 |
| 输出条件 | 解析结果是否回显、存储、日志、触发外部请求 | 只影响风险说明，不替代前四项 |

状态必须用中文：确认漏洞、条件成立、待验证、不可确认、非漏洞。

一条映射行只能有一个状态。若同一入口同时有安全 wrapper 和未确认底层 parser，按未确认片段状态记录为“待验证”或“不可确认”，并在依据中说明安全部分；不要写混合状态。

## 通用有效防护

优先接受以下防护：

- 禁用 DOCTYPE：`http://apache.org/xml/features/disallow-doctype-decl = true`。
- 同时禁用通用外部实体和参数外部实体。
- 禁止外部 DTD 加载：`http://apache.org/xml/features/nonvalidating/load-external-dtd = false`，通常作为补充。
- JAXP 1.5+ 的 `XMLConstants.ACCESS_EXTERNAL_DTD`、`ACCESS_EXTERNAL_SCHEMA`、`ACCESS_EXTERNAL_STYLESHEET` 设置为空字符串。
- StAX 的 `XMLInputFactory.SUPPORT_DTD = false` 和 `IS_SUPPORTING_EXTERNAL_ENTITIES = false`。
- 自定义 resolver 明确拒绝外部实体或只返回本地安全空源。

不足或不能单独证明安全：

- `setValidating(false)`。
- `setNamespaceAware(true)`。
- 只设置 `setExpandEntityReferences(false)`。
- 只禁用一种外部实体。
- 在异常处理或解析之后设置 feature。
- resolver 名称像 `SafeResolver`，但没有读取实现。
- 依赖新 JDK 或新库默认值，但项目运行版本未确认。

## DOM: DocumentBuilderFactory

识别：

```java
DocumentBuilderFactory.newInstance()
factory.newDocumentBuilder()
builder.parse(input)
```

重点：

- `factory.setFeature` 必须发生在 `newDocumentBuilder()` 之前。
- `setExpandEntityReferences(false)` 只能作为补充。
- `builder.setEntityResolver(resolver)` 需要读取 resolver 实现。

安全示例：

```java
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
DocumentBuilder builder = factory.newDocumentBuilder();
```

误判点：

- 看到 `DocumentBuilderFactory` 但 XML 来源是服务端固定配置，通常不是用户可控漏洞。
- 看到 `parse(File)` 时要确认文件路径是否用户可控；若只是本地配置文件，最多是加固建议。

## SAX: SAXParserFactory / XMLReader

识别：

```java
SAXParserFactory.newInstance()
factory.newSAXParser()
parser.parse(input, handler)
XMLReaderFactory.createXMLReader()
xmlReader.parse(inputSource)
```

重点：

- `SAXParserFactory` 的 feature 应配置在 factory 上并在 `newSAXParser()` 前完成。
- `XMLReader` 的 feature 应配置在实际调用 `parse()` 的 reader 上。
- `SAXParserFactory.setNamespaceAware`、`setValidating(false)` 不是 XXE 防护。

安全示例：

```java
SAXParserFactory factory = SAXParserFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
SAXParser parser = factory.newSAXParser();
```

## dom4j: SAXReader

识别：

```java
new SAXReader()
reader.read(input)
```

重点：

- `reader.setFeature` 必须在 `read()` 前调用。
- dom4j 版本不同默认行为不同，不要只凭版本推断安全。
- XPath、`elementText`、`getText` 是结果使用路径，不是解析 sink 本身。

安全示例：

```java
SAXReader reader = new SAXReader();
reader.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
reader.setFeature("http://xml.org/sax/features/external-general-entities", false);
reader.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
```

## JDOM/JDOM2: SAXBuilder

识别：

```java
new SAXBuilder()
builder.build(input)
```

重点：

- 旧 `org.jdom.input.SAXBuilder` 与 JDOM2 行为不同，要看依赖版本和配置。
- JDOM2 部分版本默认更安全，但仍应以显式配置或版本证据为准。

安全示例：

```java
SAXBuilder builder = new SAXBuilder();
builder.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
builder.setFeature("http://xml.org/sax/features/external-general-entities", false);
builder.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
```

## StAX: XMLInputFactory

识别：

```java
XMLInputFactory.newInstance()
factory.createXMLStreamReader(input)
factory.createXMLEventReader(input)
```

安全配置：

```java
XMLInputFactory factory = XMLInputFactory.newInstance();
factory.setProperty(XMLInputFactory.SUPPORT_DTD, false);
factory.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
```

Gotchas：

- `IS_COALESCING`、`IS_NAMESPACE_AWARE` 不防 XXE。
- Woodstox 等实现的默认值可能不同，仍需配置或版本证据。

## TransformerFactory / SchemaFactory

识别：

```java
TransformerFactory.newInstance()
factory.newTransformer(new StreamSource(input))
SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI)
factory.newSchema(new StreamSource(input))
```

安全配置：

```java
factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
factory.setAttribute(XMLConstants.ACCESS_EXTERNAL_STYLESHEET, "");
factory.setProperty(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
```

Gotchas：

- `TransformerFactory` 处理 XSLT 时可能加载外部 stylesheet 或 DTD。
- `SchemaFactory` 验证 XML Schema 时可能加载外部 schema 或 DTD。
- 只看到 `transform` 输出到 response 不等于 XXE；仍要看输入 Source 是否可控。

## JAXB / Unmarshaller

识别：

```java
JAXBContext.newInstance(User.class)
Unmarshaller unmarshaller = context.createUnmarshaller()
unmarshaller.unmarshal(input)
```

风险重点：

- 直接 `unmarshal(InputStream)`、`unmarshal(Reader)`、`unmarshal(StreamSource)` 需要确认底层 parser 安全。
- 如果先用安全 `DocumentBuilderFactory` 解析，再传入 `Document`，通常更安全。
- `XMLStreamReader` 由外部传入时，要检查创建它的 `XMLInputFactory` 配置。

## XStream.fromXML

识别：

```java
XStream xstream = new XStream();
xstream.fromXML(xml);
projectXmlUtil.fromXML(xml, target);
```

重点：

- `fromXML` 是 XML 解析入口，也是对象反序列化入口；本 skill 只判断 XML 外部实体维度，gadget、任意类型实例化、权限 bypass 交给反序列化专项。
- 必须确认底层 driver 或 parser，例如 XPP、DomDriver、StaxDriver、JAXP parser，以及项目是否显式配置安全 driver、converter、permission 或 parser feature。
- 只看到 `XStream.fromXML(String)` 和用户可控 XML，但无法确认底层 driver 外部实体行为时，标“待验证”，不要直接写“非漏洞”。
- 只有能证明输入不可控、底层 parser 安全配置充分，或 `fromXML` 未被执行，才可写“非漏洞”。
- 不输出 gadget 类名、链式 payload、组件 CVE、CVSS 或修复版本。
- `addPermission`、`allowTypes`、`denyTypes`、`securityFramework` 主要约束对象类型和反序列化权限，不是 XXE 外部实体防护；缺少这些配置不能作为 XXE 防护缺口证据。
- 若未确认 XStream driver/parser 是否支持外部实体解析，结论最高为“待验证”，不能写“条件成立”。
- 若无法确认目标对象 XML 结构，不能输出半截 `DOCTYPE` payload 或猜测对象字段；保留在第 4 节并补证对象结构。
- 正式 XXE 报告不列 XStream、XPP3、CXF、JAXB 等具体版本清单；如需版本风险，交给组件扫描专项。

误判点：

- 把 `XmlUtil.fromXML` 全部交给反序列化专项，忽略它仍然会解析 XML。
- 只凭 `xstream-1.4.x.jar` 文件名判定安全或不安全。
- 把 XStream 缺少 `addPermission`、`allowTypes` 或 security framework 当作 XXE 防护缺口。
- 在底层 XStream driver 行为未知、对象 XML 结构未知时输出 Burp 请求和 payload。
- 看到 `processAnnotations`、`alias`、DTO 注解就写 XXE；这些只说明映射关系，不说明外部实体行为。
- 在 XXE 报告正文写“依据 skill 规则”、`hard rule` 或列组件版本清单。

## 输入来源判断

高可控来源：

- `HttpServletRequest.getInputStream()` / `getReader()`。
- `@RequestBody String`、`@RequestBody byte[]`。
- `request.getParameter("xml")` 或 XML 字段。
- `MultipartFile.getInputStream()`。
- SOAP Body、RPC/MQ 消息体。

间接可控来源：

- 数据库中的 XML 字段。
- 文件上传后再解析的 XML。
- 第三方系统回调。

SOAP/WebService 入口：

- CXF/Spring 项目优先读取 `<jaxws:endpoint address="/Service">`、`<jaxrs:server address="/api">`、servlet mapping、WSDL service/port 或 route-mapper 输出。
- `@WebService` 的类名、接口名、实现类名、targetNamespace 只能证明服务类型和 operation 候选，不等于 HTTP 访问 path。
- 如果只知道 `FooWebServiceImpl` 或 `synchroXxx` 方法，没有配置地址证据，报告入口写“未确认”，不要拼出 `/FooWebService`。

通常不可控：

- classpath 下固定配置 XML。
- 服务端硬编码 XML。
- 只由部署人员维护的 Spring 配置。

`XML 解析器映射` 只记录真实 XML parser/transformer/unmarshaller/fromXML sink 或候选 XML sink。SOAP 配置、依赖版本、WebService 路由、过滤器状态等上下文信息可以放在审计概述、候选依据或审计结论中，但不要作为映射行，也不要计入非漏洞数量。

## 回显和 OOB 条件

回显证据：

- `response.getWriter()`、`OutputStream`、`model.addAttribute`、返回 DTO 字段。
- XML 节点值进入异常信息或业务返回。
- 整个 DOM/XSLT 转换结果写回 HTTP 响应。

无回显：

- 可以写“Blind/OOB 条件待验证”，但不要声称触发了外带。
- 确认漏洞或条件成立项可以按 `VALIDATION_GUIDE.md` 输出受控 canary payload；待验证、不可确认和非漏洞项不能输出可复制请求或 payload。
- 不输出真实外带服务器、真实敏感文件路径、内网地址、云元数据地址、数据外带模板或实体扩展 DoS。
- 授权验证说明应标注“仅限授权测试环境”，预期观察只能写受控 canary 请求、resolver 拒绝日志、受控解析错误或业务返回差异，不得声称已验证成功。

## 常见误判

- 把所有 `parse()` 命中写成 XXE，未确认 XML 来源。
- 把 `setValidating(false)` 当作安全防护。
- 把 `@WebService` 或 SOAP endpoint 本身当作 XML 解析 sink。
- 用 WebService 类名、接口名或方法名臆造 endpoint path，而没有引用 CXF/JAX-WS/WSDL/route-mapper 证据。
- 没有读取 resolver 实现就认为自定义 resolver 安全。
- 看到 `DocumentBuilderFactory` 解析固定配置文件就写漏洞。
- 只凭依赖版本推断安全或不安全，缺少实际 parser 配置证据。
- 把 `XStream.fromXML` 写成“非 XXE”而未确认底层 driver 或 parser 外部实体行为。
- 待验证或不可确认项输出 Burp 请求、DOCTYPE payload、外部实体 payload。
- 确认漏洞或条件成立项没有 Burp Suite 请求和低风险 payload。
- 报告写工具权限、网络限制、命令失败、模型规则编号或测试过程，而不是代码证据和证据缺口。
- 在 XXE 报告中展开组件版本、CVE 编号或 CVSS 事项；这些属于组件扫描边界。
