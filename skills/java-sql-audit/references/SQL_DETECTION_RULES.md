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

## 常见误判

- 将 `Manager.save(bean)` 写成 SQL sink，但没有实现源码或 Mapper XML。
- 将所有 `${}` 都写成漏洞，忽略 Java 层固定映射。
- 将 `PreparedStatement` 值绑定写成 SQL 注入。
- 将日志输出的 SQL 字符串当作执行 SQL。
- 忽略数据库类型分支，把只在未部署分支执行的拼接写成确认漏洞。
- 把数值解析后的参数按字符串注入处理。
- 没有入口和可控性证据，仅凭 DAO 方法拼接常量输出漏洞。
- 未定位实现类，却按“同包风格”把下游 DAO/Manager 写成非漏洞。
- 把 `String.format("prefix {0} suffix", value)` 当成 Java 会替换 `{0}` 的证据。
- 引用不存在的反编译路径或未实际读取的文件作为确认漏洞证据。
- 在报告中用三个连续英文句点省略代码、SQL、路径或自检内容；这会掩盖证据是否真实完整。

## 低风险验证建议

报告可以给“授权环境验证思路”，但不要给破坏性 payload 或声称验证成功。

允许：

- 建议在授权测试环境对候选参数发送单引号、异常字符或排序字段非法值，观察是否进入受控错误处理。
- 建议打开 SQL 日志或断点，确认最终 SQL 结构是否被用户输入改变。
- 建议用安全样例值验证白名单是否拒绝非法列名。

禁止：

- 输出删除、写文件、命令执行、堆叠查询、时间延迟、数据外带 payload。
- 伪造 Burp 请求、响应包或数据库错误。
- 在未确认真实入口时给可复制攻击请求。
