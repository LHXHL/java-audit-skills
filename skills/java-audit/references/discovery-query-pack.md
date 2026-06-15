# Java Web 审计 Query Pack

本文件用于漏洞审计中的系统化候选发现。Query Pack 的目标是减少“凭第一眼判断”导致的漏审；它只生成真实代码命中和候选线索，不确认漏洞。

具体查询组和正则维护在 `discovery-query-pack.yaml`，脚本 `scripts/run_discovery_queries.py` 只负责加载 YAML、执行检索、生成 `search-hits/`。新增或调整检索规则时只改 YAML，并先运行：

```bash
python3 skills/java-audit/scripts/run_discovery_queries.py --validate-queries
```

## 使用规则

- 漏洞审计在完成组件暴露面识别和组件漏洞命中扫描后、漏洞族初筛前运行 Query Pack。
- 默认读取 `references/discovery-query-pack.yaml`；需要临时实验规则时可以用 `--queries <yaml>` 指定替代文件，但最终 Skill 规则应回写到默认 YAML。
- 默认使用 Python 标准库检索源码、反编译产物、业务 JAR/class 解包或反编译后的目录，不依赖 `rg`。
- 可用 `--engine auto` 在存在 `rg` 时自动使用 `rg` 加速；可用 `--engine rg` 强制使用 `rg`；Windows/macOS/Linux 通用默认值是 `--engine python`。
- 大型项目可用 `--group <slug>` 只运行部分查询组；用 `--list-groups` 查看所有查询组。分组执行不能替代最终闭环，未运行或未处理的高价值面需要在覆盖限制里说明。
- Query 命中不等于漏洞。命中必须进入 `workspace/evidence/search-hits/`，再由 AI 结合入口、参数、鉴权、传播链和防护判断归类。
- 一个命中可以映射多个漏洞族。例如 `URL.openConnection` 可映射 SSRF、开放重定向、敏感信息泄露；`XMLInputFactory` 可映射 XXE、XSLT、SSRF、文件读取。
- 高价值命中必须生成或合并到 `VULN-CAND-xxx`；低价值、不适用、误报或被防护阻断必须写明处理原因。每条命中完成处理后都要填写 `处理说明`。
- 不得把 search hits 原表复制进最终报告。

## 输出文件

运行脚本后生成：

```text
workspace/evidence/search-hits/index.md
workspace/evidence/search-hits/<slug>.md
workspace/evidence/search-hits/manifest.json
```

脚本每次运行都会重建 `search-hits/*.md` 和 `manifest.json`，该目录表示本次 Query Pack 的快照；不要在其中手写长期证据，长期判断应落到 `vulnerability-type-screening.md` 和 `VULN-CAND-xxx-evidence-matrix.md`。

`manifest.json`、`index.md` 和各 `<slug>.md` 中的生成工具标记、Query Pack 文件路径和 YAML 加载器用于证明 Query Pack 真实执行过。不得手写、伪造或补填 `search-hits/index.md`；如果脚本未运行，必须补跑脚本，而不是手工创建命中摘要。

每条命中至少包含：

```text
编号、漏洞族、优先级、命中模式、文件、行号、上下文、可映射漏洞族、处理状态、候选 ID、处理说明
```

初始 `处理状态` 为 `未处理`。生成最终报告前，所有命中都必须填写 `处理说明`，并处理为以下之一：

```text
生成候选 / 合并候选 / 低价值放弃 / 误报 / 不适用 / 防护阻断
```

## 查询集

下表是 YAML 查询组索引；正则内容以 `discovery-query-pack.yaml` 为准。

