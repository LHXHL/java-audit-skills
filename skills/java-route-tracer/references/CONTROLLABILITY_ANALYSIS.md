# 参数可控性与 Sink 分类

本 reference 用于判断“用户输入是否以何种形式到达 sink”。它只输出数据流证据，不直接判断漏洞成立。

## 1. 基本术语

| 术语 | 含义 |
|------|------|
| Source | HTTP path/query/form/body/header/cookie/file/SOAP 参数，或用户可间接控制的数据库、消息、配置导入数据 |
| Transform | JSON/XML 解析、DTO 映射、类型转换、trim、decode、拼接、默认值处理 |
| Guard | 白名单、黑名单、格式校验、权限检查、路径规范化、SQL 参数化、XML 安全配置等限制 |
| Sink | 可能被下游专项审计关注的执行点或输出点 |
| Controllability | Source 到 Sink 的可控程度 |

## 2. Sink 类型

报告中使用统一类型，必要时写 subtype：

| Sink 类型 | 典型代码 | 下游 |
|-----------|----------|------|
| SQL | JDBC `Statement`、`PreparedStatement`、Hibernate/JPA Criteria、MyBatis `${}` / `#{}`、HQL/JPQL/native SQL、Mapper XML | `java-sql-audit` |
| FILE_READ | `FileInputStream`、`Files.read*`、`FileReader`、下载流 | `java-file-read-audit` |
| FILE_WRITE | `MultipartFile.transferTo`、`FileItem.write`、`Files.write`、上传保存 | `java-file-upload-audit` |
| XML | `DocumentBuilder.parse`、`SAXReader.read`、`XMLInputFactory`、`Unmarshaller` | `java-xxe-audit` 或反序列化审计 |
| DESERIALIZE | `ObjectInputStream.readObject`、`XMLDecoder`、Fastjson/XStream/Jackson 多态反序列化、Shiro RememberMe | `java-deserialization-audit` |
| COMMAND | `Runtime.exec`、`ProcessBuilder`、脚本执行 | 人工或后续命令注入审计 |
| HTTP | `URL.openConnection`、`HttpClient`、`RestTemplate`、OkHttp | SSRF/HTTP sink 审计 |
| LDAP | `DirContext.search`、`LdapTemplate` | LDAP 注入审计 |
| EXPRESSION | SpEL、OGNL、MVEL、JEXL、模板表达式执行 | 表达式注入审计 |
| RESPONSE | `response.getWriter`、模板输出、`@ResponseBody` 返回用户输入 | XSS/响应输出审计 |
| PATH | `new File(base, input)`、`Paths.get` 但尚未读写 | 文件类专项审计的候选路径 |
| UNCONFIRMED | 已到达 Manager/DAO/Util/接口方法，但实现源码、反编译结果或真实危险 API 缺失 | 继续反编译或补源码确认 |
| NONE | 未发现敏感 sink | 无下游专项或仅记录覆盖 |

如果一个 sink 同时满足多个类型，主类型写最直接的执行点，备注中写关联类型。例如 XML 输入进入 XStream 时主类型可写 `DESERIALIZE`，备注“XML 格式承载”。

不要凭方法名或类名推断 sink。`getUserBean`、`addUser`、`save`、`query`、`Dao`、`ManagerImpl`、`Repository` 只能说明“下游候选调用”。只有读到真实执行 API、Mapper XML、注解 SQL 或反编译方法体后，才能写具体 sink 类型。

## 3. 可控性结论

| 结论 | 使用场景 | 报告写法 |
|------|----------|----------|
| 完全可控 | Source 未被覆盖或限制，原值或等价值到达 sink | `完全可控` |
| 条件可控 | 需要满足分支、非空、角色、配置开关、类型等条件才到达 sink | `条件可控: 仅当 status=enabled` |
| 受限可控 | 只允许白名单、枚举、数值范围、固定目录内文件名等有限值 | `受限可控: 仅允许 id/name` |
| 不可控 | 到达 sink 的值由服务端常量、配置、数据库固定值或无条件覆盖决定 | `不可控` |
| 未确认 | 源码缺失、反射目标不明、反编译失败或配置缺失导致无法判断 | `未确认: 反射目标缺失` |
| 无敏感 Sink | 参数未到达本 skill 关注的 sink | `无敏感 Sink` |

不要把“完全可控”直接写成“漏洞成立”，也不要把“参数化/白名单/校验”写成“漏洞不成立”。漏洞判断需要专项规则、上下文和防护检查。

## 4. 判定步骤

### 4.1 确认 Source

记录每个参数的来源：

