---
name: java-sql-audit
description: 当用户要求审计 Java 源码中的 SQL 注入、动态 SQL 拼接、JDBC/MyBatis/Hibernate/JPA 查询参数化缺陷，或 pipeline 已有路由/调用链证据需要判定 SQL sink 是否可被用户输入影响时使用；只做路由梳理、调用链追踪、鉴权、XXE、文件、反序列化或组件 CVE 扫描时不要使用。
---

# Java SQL Audit

## 当前定位

`java-sql-audit` 是 Java 审计技能集中的 SQL 注入专项判定层。它读取源码、Mapper XML、反编译结果、`java-route-mapper` 路由清单或 `java-route-tracer` 调用链证据，回答：

- 是否存在真实 SQL/HQL/JPQL/native SQL 执行点。
- 用户可控参数是否到达 SQL 片段、标识符或查询 API。
- SQL 构造是否使用安全参数绑定、白名单或类型转换。
- 分支、数据库类型、鉴权上下文和环境条件是否影响结论。
- 风险应标为确认漏洞、条件成立、待验证、不可确认还是非漏洞。

本 skill 不负责产出路由全量清单，不替代调用链追踪，不做鉴权结论，不扫描依赖 CVE，不生成破坏性 PoC。

## 上下游边界

上游输入可以是：

- 用户指定的 Java 项目路径、特定路由、类、方法、Mapper XML 或 DAO/Repository。
- `java-route-mapper` 产出的路由、参数和入口方法清单。
- `java-route-tracer` 产出的调用链、可控性、分支条件和 sink 候选。
- 源码不可用时的 `.class`、`.jar`、`.war` 或已有反编译结果。

下游通常读取：

- SQL 注入审计报告。
- 按根因聚合后的受影响入口、证据链和限制说明。
- 需要人工复核或环境确认的待验证项。

相邻 skill 边界：

- `java-route-mapper`：枚举路由和入口参数；本 skill 只消费其结果，不重新定义路由体系。
- `java-route-tracer`：追踪参数到 sink；本 skill 只在需要数据流证据时读取或请求调用链追踪，不把“调用到 Manager/DAO 名称”当 SQL 证据。
- `java-auth-audit`：判断鉴权/越权；本 skill 只透传上游鉴权上下文，不能自行扩大为鉴权漏洞。
- `java-xxe-audit`、`java-file-upload-audit`、`java-file-read-audit`、`java-deserialization-audit`：处理非 SQL sink；发现这些 sink 时切换或交接，不混写。
- `java-vuln-scanner`：扫描依赖组件 CVE；本 skill 不编造 CVE、CVSS、修复版本。

## 触发条件

满足任一条件时触发：

- 用户明确要求审计 SQL 注入、JDBC、MyBatis、Hibernate、JPA、Mapper XML、`ORDER BY` 注入、动态表名/列名或动态查询拼接。
- pipeline 阶段需要判断某个 `SQL`、`HQL`、`JPQL`、`native SQL`、`Mapper XML` 或查询 API sink 是否构成注入风险。
- `java-route-tracer` 报告中已有 SQL sink 证据，且需要从安全边界角度做漏洞判定。
- 源码缺失但字节码中可能包含 DAO/Mapper/Repository/SqlProvider，需要反编译后审计 SQL 逻辑。
- 用户给出候选代码片段，要求判断是否可由用户输入影响 SQL 执行。

## 不触发条件

以下情况不要触发本 skill：

- 只要求列出 Java Web 路由、Controller、Servlet 或 WebService operation。
- 只要求追踪参数调用链，不要求判断 SQL 注入。
- 只看到 `Manager`、`Service`、`DAO`、`Repository`、`Mapper` 方法名，但没有真实实现、Mapper XML、反编译结果或 SQL API 调用。
- 只审计鉴权、越权、未授权、角色绕过。
- 只扫描依赖版本、CVE、License 或 SCA。
- SQL 字符串完全由常量、枚举或不可变配置组成，且没有用户可控数据进入。
- 用户要求生成利用链、破坏性 payload、批量验证脚本或未授权攻击请求。

## 成功标准

合格输出必须同时满足：