| 查询组 | 主要模式 | 可映射漏洞族 |
|---|---|---|
| 入口/路由-Web | `@RequestMapping`, `@RestController`, `@Path`, `@WebServlet`, `HttpServlet`, `RouterFunction` | 未授权访问、鉴权绕过、参数来源 |
| 入口/RPC/WebService | `@WebService`, `CXF`, `JAX-WS`, `Dubbo`, `Hessian`, `gRPC`, `Thrift`, `RMI` | 未授权访问、反序列化、XXE |
| 入口/消息/WebSocket/任务 | `@KafkaListener`, `@RabbitListener`, `@JmsListener`, `ObjectMessage`, `@ServerEndpoint`, `@Scheduled` | 反序列化、业务流程滥用 |
| 参数来源/HTTP | `getParameter`, `getHeader`, `@RequestBody`, `@PathVariable`, `MultipartFile`, `Part` | 注入、文件、SSRF、XSS、Mass Assignment |
| 参数来源/结构化数据 | `JSONObject`, `ObjectMapper`, `XmlMapper`, `XStream`, `Yaml`, `Map<String`, `DataBinder` | 反序列化、Mass Assignment、NoSQL/XSS |
| 传播中间态/拼接点 | `StringBuilder`, `String.format`, `BeanUtils`, `orderBy`, `tableName`, `filename`, `url`, `tenantId` | SQL、SSRF、路径穿越、越权 |
| 鉴权/授权-Spring/Shiro | `SecurityFilterChain`, `permitAll`, `@PreAuthorize`, `ShiroFilterFactoryBean`, `anon`, `authc` | 未授权、认证绕过、越权、CSRF |
| 鉴权/Token/Session/JWT | `Jwts`, `JWT.decode`, `Algorithm.none`, `Authorization`, `getSession`, `SaToken`, `Keycloak`, `SAMLResponse` | 认证绕过、弱密码学、敏感信息泄露 |
| 组件/框架 | `Fastjson`, `Jackson`, `XStream`, `SnakeYAML`, `Shiro`, `Struts`, `MyBatis`, `Actuator`, `DWR` | 组件暴露面与关联漏洞族 |
| SQL/JDBC/Spring JDBC | `createStatement`, `JdbcTemplate`, `select ... +`, `StringBuilder`, `String.format` | SQL 注入、动态排序、数据越权 |
| SQL/MyBatis/MyBatis-Plus | `${`, `@SelectProvider`, `QueryWrapper`, `.last(`, `.apply(`, `orderBySql`, `inSql` | SQL 注入、动态排序、数据越权 |
| SQL/HQL/JPQL/JPA | `createQuery`, `createNativeQuery`, `@Query`, `Querydsl`, `CriteriaBuilder`, `ORDER BY` | HQL/JPQL/JPA 注入 |
| NoSQL/搜索 | `MongoTemplate`, `Document.parse`, `Elasticsearch`, `SearchSourceBuilder`, `SolrQuery`, `RedisTemplate` | NoSQL/搜索注入、数据越权 |
| 命令/进程执行 | `Runtime.exec`, `ProcessBuilder`, `/bin/sh`, `cmd.exe`, `ffmpeg`, `wkhtmltopdf` | 命令注入、RCE |
| 脚本/表达式执行 | `ScriptEngine`, `GroovyShell`, `Janino`, `MVEL`, `SpEL`, `OGNL`, `Drools` | 代码/脚本/表达式注入 |
| 模板/视图输出 | `Freemarker`, `Velocity`, `Thymeleaf`, `th:utext`, `no_esc`, `ModelAndView`, `out.print` | SSTI、XSS |
| 文件/路径/IO | `Files.read`, `Files.write`, `FileUtils`, `IOUtils`, `ResourceUtils`, `getRealPath`, `normalize` | 路径穿越、任意文件读写 |
| 文件/上传/删除 | `MultipartFile`, `Part.write`, `transferTo`, `getOriginalFilename`, `FileItem`, `ServletFileUpload` | 文件上传、任意文件写/删除 |
| 压缩/解压 | `ZipInputStream`, `ZipEntry`, `TarArchiveEntry`, `ArchiveInputStream`, `extract` | Zip Slip、任意文件写 |
| SSRF/HTTP 客户端 | `RestTemplate`, `WebClient`, `Feign`, `Retrofit`, `Jsoup.connect`, `URLConnection`, `callbackUrl` | SSRF、内网探测 |
| 跳转/转发/Header | `sendRedirect`, `redirect:`, `forward:`, `Location`, `returnUrl`, `setHeader` | 开放重定向、响应拆分 |
| 云存储/外部存储/网络文件 | `AmazonS3`, `MinioClient`, `OSSClient`, `FTPClient`, `ChannelSftp`, `SmbFile` | SSRF、凭据泄露、路径风险 |
| XML/XXE/XPath/XSLT | `DocumentBuilderFactory`, `SAXReader`, `JAXBContext`, `TransformerFactory`, `XPathFactory`, `DOCTYPE` | XXE、XPath、XSLT、SSRF |
| LDAP/目录查询 | `DirContext`, `LdapTemplate`, `SearchControls`, `ldap://`, `filter=` | LDAP 注入、认证绕过 |
| 反序列化/Java 原生与传输 | `ObjectInputStream`, `ObjectMessage`, `XMLDecoder`, `Hessian`, `Kryo`, `RMI` | Java 反序列化、RCE |
| 反序列化/JSON/YAML 多态 | `fastjson`, `SupportAutoType`, `enableDefaultTyping`, `@JsonTypeInfo`, `SnakeYAML` | JSON/YAML 多态反序列化、JNDI |
| XSS/响应输出 | `getWriter`, `ResponseEntity`, `text/html`, `addAttribute`, `htmlUnescape`, `escapeXml=false` | XSS、信息泄露 |
| Mass Assignment | `BeanUtils`, `ModelMapper`, `@RequestBody`, `updateById`, `role`, `status`, `amount`, `tenantId` | 属性越权、金额/状态篡改 |
| 凭据/敏感配置 | `password`, `secret`, `accessKey`, `privateKey`, `jdbc:`, `AKIA`, `BEGIN PRIVATE KEY` | 硬编码凭据、敏感信息泄露 |
| 密码学/随机数/Token | `MD5`, `SHA1`, `DES`, `AES/ECB`, `Random`, `Math.random`, `static KEY/IV` | 弱密码学、Token 可预测 |
| TLS/证书信任 | `TrustManager`, `HostnameVerifier`, `NoopHostnameVerifier`, `trustAllCerts` | TLS 信任错误、敏感通信风险 |
| CORS/CSRF/Cookie | `@CrossOrigin`, `allowedOrigins`, `csrf.disable`, `SameSite`, `HttpOnly`, `Secure` | CORS、CSRF、Cookie 安全属性 |
| 管理/调试端点 | `actuator`, `heapdump`, `swagger`, `api-docs`, `Jolokia`, `DruidStatView`, `H2 Console` | 调试接口暴露、未授权 |
| 日志/审计 | `logger`, `printStackTrace`, `MDC.put`, `X-Forwarded-For`, `\r`, `\n` | 日志注入、敏感信息泄露 |
| ReDoS/资源消耗 | `Pattern.compile`, `replaceAll`, `while(true)`, `pageSize`, `export`, `readAllBytes` | ReDoS、资源消耗、批量导出 |
| 业务安全关键词 | `resetPassword`, `verifyCode`, `pay`, `refund`, `approve`, `tenant`, `callback`, `order` | 越权、业务流程滥用 |

## 处理要求

- 命中必须先归类，再决定是否生成候选；不要把命中直接写成漏洞。
- 同一漏洞族下多个独立入口、root cause、sink 或传播链必须拆分为多个候选，或明确合并到已有候选。
- 一个命中如果由组件表或组件漏洞命中驱动，应同时体现在 `component-surface.md` / `component-hits/` 和 `vulnerability-type-screening.md`。
- 最终报告前，`search-hits/` 中不得存在 `未处理`、`待归类` 或空处理状态。
