#!/usr/bin/env python3
"""运行 Java Web 审计 Query Pack，生成内部 search-hits 证据。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class QueryGroup:
    slug: str
    title: str
    primary_family: str
    mapped_families: tuple[str, ...]
    priority: str
    patterns: tuple[str, ...]


QUERY_GROUPS: tuple[QueryGroup, ...] = (
    QueryGroup("entrypoints-web", "入口/路由-Web", "入口面", ("未授权访问", "鉴权绕过", "参数来源"), "高", (
        r"@RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping|@PatchMapping",
        r"@Controller|@RestController|@ResponseBody|@Path\(|@GET|@POST|@PUT|@DELETE",
        r"@WebServlet|HttpServlet|doGet|doPost|doPut|doDelete|service\(",
        r"RouterFunction|route\(|HandlerFunction|ServerRequest|ServerResponse",
    )),
    QueryGroup("entrypoints-rpc", "入口/RPC/WebService", "入口面", ("未授权访问", "鉴权绕过", "反序列化", "XXE"), "高", (
        r"@WebService|@WebMethod|Endpoint|ServiceEndpoint|CXF|JAX-WS|SOAPMessage",
        r"@Path\(|ApplicationPath|ResourceConfig|Jersey|RESTEasy|Dropwizard",
        r"@DubboService|@DubboReference|@Reference|@Service\(.*version|HessianServiceExporter|BurlapServiceExporter",
        r"@GrpcService|BindableService|StreamObserver|Thrift|TProcessor|RMI|UnicastRemoteObject",
    )),
    QueryGroup("entrypoints-async", "入口/消息/WebSocket/任务", "入口面", ("未授权访问", "反序列化", "业务流程滥用"), "中", (
        r"@KafkaListener|@RabbitListener|@RocketMQMessageListener|@JmsListener|MessageListener",
        r"ObjectMessage|BytesMessage|TextMessage|onMessage\(|consumeMessage|handleMessage",
        r"@ServerEndpoint|WebSocketHandler|TextWebSocketHandler|handleTextMessage|onMessage\(",
        r"@Scheduled|QuartzJobBean|JobExecutionContext|executeInternal|TimerTask",
    )),
    QueryGroup("user-input-http", "参数来源/HTTP", "参数来源", ("SQL 注入", "命令注入", "文件读写", "SSRF", "XSS", "Mass Assignment"), "高", (
        r"getParameter|getParameterMap|getParameterValues|getHeader|getHeaders|getCookies|getInputStream|getReader",
        r"@RequestParam|@RequestBody|@PathVariable|@RequestHeader|@CookieValue|@ModelAttribute",
        r"HttpServletRequest|ServletRequest|ServerHttpRequest|ServerWebExchange|MultiValueMap",
        r"MultipartFile|Part|getParts|CommonsMultipartFile|MultipartHttpServletRequest",
    )),
    QueryGroup("user-input-structured", "参数来源/结构化数据", "参数来源", ("反序列化", "Mass Assignment", "NoSQL/搜索注入", "XSS"), "中", (
        r"JSONObject|JSONArray|JSON\.parse|JSON\.parseObject|ObjectMapper|readValue|readTree",
        r"XmlMapper|XStream|Yaml|YAMLFactory|new Yaml|loadAs\(|load\(",
        r"Map<String|HashMap|MultiValueMap|JsonNode|ObjectNode|ArrayNode",
        r"BindingResult|DataBinder|WebDataBinder|setAllowedFields|setDisallowedFields",
    )),
    QueryGroup("propagation-join-points", "传播中间态/拼接点", "传播链线索", ("SQL 注入", "SSRF", "路径穿越", "越权", "Mass Assignment"), "中", (
        r"StringBuilder|StringBuffer|StringJoiner|String\.format|MessageFormat\.format|append\(",
        r"BeanUtils\.copyProperties|PropertyUtils|ModelMapper|ConvertUtils|ReflectionUtils",
        r"orderBy|sortField|sortOrder|column|columns|tableName|where|filter|condition|keyword|query",
        r"fileName|filename|path|dir|url|uri|host|domain|callback|returnUrl|redirectUrl|tenantId|ownerId|userId|roleId",
    )),
    QueryGroup("auth-spring-shiro", "鉴权/授权-Spring/Shiro", "鉴权面", ("未授权访问", "认证绕过", "水平/垂直越权", "CSRF/CORS"), "高", (
        r"SecurityFilterChain|WebSecurityConfigurerAdapter|authorizeHttpRequests|authorizeRequests|permitAll|web\.ignoring",
        r"antMatchers|mvcMatchers|requestMatchers|hasRole|hasAnyRole|hasAuthority|access\(",
        r"@PreAuthorize|@PostAuthorize|@Secured|@RolesAllowed|PermissionEvaluator",
        r"ShiroFilterFactoryBean|DefaultWebSecurityManager|anon|authc|roles|perms|Subject|isAuthenticated|isPermitted",
    )),
    QueryGroup("auth-token-session", "鉴权/Token/Session/JWT", "鉴权面", ("认证绕过", "弱密码学", "敏感信息泄露"), "高", (
        r"Jwts\.parser|Jwts\.builder|JWT\.decode|JWT\.require|Algorithm\.none|NimbusJwtDecoder|JwtDecoder",
        r"Claims|getSubject|getClaim|Authorization|Bearer|refreshToken|accessToken|tokenSecret|signingKey",
        r"getSession|setAttribute|getAttribute|invalidate|rememberMe|setMaxInactiveInterval|SessionRegistry",
        r"SaRouter|StpUtil|SaToken|pac4j|Keycloak|OpenSAML|SAMLResponse|OAuth2|OIDC",
    )),
    QueryGroup("components-frameworks", "组件/框架", "组件暴露面", ("反序列化", "表达式注入", "SQL 注入", "未授权访问", "敏感信息泄露"), "中", (
        r"fastjson|fastjson2|ObjectMapper|Jackson|XStream|SnakeYAML|Hessian|Kryo|FST",
        r"Shiro|Spring Security|Sa-Token|pac4j|Keycloak|Struts|OGNL|SpEL",
        r"MyBatis|MyBatis-Plus|Hibernate|JPA|JOOQ|QueryDSL|Druid|HikariCP",
        r"Actuator|Swagger|springfox|OpenAPI|Log4j|Jolokia|H2 Console|DWR|CXF|Axis",
    )),
    QueryGroup("sql-jdbc", "SQL/JDBC/Spring JDBC", "SQL 注入", ("动态排序注入", "数据越权"), "高", (
        r"createStatement|prepareStatement|CallableStatement|executeQuery|executeUpdate|execute\(",
        r"JdbcTemplate|NamedParameterJdbcTemplate|SimpleJdbcInsert|queryForObject|queryForList|batchUpdate",
        r"select\s+.*\+|update\s+.*\+|insert\s+.*\+|delete\s+.*\+|where\s+.*\+",
        r"StringBuilder.*select|append\(.*select|String\.format\(.*select|MessageFormat\.format\(.*select",
    )),
    QueryGroup("sql-mybatis", "SQL/MyBatis/MyBatis-Plus", "SQL 注入", ("HQL/JPQL/JPA 注入", "动态排序注入", "数据越权"), "高", (
        r"\$\{|#\{|<select|<update|<insert|<delete|<foreach|<where|<if\b|<choose|<bind",
        r"@Select|@Update|@Insert|@Delete|@SelectProvider|@UpdateProvider|@InsertProvider|@DeleteProvider",
        r"QueryWrapper|LambdaQueryWrapper|UpdateWrapper|Wrappers\.|SqlRunner|BaseMapper",
        r"\.last\s*\(|\.apply\s*\(|\.exists\s*\(|\.notExists\s*\(|\.orderBy\s*\(|\.orderByAsc\s*\(|\.orderByDesc\s*\(",
        r"orderBySql|inSql|notInSql|setSql|having|groupBy|tableName|column|sort",
    )),
    QueryGroup("sql-orm", "SQL/HQL/JPQL/JPA", "HQL/JPQL/JPA 注入", ("SQL 注入", "动态排序注入", "数据越权"), "高", (
        r"createQuery|createNativeQuery|entityManager|Session\.createQuery|Session\.createSQLQuery",
        r"@Query|nativeQuery|Querydsl|JPAQueryFactory|CriteriaBuilder|Specification<",
        r"ORDER BY|GROUP BY|LIMIT|OFFSET|order by|group by|where .* like|where .* in",
        r"setParameter|setParameterList|Query\.set|TypedQuery|NativeQuery",
    )),
    QueryGroup("nosql-search", "NoSQL/搜索", "NoSQL/搜索注入", ("数据越权", "敏感信息泄露"), "中", (
        r"MongoTemplate|BasicDBObject|Document\.parse|Criteria\.where|Query\.query|Aggregation",
        r"Elasticsearch|SearchRequest|SearchSourceBuilder|QueryBuilder|scriptQuery|matchQuery|termQuery|boolQuery",
        r"SolrQuery|setQuery|addFilterQuery|Jedis|Redisson|RedisTemplate|opsForValue|opsForHash",
        r"Neo4jClient|CassandraTemplate|CqlSession|InfluxDB|Prometheus",
    )),
    QueryGroup("command-exec", "命令/进程执行", "命令注入", ("脚本注入", "RCE"), "高", (
        r"Runtime\.getRuntime\(\)\.exec|Runtime\.exec|ProcessBuilder|ProcessImpl|start\(",
        r"/bin/sh|/bin/bash|cmd\.exe|powershell|sh -c|bash -c|cmd /c",
        r"command|cmd|args|shell|exec\(|executeCommand|runCommand",
        r"ffmpeg|convert|ImageMagick|wkhtmltopdf|phantomjs|tar |zip |unzip ",
    )),
    QueryGroup("script-expression", "脚本/表达式执行", "表达式注入", ("代码/脚本注入", "模板注入/SSTI", "RCE"), "高", (
        r"ScriptEngine|ScriptEngineManager|eval\(|GroovyShell|GroovyClassLoader|Janino|AviatorEvaluator",
        r"MVEL|JEXL|ExpressionFactory|ExpressionParser|SpEL|parseExpression|StandardEvaluationContext",
        r"OGNL|getValue\(|setValue\(|Drools|KieSession|RuleEngine|Nashorn|Rhino",
    )),
    QueryGroup("template-view", "模板/视图输出", "模板注入/SSTI", ("XSS", "表达式注入"), "中", (
        r"Freemarker|Velocity|Thymeleaf|Mustache|Pebble|Beetl|TemplateEngine|processTemplate|render",
        r"th:utext|utext|no_esc|escapeHtml|unescape|HtmlUtils|StringEscapeUtils",
        r"ModelAndView|addObject|addAttribute|setViewName|InternalResourceViewResolver",
        r"JSP|JstlView|out\.print|c:out|escapeXml",
    )),
    QueryGroup("file-path-io", "文件/路径/IO", "路径穿越", ("任意文件读写", "敏感信息泄露"), "高", (
        r"new File|Paths\.get|Path\.of|Files\.read|Files\.write|Files\.copy|Files\.move|Files\.delete",
        r"FileInputStream|FileOutputStream|RandomAccessFile|FileReader|FileWriter|FileChannel",
        r"FileUtils|IOUtils|ResourceUtils|ClassPathResource|PathResource|UrlResource|ServletContext\.getRealPath",
        r"getCanonicalPath|getAbsolutePath|normalize\(|toRealPath|resolve\(|relativize",
    )),
    QueryGroup("file-upload", "文件/上传/删除", "文件上传危险类型", ("任意文件写/删除", "路径穿越", "敏感信息泄露"), "高", (
        r"MultipartFile|CommonsMultipartFile|MultipartResolver|MultipartConfigElement|Part\.write",
        r"transferTo|getOriginalFilename|getContentType|getSize|upload|download|delete\(|renameTo|copy|move",
        r"allowedExtensions|fileExt|suffix|contentType|mime|magic|thumbnail|ImageIO|PDFBox|POI",
        r"FileItem|DiskFileItemFactory|ServletFileUpload|isMultipartContent",
    )),
    QueryGroup("archive", "压缩/解压", "Zip Slip/归档穿越", ("任意文件写/删除", "路径穿越"), "高", (
        r"ZipInputStream|ZipOutputStream|ZipEntry|JarEntry|JarFile|getNextEntry|entry\.getName",
        r"TarArchiveInputStream|TarArchiveEntry|ArchiveInputStream|ArchiveEntry|SevenZFile|ZipFile",
        r"unzip|extract|decompress|expand|untar|unarchive|normalize\(|getCanonicalPath",
    )),
    QueryGroup("ssrf-http-client", "SSRF/HTTP 客户端", "SSRF", ("开放重定向/转发", "内网探测", "敏感信息泄露"), "高", (
        r"RestTemplate|WebClient|HttpClient|HttpClients|CloseableHttpClient|OkHttpClient|URLConnection|openConnection",
        r"FeignClient|Feign\.builder|Retrofit|Jsoup\.connect|AsyncHttpClient|Unirest|Fuel|JoddHttp",
        r"URL\(|URI\(|InetAddress|getByName|Socket\(|ProxySelector|DnsResolver",
        r"callback|webhook|notifyUrl|callbackUrl|targetUrl|remoteUrl|imageUrl|avatarUrl",
    )),
    QueryGroup("redirect-forward", "跳转/转发/Header", "开放重定向/转发", ("SSRF", "HTTP 响应拆分", "XSS"), "中", (
        r"sendRedirect|redirect:|forward:|RequestDispatcher|response\.setHeader|response\.addHeader",
        r"Location|returnUrl|redirectUrl|nextUrl|backUrl|goto|target|callback",
        r"setStatus\(30|HttpStatus\.FOUND|HttpStatus\.MOVED|ResponseEntity\.status",
    )),
    QueryGroup("cloud-storage-network", "云存储/外部存储/网络文件", "SSRF", ("凭据泄露", "路径穿越", "敏感信息泄露"), "中", (
        r"AmazonS3|S3Client|S3Object|MinioClient|OSSClient|ObsClient|CosClient|BlobClient",
        r"FTPClient|SFTP|ChannelSftp|JSch|SmbFile|jcifs|NtlmPasswordAuthentication",
        r"putObject|getObject|presigned|preSigned|bucket|objectKey|endpoint|endpointUrl",
    )),
    QueryGroup("xml-xxe", "XML/XXE/XPath/XSLT", "XXE", ("XPath 注入", "XSLT 注入", "SSRF", "文件读取"), "高", (
        r"DocumentBuilderFactory|SAXParserFactory|XMLInputFactory|SAXReader|SAXBuilder|JDOM|dom4j",
        r"JAXBContext|Unmarshaller|Marshaller|XMLReader|SAXSource|StreamSource|InputSource",
        r"TransformerFactory|Transformer|Templates|URIResolver|XPathFactory|XPath\.evaluate|SchemaFactory",
        r"DOCTYPE|ENTITY|external-general-entities|external-parameter-entities|ACCESS_EXTERNAL_DTD|ACCESS_EXTERNAL_SCHEMA",
    )),
    QueryGroup("ldap-directory", "LDAP/目录查询", "LDAP 注入", ("认证绕过", "敏感信息泄露"), "高", (
        r"DirContext|InitialDirContext|LdapContext|LdapTemplate|SearchControls|NamingEnumeration",
        r"ldap://|ldaps://|distinguishedName|userDn|baseDn|filter\s*=|\(uid=|\(cn=",
        r"DirContext\.search|ldapTemplate\.search|authenticate\(|bind\(|lookup\(",
    )),
    QueryGroup("deserialization-java", "反序列化/Java 原生与传输", "反序列化", ("JNDI/远程查找", "RCE"), "高", (
        r"ObjectInputStream|readObject|readUnshared|resolveClass|ObjectMessage|getObject\(",
        r"XMLDecoder|Hessian|Burlap|Kryo|FST|Protostuff|SerializationUtils\.deserialize",
        r"RMI|UnicastRemoteObject|Registry\.lookup|Naming\.lookup|MarshalledObject",
    )),
    QueryGroup("deserialization-json-yaml", "反序列化/JSON/YAML 多态", "反序列化", ("JNDI/远程查找", "代码/脚本注入", "RCE"), "高", (
        r"fastjson|JSON\.parseObject|parseArray|ParserConfig|autoType|SupportAutoType|JSONReader\.Feature",
        r"ObjectMapper|enableDefaultTyping|activateDefaultTyping|@JsonTypeInfo|DefaultTyping|PolymorphicTypeValidator",
        r"XStream|fromXML|allowTypes|SnakeYAML|new Yaml|Constructor\(|TypeDescription",
        r"InitialContext|JNDI|lookup\(|ldap://|rmi://|iiop://",
    )),
    QueryGroup("xss-response", "XSS/响应输出", "XSS", ("HTTP 响应拆分", "敏感信息泄露"), "中", (
        r"getWriter|print\(|write\(|ResponseEntity|StreamingResponseBody|text/html|application/javascript",
        r"ModelAndView|addAttribute|addObject|out\.print|innerHTML|document\.write",
        r"StringEscapeUtils\.unescape|HtmlUtils\.htmlUnescape|escapeXml\s*=\s*\"false\"",
    )),
    QueryGroup("mass-assignment", "Mass Assignment/属性越权", "Mass Assignment", ("水平/垂直越权", "金额/状态篡改", "租户越权"), "中", (
        r"BeanUtils\.copyProperties|PropertyUtils|ModelMapper|DozerBeanMapper|BeanCopier",
        r"@RequestBody|@ModelAttribute|Map<String|JSONObject|JsonNode|updateById|saveOrUpdate|merge\(|save\(",
        r"role|admin|isAdmin|status|price|amount|balance|userId|tenantId|ownerId|orgId|permission",
    )),
    QueryGroup("secrets-config", "凭据/敏感配置", "硬编码凭据/密钥", ("敏感信息泄露", "横向访问风险"), "高", (
        r"password|passwd|pwd|secret|token|accessKey|secretKey|privateKey|BEGIN RSA|BEGIN PRIVATE KEY",
        r"jdbc:|redis:|mongodb:|mysql:|postgresql:|oracle:|ftp|smtp|credential|apikey|api_key",
        r"AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|xox[baprs]-|-----BEGIN",
    )),
    QueryGroup("crypto-random", "密码学/随机数/Token", "弱密码学", ("Token 可预测", "认证绕过辅助链"), "中", (
        r"MD5|SHA1|SHA-1|DES|3DES|RC4|AES/ECB|NoPadding|MessageDigest|getInstance\(\"MD5|getInstance\(\"SHA1",
        r"Random\(|Math\.random|RandomStringUtils|UUID\.randomUUID|SecureRandom",
        r"Cipher\.getInstance|Mac\.getInstance|KeyGenerator|PBEKeySpec|static final .*KEY|static final .*IV",
    )),
    QueryGroup("tls-trust", "TLS/证书信任", "TLS 信任错误", ("SSRF", "敏感信息泄露"), "高", (
        r"TrustManager|X509TrustManager|HostnameVerifier|ALLOW_ALL|NoopHostnameVerifier|TrustAll",
        r"checkServerTrusted|verify\(.*SSLSession|setHostnameVerifier|SSLContext\.getInstance",
        r"disableCertificateValidation|ignoreSsl|trustAllCerts|setDefaultHostnameVerifier",
    )),
    QueryGroup("cors-csrf-cookie", "CORS/CSRF/Cookie", "CORS/CSRF 配置缺陷", ("Cookie 安全属性缺失", "认证绕过辅助链"), "中", (
        r"@CrossOrigin|CorsConfiguration|allowedOrigins|allowedOriginPatterns|allowCredentials|CorsFilter",
        r"csrf\.disable|CsrfFilter|csrfTokenRepository|SameSite|HttpOnly|Secure|setCookie|addCookie",
        r"Origin|Referer|X-Requested-With|CookieSerializer|DefaultCookieSerializer",
    )),
    QueryGroup("debug-admin-endpoints", "管理/调试端点", "Actuator/调试接口暴露", ("未授权访问", "敏感信息泄露"), "高", (
        r"actuator|management\.endpoints|heapdump|threaddump|env|configprops|prometheus|metrics",
        r"swagger|springfox|OpenAPI|api-docs|v2/api-docs|v3/api-docs|debug|trace",
        r"Jolokia|JMX|DruidStatView|StatViewServlet|H2 Console|Arthas|Dubbo Admin",
    )),
    QueryGroup("logging-audit", "日志/审计", "日志注入", ("审计污染", "敏感信息泄露"), "低", (
        r"logger\.|log\.|audit|access log|login failed|userAgent|remoteAddr|X-Forwarded-For",
        r"printStackTrace|e\.getMessage|getStackTrace|StackTraceElement|Throwable",
        r"CRLF|\\r|\\n|replaceAll\(.*\\n|MDC\.put|ThreadContext\.put",
    )),
    QueryGroup("resource-redos", "ReDoS/资源消耗", "ReDoS/资源消耗", ("批量导出", "业务滥用"), "中", (
        r"Pattern\.compile|matches\(|replaceAll|split\(|Matcher\.find|Matcher\.matches",
        r"while\(true\)|recursive|Thread\.sleep|CountDownLatch|parallelStream|CompletableFuture",
        r"pageSize|limit|batch|export|downloadAll|ZipInputStream|BigDecimal|parse|readAllBytes",
    )),
    QueryGroup("business-sensitive-flow", "业务安全关键词", "业务流程滥用", ("越权", "回调伪造", "金额篡改", "验证码绕过"), "中", (
        r"resetPassword|changePassword|forgotPassword|verifyCode|captcha|smsCode|emailCode|otp",
        r"pay|refund|withdraw|transfer|balance|amount|price|discount|coupon|invoice",
        r"approve|audit|role|permission|tenant|org|owner|callback|notify|webhook|order|status",
    )),
)


def markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def candidate_sources(workspace: Path, explicit_sources: list[Path]) -> list[Path]:
    sources = [path.resolve() for path in explicit_sources if path.exists()]
    if sources:
        return sources

    defaults = [
        workspace / "decompiled",
        workspace / "src",
        workspace / "source",
        workspace / "sources",
        workspace / "classes",
        workspace / "unpacked",
        workspace / "exploded",
        workspace / "bytecode",
    ]
    return [path.resolve() for path in defaults if path.exists()]


def run_rg(rg_bin: str, pattern: str, sources: list[Path], max_hits: int) -> list[tuple[str, str, str]]:
    command = [
        rg_bin,
        "-n",
        "-a",
        "-i",
        "--no-heading",
        "--color",
        "never",
        "-g",
        "!tools/**",
        "-g",
        "!logs/**",
        "-g",
        "!reports/**",
        "-g",
        "!evidence/**",
        "--",
        pattern,
        *[str(source) for source in sources],
    ]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode not in {0, 1}:
        raise RuntimeError(proc.stderr.strip() or f"rg 执行失败: {pattern}")

    hits: list[tuple[str, str, str]] = []
    for line in proc.stdout.splitlines():
        if len(hits) >= max_hits:
            break
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        hits.append((parts[0], parts[1], parts[2]))
    return hits


def select_query_groups(selected: list[str]) -> tuple[QueryGroup, ...]:
    if not selected:
        return QUERY_GROUPS

    selected_set = set(selected)
    groups = tuple(group for group in QUERY_GROUPS if group.slug in selected_set)
    missing = sorted(selected_set - {group.slug for group in groups})
    if missing:
        valid = ", ".join(group.slug for group in QUERY_GROUPS)
        raise ValueError(f"未知查询组: {', '.join(missing)}；可用查询组: {valid}")
    return groups


def write_group_hits(output_dir: Path, group: QueryGroup, rows: list[dict[str, str]]) -> None:
    path = output_dir / f"{group.slug}.md"
    lines = [
        f"# {group.title} Query Hits",
        "",
        "| 编号 | 漏洞族 | 优先级 | 命中模式 | 文件 | 行号 | 上下文 | 可映射漏洞族 | 处理状态 | 候选 ID | 处理说明 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {family} | {priority} | {pattern} | {file} | {line} | {context} | {mapped} | 未处理 |  |  |".format(
                id=row["id"],
                family=markdown_cell(row["family"]),
                priority=markdown_cell(row["priority"]),
                pattern=markdown_cell(row["pattern"]),
                file=markdown_cell(row["file"]),
                line=markdown_cell(row["line"]),
                context=markdown_cell(row["context"]),
                mapped=markdown_cell(row["mapped"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(output_dir: Path, workspace: Path, sources: list[Path], summaries: list[tuple[QueryGroup, int]]) -> None:
    lines = [
        "# Query Pack 检索索引",
        "",
        f"生成时间: {datetime.now().isoformat(timespec='seconds')}",
        f"审计工作目录: {workspace}",
        "",
        "## 检索范围",
        "",
    ]
    for source in sources:
        lines.append(f"- {source}")
    lines.extend([
        "",
        "## 汇总",
        "",
        "| 查询组 | 文件 | 命中数 | 未处理 | 说明 |",
        "|---|---|---:|---:|---|",
    ])
    for group, count in summaries:
        hit_file = f"{group.slug}.md" if count else "无"
        lines.append(f"| {markdown_cell(group.title)} | {hit_file} | {count} | {count} | 命中需归类，不能直接作为漏洞 |")
    output_dir.joinpath("index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def reset_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for markdown_file in output_dir.glob("*.md"):
        markdown_file.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 Java Web 审计 Query Pack")
    parser.add_argument("--workspace", type=Path, required=True, help="审计工作目录")
    parser.add_argument("--source", type=Path, action="append", default=[], help="额外检索源码或反编译目录，可重复")
    parser.add_argument("--group", action="append", default=[], help="只运行指定查询组 slug，可重复")
    parser.add_argument("--list-groups", action="store_true", help="列出查询组后退出")
    parser.add_argument("--max-hits-per-query", type=int, default=200, help="单个查询模式最多记录命中数")
    args = parser.parse_args()

    if args.list_groups:
        for group in QUERY_GROUPS:
            print(f"{group.slug}\t{group.title}\t{group.priority}")
        return 0

    try:
        query_groups = select_query_groups(args.group)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    rg_bin = shutil.which("rg")
    if not rg_bin:
        print("[FAIL] 未找到 rg，请先安装 ripgrep 后再运行 Query Pack", file=sys.stderr)
        return 1

    workspace = args.workspace.resolve()
    sources = candidate_sources(workspace, args.source)
    if not sources:
        print("[FAIL] 未找到可检索源码或反编译目录，请使用 --source 指定目标", file=sys.stderr)
        return 1

    output_dir = workspace / "evidence" / "search-hits"
    reset_output_dir(output_dir)

    summaries: list[tuple[QueryGroup, int]] = []
    total_hits = 0
    for group in query_groups:
        rows: list[dict[str, str]] = []
        seen: set[tuple[str, str, str, str]] = set()
        for pattern in group.patterns:
            hits = run_rg(rg_bin, pattern, sources, args.max_hits_per_query)
            for file_path, line_no, context in hits:
                key = (file_path, line_no, context, pattern)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "id": f"HIT-{group.slug.upper().replace('-', '_')}-{len(rows) + 1:03d}",
                    "family": group.primary_family,
                    "priority": group.priority,
                    "pattern": pattern,
                    "file": file_path,
                    "line": line_no,
                    "context": context[:240],
                    "mapped": "、".join(group.mapped_families),
                })
        if rows:
            write_group_hits(output_dir, group, rows)
        summaries.append((group, len(rows)))
        total_hits += len(rows)

    write_index(output_dir, workspace, sources, summaries)
    print(f"[OK] Query Pack 完成，命中 {total_hits} 条，输出目录: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
