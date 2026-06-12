# XXE 审计反编译策略

源码缺失、只有 `.class/.jar/.war` 或上游调用链停在 XML 工具类、SOAP handler、Manager/Service 方法时加载本文件。目标是补足 XML 解析实现、防护配置和输入来源证据，不是全量反编译项目。

通用反编译工具选择、CFR 获取方式和失败处理可参考 `../java-shared/DECOMPILE_STRATEGY.md`。本文件只描述 XXE 审计的目标选择和证据记录。

## 何时需要反编译

必须考虑反编译：

- `java-route-tracer` 只追踪到 `UNCONFIRMED` XML sink、XML 工具类、SOAP handler 或 Manager/Service 方法。
- 源码缺少实现类，但 `WEB-INF/classes`、`BOOT-INF/classes`、`target/classes`、`build/classes` 中存在字节码。
- XML 解析逻辑在业务 jar、公共工具 jar、WebService jar 或部署包中。
- 需要确认 `setFeature`、resolver、`XMLInputFactory` property、`accessExternal*` 是否在真实实例上生效。

不需要反编译：

- 源码、配置或反编译结果已经能证明解析器、防护和输入来源。
- 只缺少 JDK/JAXP/dom4j/JDOM 框架核心类。
- 当前任务只做路由枚举或调用链追踪，不做 XXE 判定。

## 目标优先级

| 优先级 | 目标 | 原因 |
|--------|------|------|
| P0 | 上游调用链直接命中的 XML 解析类 | 最可能决定当前结论 |
| P0 | `*Xml*`、`*XML*`、`*Parser*`、`*Sax*`、`*Dom*` 工具类 | 常见解析封装 |
| P1 | Servlet/Controller/Action/WebService/Endpoint/Handler | 补足入口和输入来源 |
| P1 | SOAP/CXF/JAX-WS handler、Interceptor | 可能处理原始 XML |
| P2 | Service/Manager 调用方 | 补足参数传递和分支条件 |
| P2 | 自定义 EntityResolver/XMLResolver/LSResourceResolver | 判断 resolver 是否真正拒绝外部实体 |

## 定位方法

先用轻量搜索定位候选：

```bash
find . -name "*Xml*.class" -o -name "*XML*.class" -o -name "*Parser*.class" -o -name "*Sax*.class" -o -name "*Dom*.class"
find . -name "*Servlet.class" -o -name "*Controller.class" -o -name "*Action.class" -o -name "*WebService*.class" -o -name "*Handler.class"
rg -a "DocumentBuilderFactory|SAXParserFactory|XMLReaderFactory|SAXReader|SAXBuilder|XMLInputFactory|TransformerFactory|SchemaFactory|Unmarshaller|InputSource|StreamSource" .
```

从配置定位：

- `web.xml` servlet/filter/listener。
- Spring XML `<bean class="com.example.XmlParser">`。
- CXF/JAX-WS endpoint、interceptor、handler chain。
- `applicationContext.xml` 中的 XML 工具 bean。

## 反编译范围控制

推荐顺序：

1. 只反编译当前入口调用链或搜索命中的 1 到 5 个 XML 候选类。
2. 如果解析逻辑在工具类，补充反编译调用方以确认输入来源。
3. 如果存在自定义 resolver，补充反编译 resolver。
4. 如果仍找不到解析 sink 或防护配置，记录不可确认，不扩大为确认漏洞。

避免：

- 无条件反编译整个 `WEB-INF/lib`。
- 因类名包含 `Xml` 就输出漏洞。
- 在反编译失败时编造源码行号、调用链或解析器配置。
- 引用不存在的 `decompiled` 路径作为证据。

## 证据记录

报告中必须标注：

| 项目 | 写法 |
|------|------|
| 来源文件 | `来源：反编译 WEB-INF/classes/com/acme/XmlParser.class` |
| 行号 | 有行号写反编译文件行号；无行号写“反编译结果无可靠源码行号” |
| 可信度 | 说明是否混淆、反编译失败、注解缺失、方法体缺失 |
| 限制 | 缺入口、缺 resolver 实现、缺防护分支时明确标注 |

证据路径必须真实存在，或能明确指向已读取的 class/jar 来源。若只看到 class 文件但未成功反编译，实现证据仍为缺失，结论应为“不可确认”。

## 反编译后检查清单

优先提取：

- XML parser/factory 创建位置。
- `parse`、`read`、`build`、`unmarshal`、`transform`、`newSchema` 等执行点。
- `setFeature`、`setProperty`、`setAttribute`、`setExpandEntityReferences`、`setXIncludeAware`、`setEntityResolver`。
- `XMLConstants.ACCESS_EXTERNAL_DTD`、`ACCESS_EXTERNAL_SCHEMA`、`ACCESS_EXTERNAL_STYLESHEET`。
- 输入包装：`InputStream`、`Reader`、`StringReader`、`InputSource`、`StreamSource`、`SAXSource`。
- 输出路径：response、model、返回对象、日志、异常、文件写入。
- 分支条件：Content-Type、文件后缀、配置开关、角色、异常路径。

## 失败处理

| 情况 | 处理 |
|------|------|
| 找不到 class/jar | 记录缺失实现，不下漏洞结论 |
| 反编译失败 | 记录“未取得可用反编译结果”和受影响类，结论降为不可确认；正式报告不展开工具授权、权限弹窗、网络或命令细节 |
| 字节码只出现 parser 字符串 | 作为候选，不下漏洞结论 |
| 只反编译到调用方 | 不能按调用方名称推断 parser 防护，目标仍不可确认 |
| 自定义 resolver 未读 | 不把 resolver 当安全防护 |
| 多个 parser 实现 | 分别列出已确认和未确认实现，不混成一个结论 |

## 与 `UNCONFIRMED` 的关系

如果上游 `java-route-tracer` 把 sink 标为 `UNCONFIRMED`，本 skill 必须先完成以下任一项后才能判 XXE：

- 找到源码实现并确认 XML 解析 sink。
- 找到反编译实现并确认 XML 解析 sink 和防护配置。
- 找到配置或字节码证据，能同时证明解析 sink、输入来源和防护状态。

若三者都没有，输出“不可确认：缺少 XML 解析实现证据”，不得写“疑似 XXE 已确认”。

正式报告中不要写 `CFR`、`javap`、`procyon` 等工具不可用、网络受限、命令受限或权限失败；这些属于测试过程。面向开发单位的写法应是“本轮未取得关键类可读实现/反编译方法体，无法确认输入来源、解析 sink 和防护配置”。
