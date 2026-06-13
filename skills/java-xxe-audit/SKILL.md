---
name: java-xxe-audit
description: 当用户要求审计 Java 源码、字节码或 pipeline 证据中的 XML 外部实体注入、XML 解析器安全配置、SOAP/XML 请求体解析、JAXP/JDOM/dom4j/StAX/JAXB/Transformer/Schema/XStream XML 解析风险时使用；只做路由枚举、调用链追踪、SQL、文件、反序列化、鉴权或组件 CVE 扫描时不要使用。
---

# Java XXE Audit

## 当前定位

`java-xxe-audit` 是 Java 审计体系中的 XML 解析专项判定层。它消费源码、配置、字节码、反编译结果、`java-route-mapper` 路由清单或 `java-route-tracer` 调用链证据，回答：

- 用户可控 XML 是否进入真实 XML 解析、转换、校验或 `fromXML` sink。
- 实际 parser/factory/resolver 是否禁用外部实体、外部 DTD、XInclude 或外部资源访问。
- WebService/SOAP/XML 入口、Content-Type、鉴权上下文和输出条件是否影响结论。
- 风险应标为确认漏洞、条件成立、待验证、不可确认还是非漏洞。
- 对确认漏洞或条件成立风险，给出授权测试环境可复核的 Burp Suite 请求和低风险 XXE payload。

本 skill 不负责全量路由枚举，不替代调用链追踪，不判断鉴权漏洞，不扫描依赖 CVE，不输出未授权攻击、真实敏感文件读取、内网探测、数据外带或拒绝服务 payload。

## 上下游边界

上游输入可以是：

- 用户指定的 Java 项目路径、类、方法、XML 处理器、SOAP/WebService 入口或 XML 工具类。
- `java-route-mapper` 产出的 XML/SOAP 路由、Content-Type 和入口参数。
- `java-route-tracer` 产出的 XML 参数流向、可控性、分支条件和解析 sink 候选。
- `.class`、`.jar`、`.war`、已有反编译结果或 Spring/CXF/JAX-WS 配置。

下游通常读取：

- XXE 审计报告。
- XML 解析器映射、输入来源、防护状态、输出条件和限制说明。
- 确认漏洞或条件成立项的 Burp Suite 请求和 payload，用于授权环境复核。
- 需要继续交给 `java-route-tracer`、`java-auth-audit` 或反编译工作的证据缺口。

相邻 skill 边界：

- `java-route-mapper`：枚举 XML/SOAP/REST 路由；本 skill 只消费路由证据。
- `java-route-tracer`：追踪 XML 输入从入口到解析器；本 skill 只在证据不足时请求追踪，不凭方法名推断可控性。
- `java-auth-audit`：判断入口鉴权、越权或未授权；本 skill 只引用鉴权上下文。
- `java-file-read-audit`：判断文件读取漏洞；XXE 可能导致文件读取，但本 skill 只证明 XML 外部实体解析链。
- `java-deserialization-audit`：判断 XStream/JAXB/JDK 等对象反序列化利用链；本 skill 只判断 XML 外部实体解析维度。
- `java-vuln-scanner`：扫描依赖组件 CVE；本 skill 不编造 CVE、CVSS、修复版本或组件结论。

## 触发条件

满足任一条件时触发：

- 用户明确要求审计 XXE、XML External Entity、外部实体、DTD、SOAP XML、XML parser 安全配置。
- 代码中出现 `DocumentBuilderFactory`、`SAXParserFactory`、`XMLReader`、`SAXReader`、`SAXBuilder`、`XMLInputFactory`、`TransformerFactory`、`SchemaFactory`、`JAXBContext`、`Unmarshaller`、`XStream.fromXML`、`XPathExpression` 等 XML 解析、转换或 XML 反序列化入口。
- `java-route-tracer` 已报告用户输入到达 XML 解析器或 XML 工具类，需要判定是否构成 XXE。
- 项目只有字节码，需要定位 XML 解析类并确认是否配置安全特性。
- 用户给出候选 XML 处理代码，要求判断外部实体是否可被解析。

## 不触发条件

以下情况不要触发本 skill：

- 只要求列出 Controller、Servlet、WebService 路由。
- 只要求追踪参数调用链，不要求判断 XML 解析风险。
- 只看到 XML 文件、Spring bean、SOAP 配置或 `@WebService`，但没有 XML 解析 API 或外部实体处理证据。
- 只审计 SQL、文件上传、文件读取、反序列化、鉴权、SSRF 或组件版本。
- XML 输入只作为字符串透传、日志记录或存储，没有进入解析器。
- 用户要求批量扫描线上目标、未授权攻击、真实敏感文件读取、内网探测、数据外带或拒绝服务 payload。

