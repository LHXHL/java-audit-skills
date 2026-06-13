# Skills 说明

本目录保存 Java Audit Skills 的正式 skill 集合。新版结构强调“按职责加载、按证据交接、按专项下结论”：每个 `SKILL.md` 只负责说明何时触发、何时不触发、成功标准、工作流、强制规则和 eval；大段规则、模板、payload 注意事项和框架细节放在对应 `references/` 中按需读取。

## 总体原则

- `description` 写加载时机，不写宣传式功能介绍。
- `java-route-mapper` 产出入口面；`java-route-tracer` 产出调用链证据；专项漏洞 skill 才能做漏洞判定。
- `java-vuln-scanner` 只输出组件版本证据，不直接证明业务风险成立。
- `java-audit-pipeline` 只编排真实多 agent 流水线和 QA 门禁，不顺序模拟完整 team。
- 漏洞类 skill 必须区分 `确认漏洞`、`条件成立`、`待验证`、`不可确认`、`非漏洞`。
- 只有 `确认漏洞` 和 `条件成立` 项输出 Burp Suite 请求和低破坏 payload；其他状态只写证据缺口和补证方向。
- 所有数量、文件数、路由数、命中数都必须可复核；无法精确统计时写 `不可确认` 或 `未精确统计`。
- 正式报告不得包含输出自检、技能源校验、测试提示词、模型运行状态、内部规则编号、validator 过程或工具审批信息。

## 技能地图

| Skill | 分层 | 主要输入 | 主要输出 |
|---|---|---|---|
| `java-route-mapper` | 入口面数据底座 | Java Web 源码、WAR/class/JAR、框架配置 | 路由、HTTP 方法、入口方法、参数结构、WebService/SOAP operation |
| `java-route-tracer` | 调用链证据层 | 已知路由、入口方法、route mapper 批次 | 参数流向、变量变化、分支条件、sink 和可控性 |
| `java-auth-audit` | 认证授权专项 | 路由清单、鉴权配置、Filter/Interceptor、注解、业务权限代码 | 鉴权状态映射、确认/条件成立的认证授权风险、README 限制说明 |
| `java-sql-audit` | SQL 注入专项 | SQL/HQL/JPQL/native SQL sink、Mapper、调用链证据 | SQL 操作映射、注入结论、验证材料 |
| `java-file-upload-audit` | 文件上传专项 | 上传入口、文件名/目录/内容流向、写入 sink | 上传点映射、上传风险结论、验证材料 |
| `java-file-read-audit` | 文件读取专项 | 下载/读取入口、路径参数、FILE sink | 文件读取映射、路径遍历结论、验证材料 |
| `java-xxe-audit` | XML/XXE 专项 | XML/SOAP 输入、解析器、factory/resolver 配置 | XML 解析器映射、XXE 结论、验证材料 |
| `java-deserialization-audit` | 反序列化专项 | DESERIALIZE sink、组件命中、gadget/JDK 条件 | 反序列化 sink 映射、可利用性结论、验证材料 |
| `java-vuln-scanner` | 组件版本证据层 | pom.xml、build.gradle、WEB-INF/lib、JAR/WAR | 依赖版本证据、本地规则命中、触发面交接方向 |
| `java-audit-pipeline` | 编排与质检层 | source_path、output_path、真实 team 能力 | 阶段产物、QA 报告、quality_report 或 pipeline_blocked |

## 推荐流转

### 单项审计

1. 入口不清楚时，先运行 `java-route-mapper`。
2. 需要证明请求参数是否到达 sink 时，运行 `java-route-tracer`。
3. 根据 sink 类型进入专项 skill：SQL、XXE、上传、文件读取、反序列化或鉴权。
4. 依赖版本问题单独交给 `java-vuln-scanner`；命中后再按触发面交给专项 skill。

### 完整审计

1. `java-audit-pipeline` 初始化输出目录、配置和阶段计划。
2. 阶段 1 并行产出 `route_mapper/`、`auth_audit/`、`vuln_report/`。
3. 阶段 2 做路由风险分级和组件/鉴权发现聚合。
4. 阶段 3 基于高风险路由分批运行 `java-route-tracer`。
5. 阶段 4 只对命中的 sink 启动对应专项 worker；无 sink 的目录写 `SKIPPED.md`。
6. 阶段 5 由独立 QA 汇总 `quality_report.md`。

