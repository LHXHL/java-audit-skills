# SQL 注入通用检测规则

本文件用于 `java-sql-audit` 已触发后加载，提供跨 JDBC、MyBatis、Hibernate/JPA 的通用判定方法。它不是漏洞知识教程；结论必须回到项目中的真实代码证据。

## 结论证据模型

每个 SQL 注入结论至少需要四类证据：

| 证据 | 必须回答的问题 | 不足时的结论 |
|------|----------------|--------------|
| 入口 | 参数从哪个路由、RPC、任务、消息或测试入口进入 | 只能做 sink 盘点或待验证 |
| 可控性 | 参数是否由用户或外部输入控制，是否被覆盖、转换、枚举化 | 不可确认或非漏洞 |
| SQL sink | 参数到达哪个真实 SQL/HQL/JPQL/native SQL 执行点 | 不得下 SQL 注入结论 |
| 防护缺口 | 是否缺少参数绑定、闭合集合白名单或强类型约束 | 不得下漏洞结论 |

推荐状态：

| 状态 | 使用条件 |
|------|----------|
| 确认漏洞 | 四类证据完整，防护缺失，执行路径成立 |
| 条件成立 | 四类证据基本完整，但依赖特定数据库、配置、角色或分支 |
| 待验证 | 有 SQL 拼接和可能可控输入，但缺入口、环境或分支证据 |
| 不可确认 | 只有命名、候选调用、缺失实现或无法读取的字节码 |
| 非漏洞 | 参数不可控、被白名单/枚举/参数绑定保护，或路径不可达 |

状态必须用中文输出。不要把内部判断写成 `confirmed_vulnerable`、`not_vulnerable`、`unconfirmed`。

一条映射行只能有一个状态。若同一 SQL 模板既包含已确认安全的命名参数，也包含来源未确认的动态条件片段，按动态片段的风险状态记录为“待验证”或“不可确认”，并在依据中说明命名参数部分安全；不要写“非漏洞；片段待补证”。

## 行为优先

不要只依赖类名、方法名或字段名。优先识别真实 SQL 行为：

- SQL 字符串构建：`SELECT`、`UPDATE`、`DELETE`、`INSERT`、`WHERE`、`ORDER BY`、`GROUP BY`、`LIMIT`、`IN`。
- 执行 API：`executeQuery`、`executeUpdate`、`execute`、`query`、`update`、`createQuery`、`createNativeQuery`。
- Mapper 绑定：`${}`、`#{}`、`@Select`、`@Update`、`@Insert`、`@Delete`、`@*Provider`。
- 动态片段：表名、列名、排序字段、排序方向、函数名、SQL 片段。

可用搜索方向：

```bash
rg -n "order\\s+by|group\\s+by|limit\\s|offset\\s|rownum|row_number" .
rg -n "executeQuery|executeUpdate|prepareStatement|createStatement|JdbcTemplate|NamedParameterJdbcTemplate" .
rg -n "createQuery|createNativeQuery|createSQLQuery|@Query|sqlRestriction" .
rg -n "\\$\\{|#\\{|@Select|@Update|@Insert|@Delete|Provider" .
```

搜索命中只是候选，不是漏洞结论。

`SQL 操作映射` 只记录真实 SQL sink 或候选 SQL sink。过滤器启用状态、框架版本、Spring import、数据源配置、数据库方言配置等上下文信息可以放在审计概述、候选依据或审计结论中，但不要作为 SQL 操作映射行，也不要计入非漏洞数量。

正式报告只描述代码证据和证据缺口。反编译不足应写“本轮仅取得字节码检查证据，未取得源码级反编译结果”或“本轮未取得关键类可读实现/反编译方法体”，不要写网络受限、命令受限、工具下载失败、权限弹窗、模型规则编号或测试运行过程。

class-heavy 项目不能因为只有 `.class` 就停止。若 `.class` 明显多于 `.java`，且已经发现 SQL 模板、DAO、Manager、Repository、Mapper 或 JdbcSupport 候选，应先做有界候选 class 检查，再决定是否输出不可确认。候选 class 检查至少回答：

- 哪些 class 与 SQL 模板或入口调用链直接相关。
- 字节码或反编译结果中是否出现 SQL 执行 API、字符串拼接、formatter、参数绑定或白名单。
- 仍缺少哪些证据才不能确认漏洞，例如入口参数到 SQL 字符串的完整数据流。

## 高风险 SQL 位置