## 成功标准

合格输出必须同时满足：

- 每个结论都有入口或输入来源、XML 数据可控性、真实解析 sink、防护配置和代码位置。
- 不把 XML 字符串、SOAP 框架、配置文件、类名或未读实现写成 XXE 漏洞。
- WebService/SOAP 入口地址必须来自真实证据，例如 CXF/JAX-WS 配置、`@WebService` 服务名、WSDL 或 route-mapper 输出；不得用类名、接口名或方法名臆造 endpoint path。
- 明确区分确认漏洞、条件成立、待验证、不可确认和非漏洞。
- 对 `DOCTYPE`、外部通用实体、外部参数实体、外部 DTD、XInclude、EntityResolver、accessExternal*、StAX properties 等防护给出证据。
- 对回显、无回显、OOB 条件只做静态可行性描述，不声称验证成功。
- 同根因多入口按 `../java-shared/VULNERABILITY_GROUPING.md` 聚合；不同解析器、入口、防护条件或输出条件拆分。
- `结论统计` 数量必须与 `XML 解析器映射` 中各状态行数一致；SOAP 配置、依赖版本、过滤器状态等非解析 sink 信息不能计入映射。
- 报告严格使用 `references/OUTPUT_TEMPLATE.md` 的 6 个编号章节，不新增 `## 0`、`## 7`、`## 输出自检`、技能源校验或测试验收信息。
- 确认漏洞或条件成立项必须包含 Burp Suite 请求和 payload；待验证、不可确认和非漏洞项不得输出可复制请求。
- 不编造 CVE、CVSS、修复版本、真实文件内容、外带结果、HTTP 响应、漏洞利用成功或不存在的代码路径。
- 正式报告只描述代码证据和证据缺口，不暴露工具权限、网络限制、命令失败、模型规则编号或测试过程。

## 工作流

### 1. 确定审计范围

- 读取用户指定路径、候选入口、上游 route/tracer 报告和配置文件。
- 若没有入口证据，可做 XML 解析器盘点，但结论只能是“待验证/不可确认/非漏洞”，不能写外部可利用。
- 若只有工具类名、XML 文件名或 `UNCONFIRMED` sink，先定位实现源码、字节码或反编译结果。

### 2. 选择 reference

- 解析器和防护规则：读取 `references/PARSERS.md`。
- 源码缺失或只给字节码：读取 `references/DECOMPILE_STRATEGY.md`。
- 需要输出 Burp Suite 请求或 payload：读取 `references/VALIDATION_GUIDE.md`。
- 生成报告前：读取 `references/OUTPUT_TEMPLATE.md`。

### 3. 定位 XML 解析 sink

优先查找真实解析执行点：

- DOM/SAX：`DocumentBuilder.parse`、`SAXParser.parse`、`XMLReader.parse`。
- JDOM/dom4j：`SAXBuilder.build`、`SAXReader.read`。
- StAX：`XMLInputFactory.createXMLStreamReader`、`createXMLEventReader`。
- Transformer/Schema：`TransformerFactory.newTransformer(Source)`、`SchemaFactory.newSchema(Source)`。
- JAXB：`Unmarshaller.unmarshal`，尤其是直接接收 `InputStream`、`Reader`、`StreamSource`、`SAXSource`、`XMLStreamReader` 的路径。
- XStream：`XStream.fromXML`、项目封装的 `XmlUtil.fromXML`；只判定 XML parser 外部实体行为，不展开 gadget 或对象注入利用链。
- XPath/XSLT：解析结果进入 `XPath` 或 `Transformer` 时继续检查源 parser 是否安全。

### 4. 追踪 XML 输入和输出条件

- 输入来源：`request.getInputStream`、`getReader`、`@RequestBody String`、`MultipartFile`、SOAP Body、MQ 消息、数据库 XML 字段、文件上传内容。
- 中间包装：`InputSource`、`StringReader`、`ByteArrayInputStream`、`StreamSource`、`DOMSource`、`SAXSource`、`Source`。
- 输出路径：HTTP response、页面 model、异常信息、日志、业务返回对象、文件写入、外部资源加载条件。
- 若跨层证据不足，切回 `java-route-tracer`；不要凭 `parseXml`、`loadXml`、`handleSoap` 等名称推断可控性。

### 5. 判定防护和执行条件

- 确认安全配置必须在解析器创建后、解析调用前、同一实例或实际使用的 factory 上生效。
- `setValidating(false)`、`setNamespaceAware(true)`、普通 schema 校验、try/catch 吞异常不等于 XXE 防护。
- 自定义 `EntityResolver`、`XMLResolver`、`LSResourceResolver` 只有在实现明确拒绝外部实体时才算防护。
- 解析器创建在安全工厂中，但后续又创建新解析器实例时，要分别判断。
- 数据流缺入口、缺解析 sink、缺防护状态或缺执行条件时，输出待验证或不可确认。

