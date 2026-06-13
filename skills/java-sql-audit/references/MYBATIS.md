# MyBatis SQL 注入审计规则

在项目使用 MyBatis、MyBatis-Spring、Mapper XML、Mapper 注解或 `SqlProvider` 时加载本文件。`${}` 是高风险信号，但不是独立漏洞结论；必须结合参数来源、上下文位置和防护。

## 识别入口

| 位置 | 检查对象 |
|------|----------|
| Mapper XML | `*Mapper.xml`、`*Dao.xml`、`<select>/<insert>/<update>/<delete>` |
| Mapper 注解 | `@Select`、`@Update`、`@Insert`、`@Delete` |
| Provider | `@SelectProvider`、`@UpdateProvider`、`SqlProvider` 类 |
| 调用方 | Service/DAO 中传入 Mapper 的参数、DTO、Map |
| 配置 | `mybatis-config.xml`、Spring XML、`mapperLocations` |

## `#{}` 与 `${}`

| 语法 | 行为 | 默认判断 |
|------|------|----------|
| `#{param}` | 预编译值绑定，转换为 `?` | 值位置通常安全 |
| `${param}` | 字符串替换，直接进入 SQL 结构 | 高风险候选，需要继续判定 |

注意：

- `#{}` 只能保护值，不能用来绑定表名、列名或排序方向。
- `${}` 在固定枚举、闭合集合白名单、服务端常量场景下可能不是漏洞。
- `ORDER BY ${column}` 若 `column` 来自用户原始字符串且无白名单，通常成立。

## XML Mapper 检查

优先搜索：

```bash
rg -n "\\$\\{" --glob "*Mapper.xml" --glob "*Dao.xml" .
rg -n "order\\s+by|group\\s+by|like| in \\(|limit|offset" --glob "*Mapper.xml" --glob "*Dao.xml" .
```

对每个命中点记录：

- Mapper 文件路径、statement id、SQL 类型。
- `${}` 或动态片段所在 SQL 上下文。
- 参数名是否来自 `_parameter`、`param1`、`Map`、DTO 字段或 `@Param`。
- Java 调用方是否对参数做白名单、枚举或强类型转换。
- `<if>`、`<choose>`、`<foreach>`、`<bind>` 是否改变安全性。

## 注解 Mapper 检查

```java
@Select("SELECT * FROM users ORDER BY ${orderBy}")
List<User> list(@Param("orderBy") String orderBy);
```

检查重点：

- 注解 SQL 是否包含 `${}`、字符串拼接或 Provider。
- 参数是否有 `@Param` 映射，名称是否能对应 SQL 中的字段。
- 调用方是否限制为固定列名/方向。
- 注解字符串若由常量拼接，也要追踪常量来源。

## Provider 检查

`@SelectProvider` 等 Provider 的风险通常在 Java 代码里：

```java
public String build(Map<String, Object> p) {
    return "SELECT * FROM user ORDER BY " + p.get("sort");
}
```

Provider 审计按 JDBC 字符串构造规则处理：

- 追踪 Map/DTO 参数来源。
- 检查 `StringBuilder`、`SQL` builder、自定义拼接方法。
- 确认最终 SQL 是否被 Mapper 执行。
- 如果 Provider 只拼接固定常量或白名单映射，不能判漏洞。

## 常见风险点

| 场景 | 风险条件 | 安全条件 |
|------|----------|----------|
| `WHERE id = ${id}` | `id` 外部可控且未强类型化 | 使用 `#{id}` 或数值解析后绑定 |
| `LIKE '%${keyword}%'` | `keyword` 外部可控 | `CONCAT('%', #{keyword}, '%')` 或 `<bind>` + `#{}` |
| `ORDER BY ${column}` | `column` 外部可控且无白名单 | Java 层固定映射或 XML `<choose>` |
| `ORDER BY ${column} ${dir}` | 字段和方向外部可控 | 字段、方向分别白名单 |
| `IN (${ids})` | 原始字符串直接替换 | `<foreach>` + `#{id}` |
| `FROM ${table}` | 表名外部可控 | 闭合集合表名映射 |
| `SELECT ${columns}` | 列表达式外部可控 | 固定列集合映射 |

## `<foreach>` 与 IN

安全示例：

```xml
<foreach collection="ids" item="id" open="(" separator="," close=")">
  #{id}
</foreach>
```

风险示例：

```xml
IN (${ids})
```

判断时要确认：

- `ids` 是原始字符串还是已解析集合。
- 集合元素是否用 `#{}`。
- 集合长度是否受限；长度问题通常是资源风险，不自动等于 SQL 注入。

## `<bind>` 检查

`<bind>` 本身不决定安全：

```xml
<bind name="pattern" value="'%' + keyword + '%'" />
WHERE name LIKE #{pattern}
```

上述值绑定通常安全。若 `<bind>` 结果再进入 `${pattern}`，按字符串替换分析。

## 白名单要求

有效白名单可以在 Java 或 XML 层：

- Java `Map<String, String>` 将用户输入映射为固定列名。
- `enum` 或固定常量集合。
- XML `<choose>` 根据有限值选择固定 SQL 片段。

不足白名单：

- `column.matches("[a-zA-Z_]+")`，除非项目明确只允许这类字段且无函数/别名需求，通常只能算弱约束。
- 黑名单替换 SQL 关键字。
- 仅过滤引号、空格、分号。

## 非漏洞场景

- `${}` 的参数来自服务端常量，不经过外部输入。
- `${}` 只在配置初始化阶段使用，用户不可控。
- 调用方将用户值映射成固定列名，非法值直接拒绝或使用默认固定列。
- `#{}` 值绑定且没有其他拼接片段。
- Mapper XML 存在但无调用链或功能已废弃；可写为“不可达/待验证”，不写确认漏洞。

## 输出证据要点

每个 MyBatis 风险项至少包含：

- Mapper XML/注解/Provider 路径与 statement id。
- `${}` 或拼接片段所在 SQL 上下文。
- Java 调用方和参数来源。
- 是否存在 `@Param`、DTO 字段、Map key 映射。
- 白名单、枚举、`<choose>`、`<foreach>`、`#{}` 等防护证据。
- 结论状态和限制。
