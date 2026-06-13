# JDBC SQL 注入审计规则

在项目使用 `java.sql.*`、`DataSource`、`JdbcTemplate`、`NamedParameterJdbcTemplate` 或自定义 JDBC 封装时加载本文件。所有结论仍需满足 `SQL_DETECTION_RULES.md` 的入口、可控性、sink、防护四证据模型。

## 识别范围

| 类型 | 关注点 |
|------|--------|
| `Statement` | SQL 字符串是否包含用户可控拼接 |
| `PreparedStatement` | SQL 模板是否在 prepare 前已被拼接，值是否用 `setXxx` 绑定 |
| `CallableStatement` | 存储过程名、参数和 SQL 片段是否拼接 |
| `JdbcTemplate` | `query/update/execute` 的 SQL 参数是否拼接，是否使用参数数组 |
| `NamedParameterJdbcTemplate` | 命名参数是否覆盖用户值，SQL 标识符是否仍拼接 |
| 自定义 DAO/BaseDao | 包装方法内部是否执行拼接 SQL |

## 危险模式

### Statement 执行拼接 SQL

```java
String sql = "SELECT * FROM users WHERE name = '" + name + "'";
Statement stmt = conn.createStatement();
stmt.executeQuery(sql);
```

成立条件：

- `name` 来自用户或外部输入。
- 没有强类型转换、闭合集合白名单或其他能消除 SQL 语义的处理。
- 该方法可由入口调用到。

### PreparedStatement 之前已拼接

```java
String sql = "SELECT * FROM users ORDER BY " + orderBy;
PreparedStatement ps = conn.prepareStatement(sql);
```

`PreparedStatement` 只能保护绑定值，不能保护已经拼进 SQL 结构的表名、列名、排序方向或 SQL 片段。

### StringBuilder/StringBuffer 动态构造

```java
StringBuilder sql = new StringBuilder("SELECT * FROM user WHERE 1=1");
if (keyword != null) {
    sql.append(" AND name LIKE '%").append(keyword).append("%'");
}
stmt.executeQuery(sql.toString());
```

审计时要追踪每个 `.append()` 的来源和执行条件，不要只看最终 `executeQuery` 行。

### 格式化和 concat

```java
String sql = String.format("SELECT * FROM %s WHERE id = %s", table, id);
String sql2 = "DELETE FROM t WHERE id = ".concat(id);
```

`String.format`、`MessageFormat`、`concat` 与 `+` 拼接都可能等价，但必须先确认占位符语义：

- `String.format` 只替换 `%s`、`%d` 等 Java format specifier。
- `String.format("prefix {0} suffix", value)` 不会替换 `{0}`，不能据此判定用户值进入 SQL。
- `MessageFormat.format("prefix {0} suffix", value)` 会替换 `{0}`。
- 自定义 formatter 必须读取实现后再判定。

XML 或 Spring bean 中的 `{0}` 模板只有在定位到真实消费方和 formatter 后，才能从候选风险提升为“确认漏洞”或“条件成立”。

### JdbcTemplate 拼接

```java
jdbcTemplate.query("SELECT * FROM user WHERE name = '" + name + "'", mapper);
```

危险点在 SQL 字符串本身。`JdbcTemplate` 不是天然安全，只有使用占位符和参数数组/参数列表时才保护值。

## 安全模式

### 值绑定

```java
String sql = "SELECT * FROM users WHERE name = ?";
PreparedStatement ps = conn.prepareStatement(sql);
ps.setString(1, name);
```

或：

```java
jdbcTemplate.query(
    "SELECT * FROM users WHERE name = ?",
    new Object[] { name },
    mapper
);
```

安全前提：

- 用户值只进入 `?` 或命名参数。
- SQL 模板中的标识符和结构不是用户可控拼接。
- 绑定参数数量和位置能对应 SQL 占位符。

### 动态 IN 列表

安全做法通常是拆分、校验并生成对应数量的占位符：

```java
String placeholders = String.join(",", Collections.nCopies(ids.size(), "?"));
String sql = "SELECT * FROM users WHERE id IN (" + placeholders + ")";
```

仅生成占位符本身一般安全；仍要确认每个 `id` 是否使用 `setXxx` 绑定，且列表长度有合理限制。

### 动态标识符白名单

```java
Map<String, String> columns = Map.of("name", "user_name", "time", "created_at");
String column = columns.get(input);
if (column == null) {
    throw new IllegalArgumentException("invalid sort");
}
String sql = "SELECT * FROM users ORDER BY " + column;
```

表名、列名、排序方向、函数名不能用 `?` 绑定；必须是闭合集合映射。报告中要列出白名单来源。

## 检查步骤

1. 搜索 `createStatement`、`prepareStatement`、`executeQuery`、`executeUpdate`、`execute`、`JdbcTemplate`。
2. 对每个 SQL 字符串回溯构造过程，记录常量片段和变量片段。
3. 对变量片段追踪入口来源和中间处理。
4. 检查是否有 `setXxx`、参数数组、命名参数或闭合集合白名单。
5. 检查调用链、分支和环境条件。
6. 将每个执行点写入 SQL 操作映射表，安全点也要说明依据。

## 判定矩阵

| SQL 构造 | 参数来源 | 防护 | 结论 |
|----------|----------|------|------|
| `Statement` + 用户值拼接 | 外部可控 | 无 | 确认漏洞或条件成立 |
| `Statement` + 常量 SQL | 不可控 | 不适用 | 非漏洞 |
| `PreparedStatement` + `?` | 外部可控值 | `setXxx` 绑定 | 非漏洞 |
| `PreparedStatement` + 拼接标识符 | 外部可控 | 无白名单 | 确认漏洞/条件成立 |
| `PreparedStatement` + 拼接标识符 | 外部可控 | 闭合集合白名单 | 非漏洞或加固建议 |
| `JdbcTemplate` + SQL 拼接 | 外部可控 | 无 | 确认漏洞/条件成立 |
| `JdbcTemplate` + 占位符参数 | 外部可控值 | 参数数组/列表 | 非漏洞 |

## 输出证据要点

每个 JDBC 风险项至少包含：

- SQL 构造代码位置。
- 执行 API 代码位置。
- 用户参数来源和调用链。
- 拼接变量在 SQL 中的位置。
- 是否有 `setXxx`、参数数组或白名单。
- 分支/数据库/配置条件。
- 结论状态和限制说明。