- 每个结论都有入口、可控参数、数据流、真实 SQL sink、防护状态和代码位置。
- 不把候选风险、命名相似、缺失实现、`UNCONFIRMED` sink 或单独的 `${}` 命中写成已确认漏洞。
- 明确区分确认漏洞、条件成立、待验证、不可确认和非漏洞。
- 对参数绑定、白名单、类型转换、分支条件、数据库类型和环境依赖给出证据。
- 同根因多入口按 `../java-shared/VULNERABILITY_GROUPING.md` 聚合；不同鉴权、环境、sink 或修复点拆分。
- 报告严格使用 `references/OUTPUT_TEMPLATE.md` 的 6 个编号章节，章节名和顺序不得改变，不得添加 `## 0` 或额外编号章节，保留 `## 输出自检`，不保留占位符。
- 不编造 CVE、CVSS、修复版本、数据库类型、PoC 成功结果或不存在的代码路径。

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
- 生成报告前：读取 `references/OUTPUT_TEMPLATE.md`。

### 3. 定位 SQL sink

优先查找真实执行点，而不是只看类名：

- JDBC：`Statement.execute*`、`PreparedStatement`、`CallableStatement`、`JdbcTemplate`、`NamedParameterJdbcTemplate`。
- MyBatis：`*Mapper.xml`、`${}`、`#{}`、`@Select/@Update/@Insert/@Delete`、`@*Provider`。
- Hibernate/JPA：`createQuery`、`createNativeQuery`、`createSQLQuery`、`@Query`、`Restrictions.sqlRestriction`、`EntityManager` 查询。
- SQL 构造器：`StringBuilder`、`StringBuffer`、`String.format`、`MessageFormat`、自定义 `SqlBuilder`、分页/排序工具。

### 4. 追踪可控性

- 从入口参数、JSON 字段、请求体、Header、Cookie、路径变量或 RPC 参数追踪到 SQL sink。
- 记录变量改名、对象字段、Map key、DTO 反序列化、默认值覆盖和类型转换。
- 如果数据流跨多层且证据不足，切回 `java-route-tracer` 获取调用链；不要凭方法名推断。
- 参数被硬编码覆盖、枚举转换、强类型解析失败即中断时，应降低或取消注入结论。
- 只有“同包代码风格”“框架通常参数化”“未看到拼接”等弱证据时，不得写“非漏洞”；缺少真实实现或执行点时写“不可确认”。

### 5. 判定防护和执行条件

- 参数值位置优先检查参数绑定；标识符位置检查闭合集合白名单。
- `ORDER BY`、`GROUP BY`、表名、列名、方向、函数名、SQL 片段不能靠 `?` 参数化，必须看白名单。
- 检查数据库类型分支、租户/配置开关、早返回、异常路径、权限前置和目标环境是否影响执行。
- 有 SQL 拼接但缺入口、缺可控性或缺执行条件时，输出为“待验证/不可确认”，不是确认漏洞。

### 6. 输出和自检

- 使用 `references/OUTPUT_TEMPLATE.md` 生成报告。
- 章节必须是：`1. 审计概述`、`2. 结论统计`、`3. SQL 操作映射`、`4. 候选风险与非漏洞依据`、`5. 风险详情`、`6. 审计结论`。技能路径校验、测试说明或限制必须放入这些章节表格内，不得新增 `## 0`、`## 7` 或其它编号章节。
- 遵守 `../java-shared/VULNERABILITY_GROUPING.md` 的聚合规则。
- 对没有确认漏洞的审计，也要输出已检查的 SQL 操作、非漏洞依据、待验证项和限制。
- 每个报告文件末尾必须包含 `## 输出自检`，终端总结不能替代文件内自检。

## Hard Rules

