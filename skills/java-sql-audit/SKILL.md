---
name: java-sql-audit
description: 当用户要求审计 Java 源码中的 SQL 注入、动态 SQL 拼接、JDBC/MyBatis/Hibernate/JPA 查询参数化缺陷，或 pipeline 已有路由/调用链证据需要判定 SQL sink 是否可被用户输入影响时使用；只做路由梳理、调用链追踪、鉴权、XXE、文件、反序列化或组件 CVE 扫描时不要使用。
---

# Java SQL Audit

## 当前定位

`java-sql-audit` 是 Java 审计技能集中的 SQL 注入专项判定层。它消费源码、Mapper XML、反编译结果、`java-route-mapper` 路由清单或 `java-route-tracer` 调用链证据，回答：

- 是否存在真实 SQL/HQL/JPQL/native SQL 执行点。
- 用户可控参数是否到达 SQL 值、标识符或查询片段。
- SQL 构造是否被参数绑定、白名单、强类型转换或不可达路径保护。
- 风险应标为确认漏洞、条件成立、待验证、不可确认还是非漏洞。
- 对确认漏洞或条件成立风险，给出授权测试环境可复现的低风险 Burp Suite 请求和 payload。

本 skill 不负责全量路由枚举，不替代调用链追踪，不判断鉴权漏洞，不扫描依赖 CVE，不输出破坏性 SQL payload 或未授权攻击请求。

## 上下游边界

上游输入可以是：

- 用户指定的 Java 项目路径、路由、类、方法、Mapper XML、DAO/Repository 或查询代码片段。
- `java-route-mapper` 产出的路由、参数和入口方法清单。
- `java-route-tracer` 产出的调用链、可控性、分支条件和 sink 候选。
- 源码不可用时的 `.class`、`.jar`、`.war` 或已有反编译结果。

下游通常读取：

- SQL 注入审计报告。
- 按根因聚合后的受影响入口、证据链、限制说明。
- 确认漏洞或条件成立项的 Burp Suite 请求和 payload，用于授权环境复核。
- 待验证或不可确认项的补证清单。

相邻 skill 边界：

- `java-route-mapper`：枚举路由和入口参数；本 skill 只消费其结果，不重新定义路由体系。
- `java-route-tracer`：追踪参数到 sink；本 skill 只在需要数据流证据时读取或请求调用链追踪，不把 `Manager/DAO` 方法名当 SQL 证据。
- `java-auth-audit`：判断鉴权/越权；本 skill 只引用鉴权上下文，不扩写成鉴权漏洞。
- `java-xxe-audit`、`java-file-upload-audit`、`java-file-read-audit`、`java-deserialization-audit`：处理非 SQL sink；发现这些 sink 时只记录交接建议。
- `java-vuln-scanner`：扫描依赖组件 CVE；本 skill 不编造 CVE、CVSS 或修复版本。

## 触发条件

满足任一条件时触发：

- 用户明确要求审计 SQL 注入、JDBC、MyBatis、Hibernate、JPA、Mapper XML、`ORDER BY` 注入、动态表名/列名或动态查询拼接。
- pipeline 需要判断某个 `SQL`、`HQL`、`JPQL`、`native SQL`、Mapper statement 或查询 API sink 是否构成注入风险。
- `java-route-tracer` 已报告 SQL sink 证据，需要做安全结论和可复核交付。
- 源码缺失但字节码中可能包含 DAO/Mapper/Repository/SqlProvider，需要反编译后审计 SQL 逻辑。
- 用户给出候选代码片段，要求判断外部输入是否影响 SQL 执行。

## 不触发条件

以下情况不要触发本 skill：

- 只要求列出 Java Web 路由、Controller、Servlet 或 WebService operation。
- 只要求追踪参数调用链，不要求判断 SQL 注入。
- 只看到 `Manager`、`Service`、`DAO`、`Repository`、`Mapper` 方法名，但没有真实实现、Mapper XML、反编译结果或 SQL API 调用。
- 只审计鉴权、越权、未授权、角色绕过。
- 只扫描依赖版本、CVE、License 或 SCA。
- SQL 字符串完全由常量、枚举或不可变配置组成，且没有用户可控数据进入。
- 用户要求批量扫描线上目标、未授权攻击、破坏性 payload、堆叠查询、写文件、命令执行或数据外带。

## 成功标准

合格输出必须同时满足：

