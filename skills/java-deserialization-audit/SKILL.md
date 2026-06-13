---
name: java-deserialization-audit
description: 用于 Java 反序列化漏洞深度审计。用户要求分析 DESERIALIZE sink、ObjectInputStream/readObject、XMLDecoder、Fastjson、XStream、JDBC 反序列化、Shiro RememberMe、Log4j/JNDI 或 gadget 链可利用性时触发；纯组件 CVE 查询、XXE 或 SQL 注入审计不触发。
---

# Java 反序列化漏洞审计

审计 Java 项目中的反序列化风险，输出入口可达性、用户可控性、sink、组件/JDK/gadget 条件、可利用性、Burp 请求和 payload。组件版本命中只能作为输入证据，不能直接判定漏洞成立。

## 触发与边界

触发场景：
- 用户要求审计 Java 反序列化漏洞、反序列化 RCE、gadget 链、ysoserial 链或 `DESERIALIZE` sink。
- 用户点名 `ObjectInputStream/readObject`、`XMLDecoder`、Fastjson、XStream、JDBC 反序列化、Shiro RememberMe、Log4j/JNDI。
- Pipeline 阶段4中，`route_tracer` 出现 `DESERIALIZE` sink，或 `vuln_scanner` 命中反序列化相关组件。

不触发场景：
- 只查依赖版本/CVE：使用 `java-vuln-scanner`。
- 只做路由提取：使用 `java-route-mapper`。
- 只追踪调用链、不判断漏洞：使用 `java-route-tracer`。
- 只审计 XML 外部实体：使用 `java-xxe-audit`。
- 只审计 SQL/JDBC SQL 注入：使用 `java-sql-audit`。

XStream/XMLDecoder 属于反序列化审计；普通 XML 外部实体属于 XXE 审计。

## 输入优先级

如果存在 `{project_name}_audit/`，必须按顺序读取前序输出：

1. `route_mapper/`：路由、HTTP 方法、参数结构、Burp 请求模板。
2. `route_tracer/`：`Sink类型 = DESERIALIZE`、参数可控性、调用链、分支条件。
3. `vuln_report/`：Fastjson、XStream、Shiro、Log4j、JDBC、CommonsCollections 等版本风险。
4. `cross_analysis/`：高危路由、鉴权绕过、组件漏洞与路由关联。

没有前序输出时，不强制运行 `java-route-mapper`。先命令扫描 sink、依赖和入口，再对命中分支局部追踪输入来源。Sink 细则见 [DESERIALIZATION_SINKS.md](references/DESERIALIZATION_SINKS.md)，组件条件见 [COMPONENT_PATTERNS.md](references/COMPONENT_PATTERNS.md)。

## 覆盖规则

不得仅凭 `rg --type java`、少量已反编译文件或单一关键词搜索得出“无反序列化 sink”。当项目包含 `.class`、`.jar`、XML/Properties 配置、WebService、Struts/Spring MVC、MQ、RPC 或定时/导入入口时，必须补充覆盖：

- 枚举入口：`web.xml`、`applicationContext*.xml`、`struts*.xml`、Spring MVC/REST 配置、`jaxws:endpoint`、Servlet/Filter/Listener、MQ listener、RPC/Dubbo/Hessian/RMI exporter、上传/导入/配置同步接口。
- 扫描源码与字节码：对 `.java`、反编译目录、`.class` 字符串、部署配置和关键 jar 内容分别扫描；报告中说明扫描范围，不能把“源码无命中”写成“项目无命中”。
- 追踪包装层：命中 `XmlUtil.fromXML`、`JsonUtils.fromJson`、`SerializeUtil.deserialize`、`ObjectMessage.getObject`、`DriverManager.getConnection` 等封装方法时，必须继续追到真实 sink。
- 追踪注解/DTO/配置线索：发现 `@XStreamAlias`、Fastjson autoType 配置、Shiro rememberMe 配置、JMS `MessageListener`、JDBC 动态数据源配置等线索后，必须查使用类和调用链，不得直接判为“仅配置/仅注解/仅组件”。
- 命中 `.class` 后必须按需反编译命中的类、入口类和工具类，再判断入口、参数可控性、组件/JDK/gadget 条件。

## 反编译规则

当源码缺失、不完整、与部署包不一致，或前序输出只给出 `.class` / `.jar` 证据时，按 [DECOMPILE_STRATEGY.md](../java-shared/DECOMPILE_STRATEGY.md) 使用 CFR 反编译。`SKILL.md` 不重复维护命令细节；需要执行命令时读取共享策略。

优先反编译与反序列化入口、sink 和触发条件直接相关的类：

- Controller、Action、Servlet、Filter、Listener、RPC/MQ handler。
- 调用 `ObjectInputStream/readObject`、`XMLDecoder/readObject`、Fastjson、XStream、Shiro RememberMe、Log4j/JNDI、JDBC URL/DataSource 的类。
- 配置导入、数据源测试、缓存读取、消息消费、任务执行、文件导入等可能处理外部数据的类。
- gadget 触发辅助类、反序列化封装工具类和组件适配类。