- Path: `@PathVariable`、`@PathParam`、`request.getPathInfo()`。
- Query/Form: `@RequestParam`、`request.getParameter`、Struts field/setter。
- Body: `@RequestBody`、JSON 字符串、SOAP Body、`request.getInputStream()`。
- Header/Cookie: `@RequestHeader`、`request.getHeader`、`Cookie`。
- File: `MultipartFile`、`FileItem`、上传流。

参数如果经过 DTO、Map、BeanUtils 或 JSON 字段展开，使用 `source.field` 形式记录，例如 `pageJson.orderBy`。

### 4.2 跟踪 Transform

逐层记录：

- 变量名变化。
- 对象字段映射。
- JSON/XML 解析后的字段。
- 类型转换，例如 String -> int、String -> enum。
- 拼接、decode、trim、replace、substring。
- ThreadLocal、父类字段、session attribute、request attribute。

### 4.3 识别 Guard

每个 Guard 必须写清影响：

| Guard 类型 | 判定要点 |
|------------|----------|
| 无条件覆盖 | 覆盖后使用服务端值，通常不可控 |
| 默认值 | 用户未传或为空时覆盖，用户提供有效值时仍可能可控 |
| 白名单 | 只能在白名单值内受限可控 |
| 黑名单 | 过滤危险字符但可能不完整，写成条件或受限，不直接判漏洞 |
| 参数化 | SQL 参数化可能使 SQL sink 安全，追踪报告只记录限制 |
| canonical 校验 | 文件路径限制到固定目录时写受限可控或不可控 |
| XML feature | 禁用外部实体时记录防护，XXE 结论交给下游 |
| 权限/鉴权 | 只作为路径条件或上游透传，不自行判越权 |

### 4.4 绑定 Sink

sink 位置必须包含可验证代码证据：

- 文件路径或类名。
- 方法名。
- 行号或可定位代码片段。
- 使用的变量名。
- sink 类型和 subtype。

无法获得行号时，写类方法和关键代码片段，不要编造行号。

如果只能追到接口或业务方法调用，例如 `userManager.getUserBean(loginName)`、`roleManager.addRole(roleBean)`、`ownerManager.save(ownerBean)`：

- `Sink 类型` 写 `UNCONFIRMED`，或在调用链中写“下游候选调用”。
- `位置` 写已确认的调用点，例如 `AdminServiceImpl.java:156`。
- `限制说明` 写“实现类源码/反编译结果缺失，未看到 SQL/文件/XML 等真实 sink”。
- 不得写 `SQL SELECT`、`SQL INSERT`、`Hibernate session.save`、`WHERE login_name = ?` 等未经源码证实的内容。

## 5. 输出表格

在报告中至少提供：

```markdown
| 参数 | Source | Transform 摘要 | Guard/覆盖 | Sink 类型 | Sink 位置 | 可控性 | 限制说明 |
|------|--------|----------------|------------|-----------|-----------|--------|----------|
| pageJson.orderBy | Body JSON | Page.orderBy -> dao.findSql | 非空时保留 | SQL | AbstractDao.java:123 | 条件可控 | 非空且通过字段白名单时到达 |
| loginName | SOAP Body | loginName -> userManager.getUserBean | 未确认 | UNCONFIRMED | AdminServiceImpl.java:156 | 未确认 | 未读取 UserManagerImpl，不能推断 SQL sink |
```

当存在多个 sink 时，每个参数和 sink 组合单独一行。

## 6. 常见 gotchas

- `StringUtils.defaultIfBlank(input, "id")` 不是无条件覆盖；非空输入仍可控。
- `Integer.parseInt(input)` 会限制为数字，通常不是 SQL 标识符注入，但仍可能影响业务条件。
- `PreparedStatement`、Hibernate Criteria、MyBatis `#{}` 仍是 SQL sink，但参数化限制必须写清，不能省略给 SQL 审计；不要替 SQL 审计下“注入不成立”结论。
- ORM Criteria 或参数化 API 没有显式 SQL 字符串时，不得补写推测的 `SELECT`、表名或列名；只引用实际 API 调用和参数绑定关系。
- `Manager.save()`、`Dao.query()` 不是 SQL sink 证据；必须读到实现或 Mapper。
- `Map<String,Object>`、`JSONObject`、`BeanUtils.populate` 会隐藏字段名，需要追字段访问点。
- `request.getParameterMap()`、Struts action 字段、Spring binder 都可能让参数进入对象属性。
- 文件路径 `normalize()` 后还要看是否校验 base dir；只 normalize 不等于安全。
- XML parser factory 的安全 feature 可能在工具类统一设置，不能只看 parse 调用点。
- 反序列化组件版本命中不是本 skill 的结论；这里只记录数据能否进入相关 API。