- 每个结论都有入口、可控参数、数据流、真实 SQL sink、防护状态和代码位置。
- 不把候选风险、命名相似、缺失实现、`UNCONFIRMED` sink 或单独的 `${}` 命中写成已确认漏洞。
- 明确区分确认漏洞、条件成立、待验证、不可确认和非漏洞。
- 对参数绑定、白名单、类型转换、分支条件、数据库类型和环境依赖给出证据。
- 同根因多入口按 `../java-shared/VULNERABILITY_GROUPING.md` 聚合；不同鉴权、环境、sink 或修复点拆分。
- `结论统计` 数量必须与 `SQL 操作映射` 中各状态行数一致；过滤器启用状态、框架版本、配置观察等非 SQL sink 信息只能放入第 4 节或第 6 节。
- 报告严格使用 `references/OUTPUT_TEMPLATE.md` 的 6 个编号章节，章节名和顺序不得改变，不得添加 `## 0`、`## 7`、`## 输出自检`、技能源校验或测试验收信息。
- 确认漏洞或条件成立项必须包含 Burp Suite 请求和 payload；待验证、不可确认和非漏洞项不得输出可复制请求。
- 不编造 CVE、CVSS、修复版本、数据库类型、表结构、返回包、漏洞利用成功或不存在的代码路径。
- 正式报告只描述代码证据和证据缺口，不暴露工具权限、网络限制、命令失败、模型规则编号或测试过程。

## 工作流

### 1. 确定审计范围

- 读取用户指定路径、候选路由、类、方法和已有上游报告。
- 如果没有入口证据，仍可做 sink 盘点，但结论只能是“待验证”或“不可确认”，不能写成外部可利用。
- 如果只有 `java-route-tracer` 的 `UNCONFIRMED` sink，先定位实现源码、Mapper XML 或反编译结果；找不到时停止漏洞判定并记录限制。

### 2. 选择 reference

- 通用行为规则：读取 `references/SQL_DETECTION_RULES.md`。
- JDBC/`Statement`/`PreparedStatement`：读取 `references/JDBC.md`。
- MyBatis XML、注解、`SqlProvider`：读取 `references/MYBATIS.md`。
- Hibernate/JPA/HQL/JPQL/native query/Criteria：读取 `references/HIBERNATE.md`。
- 源码缺失或只给字节码：读取 `references/DECOMPILE_STRATEGY.md`。
- 需要输出 Burp Suite 请求或 payload：读取 `references/VALIDATION_GUIDE.md`。
- 生成报告前：读取 `references/OUTPUT_TEMPLATE.md`。

### 3. 定位 SQL sink

优先查找真实执行点，而不是只看类名：

- JDBC：`Statement.execute*`、`PreparedStatement`、`CallableStatement`、`JdbcTemplate`、`NamedParameterJdbcTemplate`。
- MyBatis：`*Mapper.xml`、`${}`、`#{}`、`@Select/@Update/@Insert/@Delete`、`@*Provider`。
- Hibernate/JPA：`createQuery`、`createNativeQuery`、`createSQLQuery`、`@Query`、`Restrictions.sqlRestriction`、`EntityManager` 查询。
- SQL 构造器：`StringBuilder`、`StringBuffer`、`String.format`、`MessageFormat`、自定义 `SqlBuilder`、分页/排序工具。

### 4. 追踪可控性和防护

- 从入口参数、JSON 字段、请求体、Header、Cookie、路径变量或 RPC 参数追踪到 SQL sink。
- 记录变量改名、对象字段、Map key、DTO 反序列化、默认值覆盖和类型转换。
- 参数被硬编码覆盖、枚举转换、强类型解析失败即中断时，应降低或取消注入结论。
- 值位置优先检查参数绑定；表名、列名、排序字段、排序方向、函数名和 SQL 片段必须检查闭合集合白名单。
- 有 SQL 拼接但缺入口、缺可控性或缺执行条件时，输出为“待验证/不可确认”，不是确认漏洞。

### 5. 输出报告

- 使用 `references/OUTPUT_TEMPLATE.md` 生成 6 个编号章节。
- 遵守 `../java-shared/VULNERABILITY_GROUPING.md` 的聚合规则。
- 对没有确认漏洞的审计，也要输出已检查的 SQL 操作、非漏洞依据、待验证项和限制。
- 确认漏洞或条件成立项按 `references/VALIDATION_GUIDE.md` 输出 Burp Suite 请求和 payload；其他状态只写补证路径。
- 非 SQL sink 的过滤器启用状态、配置观察、依赖版本信息不要写入 `SQL 操作映射`，避免统计口径漂移。