反编译结果只能作为证据补全来源，必须继续结合入口、可控性、调用链、组件/JDK/gadget 条件和 payload 验证判断风险。报告中必须标注反编译来源；反编译失败时记录失败原因，不得凭类名或组件命中直接判定漏洞成立。

## Gadget 链审计规则

当存在原生反序列化、JMS `ObjectMessage`、Shiro RememberMe、XStream/Fastjson/Jackson 等可构造对象的入口，或依赖中命中 CommonsCollections、CommonsBeanutils、Groovy、Spring、C3P0、Rome、Vaadin、Hibernate、Javassist、AspectJ、Xalan/TemplatesImpl 等 gadget 组件时，必须按 [COMPONENT_PATTERNS.md](references/COMPONENT_PATTERNS.md) 做链条完整性判断。

Gadget 风险不能只看依赖。至少确认：

1. 入口是否能接收攻击者控制的序列化数据或类型声明。
2. 反序列化后是否会自动触发 `readObject`、`readResolve`、`hashCode`、`compareTo`、`toString` 等方法。
3. 链条是否能到达反射、命令执行、JNDI、类加载、模板执行、脚本/表达式执行等危险原语。
4. classpath、JDK、组件版本、模块限制、类过滤、白名单/黑名单是否允许该链成立。
5. 报告必须区分“完整链条”“缺入口”“缺中间类”“缺危险原语”“被过滤器阻断”“仅组件存在”。

## 判定规则

漏洞成立至少需要：

1. 存在反序列化 sink。
2. 输入来自不可信来源，或攻击者可间接控制。
3. 入口可达，且分支条件可满足。
4. 组件/JDK/gadget/配置条件满足，或可通过安全方式验证。
5. 报告给出安全验证思路、可复制 Burp 请求和 payload。

必须记录不可利用原因：不可达、输入不可控、类型白名单、禁用 autoType、JDK/组件版本不满足、无 gadget、无出网条件、仅本地固定文件等。

## 输出要求

输出到 `{project_name}_audit/deserialization_audit/`：

`{project_name}_deserialization_audit_{YYYYMMDD_HHMMSS}.md`

漏洞编号格式：`{C/H/M/L}-DESER-{序号}`。报告模板见 [OUTPUT_TEMPLATE.md](references/OUTPUT_TEMPLATE.md)。多入口漏洞按 [VULNERABILITY_GROUPING.md](../java-shared/VULNERABILITY_GROUPING.md) 聚合：同根因多路由合并为一个漏洞编号并列出“受影响入口”，不同鉴权、组件、gadget、payload 或修复条件时拆分。

只完整列出存在风险或不可控但需说明的 sink；安全 sink 在摘要中提及数量和安全原因即可。每个漏洞必须包含可利用前置条件、Burp 请求、payload 和修复建议。

## Payload 规则

允许输出完整 payload，但必须遵守 [PAYLOAD_GUIDE.md](references/PAYLOAD_GUIDE.md)：

- 仅用于授权测试语境。
- 优先使用 DNS OOB、`id`、`whoami`、`calc` 等低破坏验证。
- 标注组件版本、JDK 版本、是否出网、是否鉴权、是否存在 gadget。
- Burp 请求必须匹配真实路由、参数名、Content-Type 和认证状态。
- 不生成删除文件、持久化、横向移动、批量利用类 payload。

## Gotchas

- 不要把组件 CVE 命中直接当成可利用漏洞。
- 不要把 CommonsCollections/Beanutils 等 gadget 依赖直接判为 RCE；必须同时有可控入口、自动触发点、危险原语和未被过滤的链条。
- 不要把 `rg --type java` 无结果当成“项目无 sink”；Java Web 项目常只有 `.class`、jar 和 XML 配置。
- 不要只搜 `ObjectInputStream`，必须覆盖 XMLDecoder、Fastjson、XStream、JDBC、Shiro、Log4j/JNDI。
- 不要忽略包装工具类和二次调用链，例如 `XmlUtil.fromXML`、`JsonUtils.fromJson`、`SerializeUtil.deserialize`、`ObjectMessage.getObject`。
- 不要把注解、DTO 或配置线索直接当安全结论；`@XStreamAlias`、JMS listener、Shiro rememberMe、动态 DataSource 都必须追踪使用类。
- 不要把自定义危险方法当成 gadget；没有自动触发方法或容器触发点时，只能列为代码风险线索。
- 不要忽略 Filter、Servlet、Listener、RPC/MQ、配置导入、数据源测试接口。
- 不要把 `JSON.parseObject(str, SafeClass.class)` 直接判为 Fastjson RCE。
- 不要把不可达工具方法当成 HTTP 可利用漏洞。
- 不要忽略分支条件、鉴权条件、组件/JDK 条件和出网条件。
