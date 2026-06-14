# Java Web 组件暴露面识别

本文件用于漏洞审计中的内部组件暴露面识别。组件不是漏洞族，组件命中也不是漏洞确认；它只用于驱动漏洞族初筛和 `VULN-CAND` 候选生成。

固定 grep/rg 查询集放在 `discovery-query-pack.md`。本文件不要求反编译全部第三方依赖；识别组件时优先看依赖清单、`WEB-INF/lib`、配置文件、import、注解、反编译业务代码、shaded 业务包、Query Pack 命中和实际使用点。

## 输出文件

漏洞审计时，在漏洞族初筛前创建：

```text
workspace/evidence/component-surface.md
```

该文件只保留在 `workspace/evidence/`，不得复制到最终报告。

## 组件表模板

```markdown
# Java Web 组件暴露面

| 组件 | 状态 | 版本/来源 | 证据位置 | 配置/使用点 | 关联漏洞族 | 候选 ID | 处理说明 |
|---|---|---|---|---|---|---|---|
| Spring MVC | [ ] |  |  |  |  |  |  |
| Apache Shiro | [ ] |  |  |  |  |  |  |
| Fastjson | [ ] |  |  |  |  |  |  |
```

状态语义与漏洞族初筛一致：

- `[ ]`：未检查，仅允许作为过程态；最终报告前不得保留。
- `[x]`：存在明确组件暴露面和使用点，必须映射到漏洞族初筛并生成候选深审。
- `[?]`：组件或使用点证据不完整但存在可疑面，必须映射到漏洞族初筛并生成候选深审。
- `[-]`：已检查，无使用证据、不适用或无法形成候选；必须写依据和处理说明。
- `[!]`：已检查，被明确配置、防护或部署边界阻断；必须写阻断依据和处理说明。

`[x]` / `[?]` 行必须填写 `证据位置`、`关联漏洞族` 和 `候选 ID`。组件表里的 `候选 ID` 必须同时出现在 `vulnerability-type-screening.md` 对应漏洞族行中，并存在独立候选证据矩阵。

## 识别证据优先级

优先使用能证明“组件被项目实际使用”的证据：

1. 业务代码 import、注解、父类、Filter/Servlet/Listener、Controller、配置类。
2. `web.xml`、Spring XML、Shiro/Spring Security 配置、Struts 配置、Actuator/Swagger/Druid/H2 配置。
3. `pom.xml`、`build.gradle`、`WEB-INF/lib`、fat jar 依赖清单、MANIFEST、部署描述符。
4. 反编译业务类或 shaded 包里的实际调用点。
5. 仅版本命中但无使用点时，通常标 `[?]` 或 `[-]`，不能直接生成确认漏洞。

不要因为依赖存在就确认漏洞；必须继续证明入口、参数来源、鉴权方式、传播链、触发条件、payload/Burp 请求和影响。

## 组件目录

按类别逐项检查，项目中发现清单外组件时追加到表末尾。

| 类别 | 组件 |
|---|---|
| Web/MVC | Spring MVC、Spring WebFlux、Struts2、JSF、Wicket、Tapestry、Vaadin、Play Framework、Servlet、JSP、JSTL |
| REST/JAX-RS | Jersey、RESTEasy、Apache CXF JAX-RS、Dropwizard、Micronaut、Quarkus、Vert.x |
| 安全/鉴权 | Apache Shiro、Spring Security、CAS、Keycloak Adapter、pac4j、Sa-Token、jjwt、java-jwt、nimbus-jose-jwt、OpenSAML |
| JSON/序列化/XML/YAML | Fastjson 1/2、Jackson、Gson、XStream、Hessian、Kryo、SnakeYAML、JAXB、dom4j、JDOM、Saxon、Java 原生序列化 |
| ORM/数据库 | MyBatis、MyBatis-Plus、Hibernate/JPA、Spring JDBC、JOOQ、QueryDSL、Druid、HikariCP、c3p0、DBCP |
| RPC/WebService | Apache CXF/SOAP、Axis、Axis2、Dubbo、Hessian、Burlap、RMI、gRPC、Thrift、DWR、Netty |
| 模板/表达式/脚本 | FreeMarker、Velocity、Thymeleaf、JSP EL、JSTL、Pebble、Beetl、SpEL、OGNL、MVEL、JEXL、Aviator、Groovy、Nashorn、Rhino、Janino、Drools |
| 文件/上传/解析 | Commons FileUpload、Servlet Multipart、Spring Multipart、Commons IO、Commons Compress、Zip4j、Apache POI、PDFBox、ImageIO、Thumbnailator |
| HTTP/网络 | Apache HttpClient、OkHttp、RestTemplate、WebClient、Feign、Retrofit、Jsoup、Java URL/openConnection |
| 日志/监控 | Log4j 1、Log4j 2、Logback、SLF4J、Commons Logging、JUL、Sentry、Jolokia、JMX |
| 管理/调试端点 | Spring Boot Actuator、Swagger、Springfox、OpenAPI、H2 Console、Druid StatView、Dubbo Admin、Arthas 暴露 |
| 缓存/消息/搜索 | Jedis、Lettuce、Redisson、Ehcache、Hazelcast、Kafka、RabbitMQ、RocketMQ、ActiveMQ、Elasticsearch、Solr |
| 存储/云/文件服务 | AWS SDK、MinIO、阿里云 OSS、七牛云 SDK、FTP/SFTP、SMB/jcifs |
| 容器/应用服务器 | Tomcat、Jetty、Undertow、JBoss/WildFly、WebLogic、WebSphere |