### 6. 输出报告

- 使用 `references/OUTPUT_TEMPLATE.md` 生成 6 个编号章节。
- 对没有确认漏洞的审计，也要输出已检查解析点、候选风险、非漏洞依据、不可确认项和待补证据。
- 确认漏洞或条件成立项按 `references/VALIDATION_GUIDE.md` 输出 Burp Suite 请求和 payload；其他状态只写补证路径。

## Hard Rules

1. 没有真实 XML 解析/转换/反序列化 sink，不得下 XXE 结论。
2. 没有用户可控 XML 输入，不得下 XXE 结论。
3. 没有证据证明外部实体防护缺失或不足，不得下 XXE 结论。
4. `UNCONFIRMED`、工具类名、SOAP endpoint、XML 文件、DTD 字符串或框架依赖只表示候选，不是漏洞。
5. 结论状态必须使用中文枚举：确认漏洞、条件成立、待验证、不可确认、非漏洞。
6. 确认漏洞和条件成立项必须给 Burp Suite 请求和 payload；待验证、不可确认、非漏洞项不得给可复制请求。
7. XXE payload 只能用于授权测试环境低风险复核，使用受控 canary URL 或开发单位创建的无敏感测试文件占位符；不得包含真实敏感文件路径、内网地址、云元数据地址、数据外带、实体扩展 DoS 或批量探测。
8. Burp 请求必须匹配真实入口、HTTP 方法、参数名和 Content-Type；无法确认入口时不得编造请求。
9. 不编造 CVE、CVSS、修复版本、真实文件内容、HTTP 响应或外带回连结果。
10. 反编译证据必须指向真实存在且已读取的源码、反编译文件或 class/jar 来源；路径不存在时只能写不可确认。
11. WebService 路由、SOAP endpoint、operation path 和服务地址必须逐项引用配置证据；只知道 `SZFTWebServiceImpl` 这类类名时，入口只能写“未确认”。
12. `XStream.fromXML` 不得仅因“属于反序列化”写成非漏洞；未确认底层 driver、版本或安全配置时，应标待验证或不可确认，并把 gadget 风险交给反序列化专项。
13. `XStream.addPermission`、`securityFramework`、`allowTypes` 等对象反序列化限制不是 XXE 防护；缺少这些配置不能作为 XXE 防护缺口证据。
14. `XStream.fromXML` 只有在同时确认用户可控 XML、底层 driver/parser 支持外部实体解析且入口路径真实时，才可提升到条件成立；driver 行为或对象 XML 结构未知时最多写待验证。
15. `XML 解析器映射` 的每一行只能有一个结论状态；若同一入口同时有安全 wrapper 和未确认底层 parser，按未确认片段状态记录。
16. 正式报告不得出现 `## 输出自检`、技能源校验、测试提示词、Claude 运行状态、验收清单、工具权限、网络限制、命令失败、模型规则编号、`skill 规则`、`依据 skill` 或 `hard rule`。
17. 正式报告不得列依赖版本清单、组件版本号或“版本 CVE”建议；如需依赖风险，只写“交给组件扫描专项”。
18. 报告全文禁止出现三个连续英文句点；无法完整确认时写中文“省略非关键字段”或限制说明。

## Gotchas