| 位置 | 风险原因 | 合格防护 |
|------|----------|----------|
| WHERE 值 | 用户值拼接可改变条件 | 参数绑定或强类型转换 |
| LIKE 值 | 拼接引号和通配符易突破语义 | 参数绑定，将 `%` 放入绑定值 |
| IN 列表 | 原始字符串可注入额外表达式 | 拆分校验后逐项绑定 |
| ORDER BY/GROUP BY | 标识符无法用 `?` 绑定 | 闭合集合白名单或固定映射 |
| 表名/列名 | 标识符无法参数化 | 闭合集合白名单 |
| LIMIT/OFFSET | 字符串拼接仍可能改变语句 | 数值解析或绑定支持 |
| native SQL/HQL 片段 | 直接进入执行器 | 参数绑定或严格映射 |

## 可控性判定

按以下顺序确认参数是否可控：

1. 参数来源：HTTP query/form/body、JSON 字段、path variable、header、cookie、RPC 参数、MQ 消息、上传文件元数据。
2. 对象流转：DTO/VO/Bean 字段、Map key、数组/集合元素、分页对象、搜索对象。
3. 中间处理：默认值覆盖、枚举映射、字典转换、`parseInt`/`parseLong`、正则校验、白名单过滤。
4. 传递链：Controller/Action/Servlet/WebService -> Service -> DAO/Mapper/Repository -> SQL sink。
5. 分支条件：角色、配置、数据库类型、租户、功能开关、空值判断、异常处理。

如果跨层证据不足，交给 `java-route-tracer` 追踪。不要凭 `save`、`query`、`getList` 等方法名推断数据流。

公共 DAO、BaseDao、JdbcSupport、SqlBuilder 中的危险 sink 只能证明“底层执行器有风险形态”，不能单独证明某个 Web/RPC 入口可利用。确认漏洞至少要有一个具体入口到 sink 的端到端链路；若只看到入口把参数传给 Manager、另一个底层类存在拼接 sink，但缺少 Manager/DAO 中间层，状态应为“待验证”，不得输出 Burp Suite 请求或 payload。

## 防护判定

有效防护：

- JDBC `PreparedStatement` 使用 `?` 并通过 `setXxx` 绑定用户值。
- MyBatis `#{}` 用于值位置。
- Hibernate/JPA 使用命名参数或位置参数并调用 `setParameter`。
- 标识符位置使用固定枚举、Map 映射或闭合集合白名单。
- 字符串输入先转换为数值、布尔、枚举，失败路径中断执行。

不足防护：

- 只做非空、长度、trim、去引号、替换空格。
- 黑名单过滤关键字、过滤 `'`、过滤 `--`。
- 宽松正则允许点号、括号、逗号、空格、函数、运算符等 SQL 语义字符。
- `PreparedStatement` 前已经把用户值拼进 SQL 结构。
- MyBatis `${}` 直接接收外部字符串。
- `StringEscapeUtils`、HTML escape、URL decode/encode 等非 SQL 参数化措施。

## 执行条件

发现 SQL 拼接后必须继续看是否会执行：

- 数据库分支：`isOracle()`、`isMySQL()`、`dbType`、方言类、配置文件。
- 早返回和异常：`return`、`throw`、空值短路、默认值覆盖。
- 角色和功能开关：管理员入口、内网入口、租户配置、禁用功能。
- 调用链可达性：候选方法是否被入口真实调用，是否只是测试/废弃代码。
- 多态和接口：接口方法必须定位实现类；无法定位时标为不可确认。

`非漏洞` 需要积极证据，例如已读取实现并确认参数绑定、白名单、不可控或路径不可达。不能因为“未看到拼接”“同包代码风格通常使用 ORM”“框架名像 Hibernate”就写非漏洞。

## 字符串格式化边界

不同 formatter 的占位符语义不同，必须看真实调用：

| 调用 | 占位符 | 判定 |
|------|--------|------|
| `String.format("prefix %s suffix", value)` | `%s`/`%d` 等 | 会替换，按拼接分析 |
| `String.format("prefix {0} suffix", value)` | `{0}` | Java 标准 `String.format` 不替换 `{0}`；不能据此判用户值进入 SQL |
| `MessageFormat.format("prefix {0} suffix", value)` | `{0}` | 会替换，按拼接分析 |
| 项目自定义 `StringUtils.format`、`SqlUtil.format` | 依实现而定 | 必须读取实现，不能按名称猜测 |

SQL/XML 模板中的 `{0}`、`{1}` 只是候选。必须定位消费方和 formatter，确认参数来源后才能提升状态。

Spring XML SQL 模板的高价值检查顺序：

1. 提取模板 bean id 和占位符位置。
2. 搜索源码、反编译结果、字节码常量池中对 bean id 的引用。
3. 定位 `MessageFormat.format`、`String.format`、自定义 formatter、`getBean(beanId)`、字段注入或 setter 注入。
4. 确认 formatter 入参数组中的值来自用户输入、会话服务端值、枚举常量还是配置常量。
5. 确认格式化后的 SQL 是否直接进入 `createSQLQuery`、`JdbcTemplate`、`Statement`、`BaseDao.getListBySql` 或同类执行 API。