## Hard Rules

1. 没有真实 SQL/HQL/JPQL/native SQL sink，不得下 SQL 注入结论。
2. 没有用户可控数据流，不得下 SQL 注入结论。
3. 没有证据证明防护缺失或不足，不得下 SQL 注入结论。
4. `java-route-tracer` 的 `UNCONFIRMED`、`Manager.xxx()`、`DAO.xxx()`、接口方法名只表示待查，不是 SQL sink。
5. `PreparedStatement` 只有在 SQL 结构本身被用户输入拼接，或混用拼接导致用户可控 SQL 片段时才判风险；单纯 `?` 绑定值不是注入。
6. MyBatis `${}` 是高风险信号，但必须结合参数来源、上下文位置和白名单；常量、枚举或闭合集合选择不能直接判漏洞。
7. MyBatis `#{}`、Hibernate/JPA `setParameter`、JDBC `setXxx` 通常视为值绑定安全；若周围仍拼接标识符或 SQL 片段，需要单独分析该片段。
8. 白名单必须是闭合集合或等价严格映射；仅做非空、长度、去引号、黑名单替换或宽松正则不是充分防护。
9. 确认漏洞和条件成立项必须给 Burp Suite 请求和 payload；待验证、不可确认、非漏洞项不得给可复制请求。
10. SQL payload 只能用于授权测试环境的低风险复核，不得包含 DML/DDL、堆叠查询、时间延迟、命令执行、文件读写、数据外带或批量利用。
11. Burp 请求必须匹配真实入口、HTTP 方法、参数名和 Content-Type；无法确认入口时不得编造请求。
12. 不编造 CVE、CVSS、修复版本、数据库类型、表结构、返回包、漏洞利用成功或未读取过的文件内容。
13. 发现非 SQL sink 时只记录交接建议，不在本报告中扩写其他漏洞。
14. 结论状态必须使用中文枚举：确认漏洞、条件成立、待验证、不可确认、非漏洞。
15. 反编译证据必须能指向真实存在的源码文件、反编译输出文件或 class/jar 来源；路径不存在、未实际读取或只有“应当存在”的推断时，不得作为确认漏洞证据。
16. Java `String.format` 只替换 `%s`、`%d` 等格式符，不替换 `{0}`；`{0}` 只有在 `MessageFormat.format` 或项目自定义 formatter 等真实调用下才表示替换。
17. 正式报告不得出现 `## 输出自检`、技能源校验、测试提示词、Claude 运行状态或验收清单。
18. 正式报告不得写“网络受限”“命令受限”“无法获取工具”“hard rule”“根据 skill 规则”等内部运行或规则执行信息；只写“本轮未取得关键类可读实现/反编译方法体”等证据缺口。
19. `SQL 操作映射` 的每一行只能有一个结论状态；若同一 SQL 同时含安全命名参数和未确认动态片段，按未确认动态片段状态记录为“待验证/不可确认”，不要写“非漏洞；片段待补证”。
20. 报告表格序号必须连续，不得跳号。

## Gotchas

- `ORDER BY ${sort}` 常见，但如果 Java 层把 `sort` 映射为固定列名，不能判漏洞。
- `LIKE '%${keyword}%'` 高风险，但如果 `keyword` 来源是服务端常量或不可控字典项，应标为非用户可控。
- `PreparedStatement pstmt = conn.prepareStatement("select x from t order by " + orderBy)` 仍可能有注入，因为拼接发生在 prepare 之前。
- `Integer.parseInt(request.getParameter("id"))` 后拼接到 SQL，通常不等价于字符串 SQL 注入；仍可建议参数化，但不要夸大。
- MyBatis `IN (${ids})` 只有当 `ids` 可由用户直接控制且无解析/白名单时才成立；如果已拆分为数字列表并用 `<foreach>#{id}</foreach>`，不是注入。
- `@Query(nativeQuery = true)` 不自动危险；看是否有参数绑定或 SpEL/字符串拼接。
- 数据库类型分支会改变结论：Oracle 分支有拼接而目标只运行 MySQL 时，最多写环境依赖或不可确认。
- 日志中的 SQL 字符串不等于执行 SQL；必须找到执行 API。
- 反编译代码可能丢失行号或泛型；报告应标注来源和可信度，不要捏造源码行号。
- “未反编译实现类，但同包其它方法使用 Hibernate Criteria”不是非漏洞证据；只能写“不可确认”或继续反编译实现。
- 对待验证项输出 Burp 请求会误导开发单位按确认漏洞处理，属于不合格输出。
- 确认漏洞没有 payload 或 Burp 请求会缺少可复核交付物，属于不合格输出。
- 把 `SQLCheckFilter` 是否启用、框架版本或配置导入关系当作 SQL 操作映射行，会导致结论统计失真；这些只能作为上下文或限制说明。
- 同一行同时写“非漏洞”和“待补证”会让开发单位无法判断状态；应拆分或按风险片段状态降级为待验证/不可确认。
- “无法获取 CFR/javap/网络受限”是工具过程，不是代码证据；报告只能写关键类方法体未取得。
- 在 SQL 报告中列组件版本并建议扫描 CVE 会越界到组件扫描；只写“如需依赖风险，交给组件扫描专项”。
- 报告全文禁止出现三个连续英文句点；需要省略时写“省略非关键字段”。