## 组件到漏洞族映射

映射是候选生成线索，不是确认结论。

| 组件或类别 | 关联漏洞族 |
|---|---|
| Shiro、Spring Security、CAS、Sa-Token、Keycloak、pac4j | 认证绕过、权限绕过、未授权访问、CSRF、敏感信息泄露 |
| JWT/OpenSAML | 认证绕过、权限绕过、弱密码学、敏感信息泄露 |
| Fastjson、Jackson、XStream、SnakeYAML、Hessian、Kryo、Java 原生序列化 | 反序列化、JNDI/远程查找、代码/脚本注入、敏感信息泄露 |
| Struts2、OGNL、SpEL、MVEL、JEXL、模板引擎 | 表达式注入、模板注入/SSTI、参数绑定风险、XSS |
| MyBatis、Hibernate/JPA、JOOQ、QueryDSL、Spring JDBC | SQL 注入、JPQL/HQL/JPA 注入、NoSQL/搜索注入、敏感信息泄露 |
| CXF、Axis、JAX-RS、Dubbo、RMI、DWR、Thrift、gRPC | 未授权访问、XXE、反序列化、敏感信息泄露、SSRF |
| Log4j、Logback、日志组件 | JNDI/远程查找、日志注入、敏感信息泄露 |
| FileUpload、POI、PDFBox、压缩库、图片处理库 | 文件上传危险类型、路径穿越、Zip Slip/归档穿越、ReDoS/资源消耗 |
| HTTP 客户端、Jsoup、云存储 SDK、FTP/SFTP/SMB | SSRF、开放重定向/转发、凭据泄露、路径穿越 |
| Actuator、Swagger、H2、Jolokia、JMX、Druid StatView、Dubbo Admin、Arthas | Actuator/调试接口暴露、未授权访问、敏感信息泄露 |
| Tomcat、Jetty、Undertow、WebLogic、WebSphere、JBoss/WildFly | 未授权访问、路径穿越、文件上传、敏感信息泄露、容器配置缺陷 |

## 处理规则

- 组件表必须在 Query Pack 和漏洞族初筛前完成；它为后续检索解释、漏洞族初筛和候选生成提供证据输入。
- 组件 `[x]` / `[?]` 后，对应关联漏洞族必须在 `vulnerability-type-screening.md` 中标为 `[x]` 或 `[?]`，并记录相同的 `VULN-CAND-xxx`。
- 同一组件发现多个独立入口、根因或传播链时，拆成多个候选。
- 多个组件指向同一根因时，可以复用同一个候选；最终报告仍按根因归并。
- 组件版本命中 CVE 只能作为初筛依据；没有可达入口、可控输入、传播链和复现请求时，不能进入确认漏洞。
- 组件未命中或不适用只留在 `component-surface.md`，最终报告不得输出“某组件不存在漏洞”清单。
- 不要反编译全部第三方库来证明组件存在；只有当业务代码、shaded 包或配置依赖某个库实现细节时，才按需反编译相关类。

## 研究依据

- Apache Struts Security: https://struts.apache.org/security/
- Apache Shiro Security Reports: https://shiro.apache.org/security-reports.html
- Apache Logging Services Security: https://logging.apache.org/security.html
- Spring Security Advisories: https://spring.io/security/
- Apache Tomcat Security: https://tomcat.apache.org/security.html
- NVD CVE-2022-25845 Fastjson: https://nvd.nist.gov/vuln/detail/CVE-2022-25845
- XStream Project: https://x-stream.github.io/