如果没有真实 team / 多 agent 调度能力，pipeline 必须生成 `pipeline_blocked.md`，不能用单进程顺序跑出的报告冒充完整流水线。

## 各 Skill 边界

### java-route-mapper

定位：Java Web 入口面数据底座，只回答“有哪些可访问入口、入口在哪里、请求参数从哪里来”。

使用场景：

- 提取 Spring MVC、Servlet、JAX-RS、Struts2、CXF/JAX-WS/Axis 等入口。
- 生成 route mapper 输出供鉴权、调用链、漏洞专项或 pipeline 使用。
- 大型项目按模块、namespace、worker 范围拆分路由提取。

不使用场景：

- 判断漏洞、鉴权是否正确、组件 CVE 或完整调用链。
- 已有完整路由清单，只做 OpenAPI/Postman/人类文档转换。
- 非 Web Java 程序且没有 HTTP/WebService 入口。

交付重点：

- 完整 URL、HTTP 方法、入口类/方法、源码或反编译位置。
- Path、Query/Form、Body、Header、Cookie、File、SOAP 参数结构。
- WebService endpoint 地址必须来自真实配置，不用类名或 bean id 猜测。
- 通配符、dispatch 网关、Struts 动态 action 要展开真实可达实例。

### java-route-tracer

定位：调用链证据层，从已知入口追踪参数到 sink，不直接下漏洞结论。

使用场景：

- 追踪指定路由、入口方法或 pipeline 批次中的参数流向。
- 判断参数是否到达 SQL、FILE、XML、COMMAND、HTTP、LDAP、EXPRESSION、DESERIALIZE、RESPONSE 等 sink。
- 为 SQL/XXE/上传/文件读取/反序列化专项准备可控性和分支证据。

不使用场景：

- 只提取全量路由。
- 直接判断 SQL、XXE、上传、文件读取、反序列化或鉴权漏洞。
- 没有明确路由、入口方法、route mapper 输出或可定位范围时做全项目“所有调用链”。

交付重点：

- 入口证据、HTTP 请求模板、参数结构和调用层级。
- 变量改名、DTO/Map 字段、覆盖、校验、白名单、提前返回和异常路径。
- sink 类型、代码位置、分支条件和可控性结论。
- 上游鉴权状态只透传，不自行鉴权。

### java-auth-audit

定位：认证授权专项，判断入口是否被正确认证、授权是否可绕过、对象访问是否越权。

使用场景：

- 审计未授权访问、认证绕过、权限提升、IDOR、水平/垂直越权。
- 分析 Shiro、Spring Security、JWT、Session、Filter、Interceptor、方法注解或自定义权限逻辑。
- 基于 route mapper 输出生成路由鉴权映射。

不使用场景：

- 只提取路由、依赖 CVE、SQL/XXE/上传/文件读取/反序列化。
- Cookie 属性、session timeout、CSRF/CORS、密码策略等通用加固项，除非直接导致认证或授权绕过。

交付重点：

- 完整鉴权链路：网关、Filter、Interceptor、框架配置、方法注解、业务权限、对象归属校验。
- 三文件输出：主报告、鉴权映射、README。
- `确认漏洞` 和 `条件成立` 必须有真实入口、证据链、Burp 请求、角色/对象变体和限制说明。

### java-sql-audit

定位：SQL 注入专项判定层。

使用场景：

- 审计 JDBC、MyBatis、Hibernate、JPA、Mapper XML、动态 SQL、ORDER BY、动态表名/列名。
- route-tracer 已报告 SQL/HQL/JPQL/native SQL sink，需要做专项结论。
- 字节码或部署包中存在 DAO、Repository、Mapper、SqlProvider 候选，需要按需反编译。

不使用场景：

- 只梳理路由、只追踪调用链、只做鉴权或组件版本扫描。
- 只有 DAO/Mapper 方法名但没有真实实现、Mapper XML、SQL API 调用或反编译结果。
- 用户要求未授权攻击、批量数据抽取、DNS/OOB、命令执行或破坏性验证。

交付重点：

- 入口、可控参数、数据流、真实 SQL sink、防护状态和代码位置。
- 参数绑定、白名单、类型转换、数据库/环境分支和执行条件。
- 严格使用 6 个编号章节；确认/条件成立项输出 Burp 请求和 payload。