## 停止、确认或切换条件

- 找不到实现源码、Mapper XML 或可用反编译结果时：停止确认漏洞，输出“不可确认”和缺失证据。
- 需要先知道入口参数或调用链时：切换到 `java-route-tracer`，完成证据后再回来判定。
- 需要判断未授权、越权或角色限制时：交给 `java-auth-audit`，本 skill 只引用其结果。
- 用户要求组件 CVE、版本漏洞或修复版本时：交给 `java-vuln-scanner`。
- 用户要求实际攻击、批量扫描线上目标或破坏性验证时：拒绝该部分，只保留静态审计和授权环境低风险复核建议。

## Eval

| 类型 | 用户请求或场景 | 预期行为 |
|------|----------------|----------|
| 正例 | “审计这个 Spring 项目的 MyBatis `${}` 是否有 SQL 注入。” | 触发，读取 MyBatis reference，追踪参数来源和白名单后输出 SQL 审计报告 |
| 正例 | “route-tracer 说 `/user/search` 参数到达 `UserDao.search`，判断 SQL 注入是否成立。” | 触发，读取 tracer 证据，验证 DAO/Mapper 实现后判定 |
| 正例 | “只有 WAR 包，帮我看 DAO 里有没有 SQL 拼接。” | 触发，读取反编译策略，先定位 SQL 相关 class |
| 反例 | “列出所有 Controller 路由和 Burp 请求模板。” | 不触发，使用 `java-route-mapper` |
| 反例 | “追踪 `/api/download` 参数到文件读取 sink。” | 不触发或只作为下游交接，使用 `java-route-tracer`/文件读取 skill |
| 反例 | “检查 Spring Security 是否缺少鉴权。” | 不触发，使用 `java-auth-audit` |
| 边界例 | `Manager.save(bean)` 名称像数据库保存，但没有实现源码 | 不下 SQL 结论，标记缺实现/需反编译 |
| 边界例 | Mapper XML 中有 `${column}`，Java 层 `column` 来自固定 enum 映射 | 记录高风险模式但判为有白名单保护或非漏洞 |
| 边界例 | SQL 拼接只在 Oracle 分支，目标数据库未知 | 标为环境依赖/待验证，不写确认漏洞 |
| 边界例 | `sql.xml` 模板有 `{0}`，但未定位 `MessageFormat.format` 或消费方 | 写不可确认，不把 `{0}` 当已执行拼接 |
| 失败案例 | 把所有 `${}` 命中都写成已确认高危 | 不合格，缺入口、可控性和防护分析 |
| 失败案例 | 把 `PreparedStatement` 值绑定报告成 SQL 注入 | 不合格，误判参数化查询 |
| 失败案例 | 确认漏洞或条件成立项没有 Burp Suite 请求和 payload | 不合格，缺少开发单位复核材料 |
| 失败案例 | 待验证或不可确认项输出可复制 Burp 请求 | 不合格，候选风险被包装成已确认漏洞 |
| 失败案例 | 输出 CVSS、CVE、修复版本、破坏性 payload 或模型自检章节 | 不合格，违反输出边界 |
| 失败案例 | 把过滤器未启用写成 SQL 操作映射里的非漏洞，导致统计数量和映射状态不一致 | 不合格，统计口径错误 |
| 失败案例 | 报告写“网络与命令受限”“hard rule 1-3”或列出组件版本/CVE 扫描建议 | 不合格，暴露内部过程或越界 |
| 失败案例 | 同一映射行状态写“非漏洞；动态片段待补证” | 不合格，结论状态混杂 |