1. 没有真实 SQL/HQL/JPQL/native SQL sink，不得下 SQL 注入结论。
2. 没有用户可控数据流，不得下 SQL 注入结论。
3. 没有证据证明防护缺失或不足，不得下 SQL 注入结论。
4. `java-route-tracer` 的 `UNCONFIRMED`、`Manager.xxx()`、`DAO.xxx()`、接口方法名只表示待查，不是 SQL sink。
5. `PreparedStatement` 只有在 SQL 结构本身被用户输入拼接，或混用拼接导致用户可控 SQL 片段时才判风险；单纯 `?` 绑定值不是注入。
6. MyBatis `${}` 是高风险信号，但必须结合参数来源、上下文位置和白名单；常量、枚举或闭合集合选择不能直接判漏洞。
7. MyBatis `#{}`、Hibernate/JPA `setParameter`、JDBC `setXxx` 通常视为值绑定安全；若周围仍拼接标识符或 SQL 片段，需要单独分析该片段。
8. 白名单必须是闭合集合或等价的严格映射；仅做非空、长度、去引号、黑名单替换或宽松正则不是充分防护。
9. 不输出破坏性 payload、堆叠删除语句、命令执行 payload、时间延迟 payload 的可执行请求；验证建议必须低风险且标注“仅限授权环境”。
10. 不编造 CVE、CVSS、修复版本、数据库类型、表结构、返回包、漏洞利用成功或未读取过的文件内容。
11. 发现非 SQL sink 时只记录交接建议，不在本报告中扩写其他漏洞。
12. 结论状态必须使用中文枚举：确认漏洞、条件成立、待验证、不可确认、非漏洞；不要输出 `confirmed_vulnerable`、`not_vulnerable`、`unconfirmed` 等英文状态。
13. 反编译证据必须能指向真实存在的源码文件、反编译输出文件或 class/jar 来源；路径不存在、未实际读取或只有“应当存在”的推断时，不得作为确认漏洞证据。
14. Java `String.format` 只替换 `%s`、`%d` 等格式符，不替换 `{0}`；`{0}` 只有在 `MessageFormat.format` 或项目自定义 formatter 等真实调用下才表示替换。不能把 `String.format("prefix {0} suffix", value)` 当作用户值拼接证据。

## Gotchas

- `ORDER BY ${sort}` 最常见，但如果 Java 层把 `sort` 映射为固定列名，不能判漏洞。
- `LIKE '%${keyword}%'` 高风险，但如果 `keyword` 来源是服务端常量或不可控字典项，应标为非用户可控。
- `PreparedStatement pstmt = conn.prepareStatement("select x from t order by " + orderBy)` 仍可能有注入，因为拼接发生在 prepare 之前。
- `Integer.parseInt(request.getParameter("id"))` 后拼接到 SQL，通常不等价于字符串 SQL 注入；仍可建议参数化，但不要夸大。
- MyBatis `IN (${ids})` 只有当 `ids` 可由用户直接控制且无解析/白名单时才成立；如果已拆分为数字列表并用 `<foreach>#{id}</foreach>`，不是注入。
- `@Query(nativeQuery = true)` 不自动危险；看是否有参数绑定或 SpEL/字符串拼接。
- 数据库类型分支会改变结论：Oracle 分支有拼接而目标只运行 MySQL 时，最多写环境依赖或不可确认。
- 日志中的 SQL 字符串不等于执行 SQL；必须找到执行 API。
- 反编译代码可能丢失行号或泛型；报告应标注来源和可信度，不要捏造源码行号。
- “未反编译实现类，但同包其它方法使用 Hibernate Criteria”不是非漏洞证据；只能写“不可确认”或继续反编译实现。
- 报告全文禁止出现三个连续英文句点，包括代码片段、SQL 片段、路径、表格和自检。无法完整确认时删除该片段、改写为中文说明“省略非关键字段”，或只列出已确认的最小片段。

## 停止、确认或切换条件

- 找不到实现源码、Mapper XML 或可用反编译结果时：停止确认漏洞，输出“不可确认”和缺失证据。
- 需要先知道入口参数或调用链时：切换到 `java-route-tracer`，完成证据后再回来判定。
- 需要判断未授权、越权或角色限制时：交给 `java-auth-audit`，本 skill 只引用其结果。
- 用户要求组件 CVE、版本漏洞或修复版本时：交给 `java-vuln-scanner`。
- 用户要求实际攻击、批量扫描线上目标或破坏性验证时：拒绝该部分，只保留静态审计和授权验证建议。

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
| 失败案例 | 输出 CVSS、CVE、修复版本或破坏性 PoC | 不合格，违反安全边界 |
| 失败案例 | 把未反编译的 `UserManager` 按同包风格写成非漏洞 | 不合格，缺真实实现证据 |
| 失败案例 | 在报告中新增 `## 0. 已读取 Skill 文件` 或使用英文状态 | 不合格，未遵守模板 |