若第 2 至第 5 步未完成，不要把模板本身写成确认漏洞；若完成且无绑定/白名单/强类型保护，应输出可复核 payload。

## 常见误判

- 将 `Manager.save(bean)` 写成 SQL sink，但没有实现源码或 Mapper XML。
- 将所有 `${}` 都写成漏洞，忽略 Java 层固定映射。
- 将 `PreparedStatement` 值绑定写成 SQL 注入。
- 将日志输出的 SQL 字符串当作执行 SQL。
- 忽略数据库类型分支，把只在未部署分支执行的拼接写成确认漏洞。
- 把数值解析后的参数按字符串注入处理。
- 没有入口和可控性证据，仅凭 DAO 方法拼接常量输出漏洞。
- 未定位实现类，却按“同包风格”把下游 DAO/Manager 写成非漏洞。
- 只确认底层公共 `JdbcSupport.addOrderBy` 或 `BaseDao.getListBySql` 存在拼接，却没有证明具体入口参数到达该方法，就写成确认漏洞。
- 把 `String.format("prefix {0} suffix", value)` 当成 Java 会替换 `{0}` 的证据。
- 引用不存在的反编译路径或未实际读取的文件作为确认漏洞证据。
- 在报告中用三个连续英文句点省略代码、SQL、路径或关键证据；这会掩盖证据是否真实完整。
- 在 Java varargs 签名中写 `Object...`；报告中应改写为 `Object[]/varargs` 或只写方法名，避免出现三个连续英文点号。
- 用 `20+`、`60+`、范围数量或尾随加号描述入口数、方法数、行数或覆盖率；无法精确统计时写“未精确统计”。
- 将 `SQLCheckFilter` 未启用、框架版本或配置导入关系写成 `SQL 操作映射` 的非漏洞行，导致统计数量和映射状态不一致。
- 同一映射行同时写“非漏洞”和“待补证”，或表格序号跳号。
- 在 SQL 报告中展开组件版本、CVE 扫描对象或 CVSS 事项；这些属于组件扫描边界。

## 验证输出边界

确认漏洞和条件成立项必须给开发单位可复核材料；待验证、不可确认和非漏洞项不能包装成可复制攻击请求。

允许输出 Burp Suite 请求和 payload 的前提：

- 结论状态是“确认漏洞”或“条件成立”。
- 已确认真实入口、HTTP 方法、参数名、Content-Type 和调用链。
- 已确认用户输入到达 SQL sink，且防护缺口成立或在特定条件下成立。
- payload 是低风险探测，只用于授权测试环境。

禁止输出 Burp Suite 请求和 payload 的场景：

- 只有 SQL 拼接候选，但缺入口或缺可控性。
- 只有 Mapper XML、DAO 方法名、`UNCONFIRMED` sink 或未定位实现。
- 结论状态是待验证、不可确认或非漏洞。
- 需要猜测路由、参数名、Content-Type、鉴权态或数据库类型。

允许的低风险 payload 类别：

- 值位置：单引号、成对引号、非法字符、布尔条件差异探测等不会修改数据的最小 payload。
- 数值位置：基线数值和只读布尔条件差异探测；已强类型解析时不要给字符串注入 payload。
- 标识符位置：非法列名、非法排序方向、白名单外固定字符串，用于观察是否被拒绝。
- `LIKE` 场景：不会抽取数据的特殊字符探测，优先配合 SQL 日志或断点观察最终 SQL 结构。
- 结构控制探针：必要时可以使用 `OR 1=1`、WHERE 改写、注释符或受控堆叠语句证明 SQL 结构可控；涉及写操作时必须限定授权测试环境、最小样本、备份或事务回滚。
- 短时间延迟探针：仅在普通错误/布尔差异不足以确认，且目标为授权测试环境时使用；延迟值应短且单请求验证，避免造成服务压力。
- 最小回显/元数据探针：仅用于确认注入点能影响查询结构；优先使用常量回显或数据库元数据函数，不读取业务表、不枚举大量系统表、不输出真实敏感数据。

禁止的 payload 类别：

- 缺少授权测试环境、最小样本、备份或事务回滚说明的 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`TRUNCATE` 等会修改结构或数据的语句。
- 命令执行、文件读写、外带、DNS/OOB、批量枚举、业务数据批量抽取。
- 长时间延迟、并发延迟、循环延迟或任何可能造成服务压力的探测。
- 伪造 Burp 响应包、数据库错误或验证成功结果。

具体 Burp 请求和 payload 格式见 `VALIDATION_GUIDE.md`。报告中必须把验证说明限定为“仅限授权测试环境”，并写清预期观察是受控错误、结果差异、短延迟差异、最小回显差异、SQL 日志结构变化或白名单拒绝情况。