### java-file-upload-audit

定位：文件上传专项判定层。

使用场景：

- 审计 MultipartFile、Part、Commons FileUpload、FileItem、Base64/JSON 上传。
- 判断文件名、目录、内容、保存路径、校验顺序、Web 可访问性和覆盖策略。
- route-tracer 已证明上传参数到达文件写入 sink。

不使用场景：

- 文件下载或任意文件读取。
- 普通服务端导出、模板生成、缓存落盘，且没有外部上传内容/文件名/目录输入。
- 生成可执行后门样本、持久化内容、横向移动或批量验证脚本。

交付重点：

- 入口、文件内容来源、文件名来源、保存目录、写入 sink、校验逻辑和执行条件。
- 文件名净化、路径规范化、目录限制、扩展名、Content-Type、魔数、大小限制、随机重命名。
- 验证 payload 使用无害 marker，不输出可执行后门内容。

### java-file-read-audit

定位：任意文件读取和路径遍历专项判定层。

使用场景：

- 审计文件下载、预览、资源读取、模板读取、FileInputStream、FileReader、Files.read*、response 输出链路。
- 判断外部输入是否影响文件名、路径、资源 key、下载 ID 或数据库路径字段。
- route-tracer 已报告 FILE sink，需要做专项结论。

不使用场景：

- 文件上传、任意文件写入或 WebShell 上传。
- SQL、XXE、反序列化、鉴权、SSRF、命令执行或组件 CVE。
- 路径完全由服务端常量、闭合 ID 映射或不可控配置决定。

交付重点：

- 真实读取/下载/资源 sink、路径可控性、防护状态和代码位置。
- canonical/normalize、基础目录、ID 映射、白名单、扩展名、URL 解码和路径分隔符处理。
- 不输出真实敏感文件内容、生产路径或批量读取 payload。

### java-xxe-audit

定位：XML 外部实体和 XML 解析安全配置专项判定层。

使用场景：

- 审计 JAXP、JDOM、dom4j、StAX、JAXB、Transformer、Schema、XStream XML 解析风险。
- 分析 SOAP/XML 请求体、Content-Type、parser/factory/resolver 安全配置。
- route-tracer 已报告用户输入到达 XML 解析器或 XML 工具类。

不使用场景：

- 只看到 XML 文件、Spring bean、SOAP 配置或 `@WebService`，但没有解析 API 或外部实体处理证据。
- XStream/JAXB 的对象反序列化 gadget 风险，应交给 `java-deserialization-audit`。
- 组件版本 CVE 扫描。

交付重点：

- 用户可控 XML、真实解析 sink、防护配置、入口地址和输出条件。
- WebService endpoint 必须来自 CXF/JAX-WS 配置、WSDL、注解或 route mapper 证据。
- payload 只使用授权测试环境的受控 canary 或无敏感测试文件占位符。

### java-deserialization-audit

定位：反序列化漏洞深度审计。

使用场景：

- 分析 DESERIALIZE sink、ObjectInputStream/readObject、XMLDecoder、Fastjson、XStream、JDBC、Shiro RememberMe、Log4j/JNDI。
- 判断 gadget 链、JDK/组件版本、classpath、过滤器、白名单/黑名单和出网条件。
- pipeline 阶段 4 中 route-tracer 或 vuln-scanner 给出反序列化相关证据。

不使用场景：

- 只查依赖版本或 CVE。
- 只审计普通 XXE、SQL 注入、路由提取或调用链证据。
- 只有 gadget 依赖，没有入口、自动触发点和危险原语。

交付重点：

- sink、入口可达性、用户可控性、分支条件、组件/JDK/gadget 条件。
- 组件版本命中只能作为输入证据，不能直接判定漏洞成立。
- payload 必须遵守授权测试语境，不生成删除文件、持久化、横向移动或批量利用内容。

### java-vuln-scanner

定位：组件版本证据层。

使用场景：

- 扫描 Maven、Gradle、JAR、WAR、WEB-INF/lib 中的依赖版本。
- 用本地 `java-vulnerability.yaml` 规则库匹配 CVE/组件风险。
- pipeline 需要组件版本命中清单，作为后续专项审计输入。

不使用场景：