- `@WebService` 或 SOAP 本身不等于 XXE；很多 SOAP 栈由框架解析，业务代码未必能配置 parser。要看业务是否直接解析 XML。
- `@WebService` 类名或接口名不等于访问路径；CXF `jaxws:endpoint address`、Spring bean、WSDL service/port 可能与类名完全不同，未读到真实配置时不要写具体 path。
- `DocumentBuilderFactory.newInstance()` 后如果只调用 `setValidating(false)`，仍不能防 XXE。
- 只禁用 `external-general-entities` 但未禁用 `external-parameter-entities`，不能算完整防护。
- `setExpandEntityReferences(false)` 对 DOM 只是部分防护，不能单独证明安全。
- `TransformerFactory`、`SchemaFactory`、`XMLInputFactory`、`Unmarshaller` 也可能触发外部资源加载，不要只查 5 种经典 parser。
- `XStream.fromXML` 同时横跨 XML 解析和反序列化；XXE 只看 XML parser 外部实体行为，不能因 gadget 风险归属其他 skill 就排除 XML 解析风险。
- `XStream` 缺少 `addPermission` 或 `allowTypes` 是反序列化安全问题，不等同于 XXE；XXE 仍要看底层 XML driver 是否解析外部实体。
- 在 XXE 映射或防护状态中写“无 addPermission/allowTypes/securityFramework”会误导为 XXE 防护缺口；这些词只可作为“交给反序列化专项”的边界说明，正式 XXE 报告中通常不要展开。
- 如果只知道 Struts 通配符约定但没有从 `struts.xml`、action 配置或 route-mapper 确认具体 path，不得输出 Burp 请求；入口写“未确认”。
- 如果无法构造符合 XStream 目标对象结构的完整 XML，确认漏洞/条件成立不能输出半截 payload；应降为待验证并写补证对象结构。
- 自定义 resolver 名为 `SafeEntityResolver` 不代表安全，必须读实现。
- XML 来自配置文件或服务端常量时，通常不是用户可控；可写加固建议，不写漏洞。
- 回显不存在不等于无风险，但只能写 Blind/OOB 条件待验证，不能声称已外带。
- 对待验证项输出 Burp 请求会误导开发单位按确认漏洞处理，属于不合格输出。
- 确认漏洞没有 payload 或 Burp 请求会缺少可复核交付物，属于不合格输出。
- 在 XXE 报告中列组件版本并建议扫描 CVE 会越界到组件扫描；只写“如需依赖风险，交给组件扫描专项”。
- 报告正文写“依据 skill 规则”或列出 `XStream 1.4.3/CXF 2.6.2/JAXB 2.2.5/xpp3` 等版本清单，会暴露内部过程或越界。

## 停止、确认或切换条件

- 找不到实现源码、反编译结果或字节码证据时：停止确认漏洞，输出不可确认。
- 需要先知道 XML 输入是否来自入口时：切换到 `java-route-tracer`。
- 需要判断入口是否未授权或越权时：交给 `java-auth-audit`。
- 用户要求组件版本漏洞或 CVE 时：交给 `java-vuln-scanner`。
- 用户要求真实攻击、批量扫描线上目标、真实敏感文件读取、内网探测、数据外带或拒绝服务 payload 时：拒绝该部分，只保留静态审计和授权环境低风险复核建议。

## Eval

| 类型 | 用户请求或场景 | 预期行为 |
|------|----------------|----------|
| 正例 | “审计这个接口的 XML 解析是否有 XXE。” | 触发，定位入口、解析器、防护和输出条件 |
| 正例 | “检查项目里 DocumentBuilderFactory 有没有禁用外部实体。” | 触发，读取 parser reference 并输出解析器映射 |
| 正例 | “WAR 里只有 class，帮我看 SOAP XML 处理有没有 XXE。” | 触发，读取反编译策略，先定位 XML 处理类 |
| 反例 | “列出所有 WebService operation。” | 不触发，使用 `java-route-mapper` |
| 反例 | “追踪这个 XML 字符串到哪个方法。” | 不触发或仅上游，使用 `java-route-tracer`；若要求判定 XXE 再触发 |
| 反例 | “检查 xstream 版本 CVE。” | 不触发，使用 `java-vuln-scanner` |
| 边界例 | `DocumentBuilderFactory` 解析服务端固定 XML 配置 | 记录解析点，通常非漏洞或加固建议 |
| 边界例 | `SAXReader` 无防护但输入来自数据库 XML 字段 | 待验证或条件成立，取决于数据库字段是否外部可控 |
| 边界例 | SOAP endpoint 存在，但业务代码未直接解析 XML | 不下 XXE 结论，记录框架解析边界 |
| 失败案例 | 把所有 `parse()` 命中都写成确认漏洞 | 不合格，缺输入可控性和防护分析 |
| 失败案例 | 确认漏洞或条件成立项没有 Burp Suite 请求和 payload | 不合格，缺少开发单位复核材料 |
| 失败案例 | 待验证或不可确认项输出可复制 Burp 请求 | 不合格，候选风险被包装成已确认漏洞 |
| 失败案例 | 输出真实文件读取、内网探测、数据外带、DoS payload、CVSS、CVE、修复版本或模型自检章节 | 不合格，违反输出边界 |
| 失败案例 | 把 XStream 缺少 `addPermission` 当成 XXE 防护缺口，或在 driver 行为未知时写条件成立 | 不合格，混淆反序列化与 XXE |
| 失败案例 | 根据 Struts 约定猜测 `/admin/access_addOrg.action` 并输出 Burp 请求 | 不合格，入口证据不足 |
| 失败案例 | Payload 只给 DOCTYPE 片段，未嵌入目标对象 XML 结构 | 不合格，不可直接复核 |
| 失败案例 | 报告写“依据 skill 规则”或列依赖版本清单 | 不合格，暴露内部过程或组件扫描越界 |