- 证明某个业务风险真实成立。
- 输出可复制验证请求、攻击字符串、payload、CVSS、具体修复版本或维护版本承诺。
- 用户需要最新官方安全公告或实时 CVE 状态。

交付重点：

- 必须运行 `scripts/scan_dependencies.py` 获取 JSON 结果。
- 正式报告的组件、版本、规则/CVE 只能来自脚本 JSON。
- 状态只使用 `版本命中`、`触发面待核查`、`环境条件待确认`、`不可确认`、`未命中`。
- 对每个命中项说明需交给哪个专项 skill 继续确认触发面。

### java-audit-pipeline

定位：Claude team / 多 agent 编排 skill，不是漏洞检测 skill。

使用场景：

- 用户要求一键审计、完整安全审计流水线、Java 全链路审计。
- 用户明确要求多 agent、质检员、阶段门禁、返工或并行编排。
- 需要统一调度 route mapper、auth、vuln scanner、route tracer 和专项 worker。

不使用场景：

- 只需要单一 skill、单条调用链、依赖扫描或普通报告润色。
- 当前环境实际不能创建、等待、质检或关闭独立 agent；此时写阻塞报告，不顺序模拟。

交付重点：

- 初始化 `pipeline_plan.md`、`scripts/pipeline_config.json`、`team_execution.md`、`tmp/`、`decompiled/cache/`。
- 每个 worker 完成后由独立 `agent-7-x` 质检员校验；阶段门禁通过后才能进入下游。
- 产出 `qa_reports/`、`quality_report.md` 或 `pipeline_blocked.md`。
- 漏洞规则、模板、Burp 请求、payload 和结论均由对应子 skill 负责。

## 输出目录

统一输出目录建议为 `{project_name}_audit/`：

```text
{project_name}_audit/
├── route_mapper/
├── auth_audit/
├── vuln_report/
├── cross_analysis/
│   ├── high_risk_routes.md
│   ├── trace_batch_plan.md
│   ├── component_vulnerabilities.md
│   └── auth_bypass_vulnerabilities.md
├── route_tracer/
├── sql_audit/
├── xxe_audit/
├── file_upload_audit/
├── file_read_audit/
├── deserialization_audit/
├── qa_reports/
├── decompiled/
├── quality_report.md
└── pipeline_blocked.md
```

单项 skill 可以只生成自己的子目录；pipeline 需要保留完整目录结构。无 sink 的专项目录写 `SKIPPED.md`，用于区分“已判断不触发”和“漏跑”。

## References 与脚本

- 大段规则、模板、payload 注意事项和框架细节放在各 skill 的 `references/` 中。
- 共享反编译策略和通用输出规范放在 `java-shared/` 中。
- 运行期脚本保留在对应 skill 的 `scripts/` 下，例如 `java-vuln-scanner/scripts/scan_dependencies.py`。
- 维护/回归检查脚本放在 `tools/skill-maintenance/validators/`，仅用于本地验收辅助。

常用维护检查：

```bash
python3 -m py_compile tools/skill-maintenance/validators/*.py
python3 tools/skill-maintenance/validators/validate_vuln_output.py <输出目录>
python3 tools/skill-maintenance/validators/validate_auth_output.py <输出目录>
python3 tools/skill-maintenance/validators/validate_sql_output.py <输出目录>
python3 tools/skill-maintenance/validators/validate_file_read_output.py <输出目录>
python3 tools/skill-maintenance/validators/validate_route_tracer_output.py <输出目录>
python3 tools/skill-maintenance/validators/validate_pipeline_output.py <输出目录>
```

validator 不能替代人工审计判断，也不能把“validator 通过”写入正式报告或最终用户回复。

## 编写和修改 Skill 的约束

- 新增或重写内容默认使用中文；类名、方法名、配置键、CVE、命令和路径保持原文。
- `SKILL.md` 不堆长篇漏洞背景、工具教程或完整模板。
- reference 职责混杂时应拆分或重命名。
- 模板不得诱导模型编造 CVE、CVSS、修复版本、PoC、利用链或不可验证结论。
- 组件版本证据类 skill 不输出 Burp、payload、PoC、CVSS、具体修复版本或确认性漏洞结论。
- 漏洞类 skill 的确认项必须给出可交付给开发单位的验证材料；待验证、不可确认和非漏洞项不得补写验证材料。
