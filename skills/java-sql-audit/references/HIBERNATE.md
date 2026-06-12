# Hibernate/JPA SQL 注入审计规则

在项目使用 Hibernate、JPA、Spring Data JPA、HQL、JPQL、native query、Criteria 或 `@Query` 时加载本文件。ORM 不天然免疫 SQL 注入，关键仍是查询字符串是否由用户输入拼接，以及是否使用参数绑定或类型安全 API。

## 识别范围

| 类型 | 关注点 |
|------|--------|
| HQL/JPQL | `Session.createQuery`、`EntityManager.createQuery` |
| Native SQL | `createNativeQuery`、`createSQLQuery` |
| Spring Data JPA | `@Query`、`nativeQuery = true`、SpEL |
| Criteria | `CriteriaBuilder`、Hibernate Criteria、`Restrictions.sqlRestriction` |
| Repository/DAO | 自定义查询构造方法 |

## HQL/JPQL 拼接

危险候选：

```java
String hql = "FROM User WHERE name = '" + name + "'";
return session.createQuery(hql).list();
```

安全候选：

```java
String hql = "FROM User WHERE name = :name";
return session.createQuery(hql).setParameter("name", name).list();
```

判定要点：

- 用户值是否直接进入 HQL/JPQL 字符串。
- 查询是否实际传入 `createQuery`。
- 是否使用 `setParameter` 或等价绑定。
- 拼接位置是值、标识符、排序字段还是完整表达式。
- HQL 中实体名/属性名拼接同样需要白名单。

## Native SQL

Native SQL 按 JDBC 字符串拼接规则审计：

```java
String sql = "SELECT * FROM users WHERE id = " + id;
em.createNativeQuery(sql).getResultList();
```

安全模式：

```java
Query q = em.createNativeQuery("SELECT * FROM users WHERE id = :id");
q.setParameter("id", id);
```

注意：

- `nativeQuery = true` 不自动危险；看是否参数绑定。
- 参数绑定不能保护动态表名、列名、排序方向。
- `createSQLQuery` 是旧 API，但风险判定相同。

## Spring Data `@Query`

安全候选：

```java
@Query("SELECT u FROM User u WHERE u.name = :name")
List<User> findByName(@Param("name") String name);
```

重点检查：

- `@Query` 字符串是否使用命名参数或位置参数。
- 是否存在 SpEL 表达式将用户输入拼成查询片段。
- `nativeQuery = true` 时是否仍使用参数绑定。
- 动态排序是否交给 `Sort`/`Pageable` 并由框架校验，还是拼入字符串。

风险候选：

```java
@Query("SELECT u FROM User u WHERE u.name = '#{#name}'")
```

不要只凭 `@Query` 存在就判漏洞。

## Criteria API

类型安全 Criteria 通常不构成 SQL 注入：

```java
CriteriaBuilder cb = em.getCriteriaBuilder();
cq.where(cb.equal(root.get("name"), name));
```

高风险 API：

```java
criteria.add(Restrictions.sqlRestriction("name = '" + name + "'"));
```

检查点：

- `Restrictions.sqlRestriction`、`Expression.sql`、原生 SQL 片段是否拼接用户输入。
- `root.get(sortField)` 这类动态属性名是否经过白名单。
- `Order.asc(sort)`、`Sort.by(sort)` 是否由固定字段映射生成。

## 排序和分页

ORM 场景下排序字段常绕开参数绑定：

```java
String hql = "FROM User ORDER BY " + sort;
```

合格防护：

- `sort` 映射为固定实体属性名。
- `Sort` 参数来自后端枚举或明确白名单。
- 非法字段直接拒绝或降级为固定默认字段。

不足防护：

- 只限制长度或去掉空格。
- 黑名单替换关键字。
- 允许点号、括号、逗号、函数调用等表达式字符。

## IN 和 LIKE

安全：

```java
query.setParameterList("ids", ids);
query.setParameter("keyword", "%" + keyword + "%");
```

风险：

```java
String hql = "FROM User WHERE id IN (" + ids + ")";
String hql = "FROM User WHERE name LIKE '%" + keyword + "%'";
```

仍需确认 `ids`/`keyword` 是否外部可控，以及是否已解析为强类型集合。

## 存储过程

风险候选：

```java
String sql = "CALL sp_get_user('" + username + "')";
em.createNativeQuery(sql).executeUpdate();
```

安全候选：

```java
StoredProcedureQuery q = em.createStoredProcedureQuery("sp_get_user");
q.registerStoredProcedureParameter("username", String.class, ParameterMode.IN);
q.setParameter("username", username);
```

存储过程名动态拼接也需要白名单。

## 非漏洞场景

- HQL/JPQL 使用参数绑定，且没有其他动态片段。
- CriteriaBuilder 类型安全构造值条件。
- 动态字段来自固定 enum/Map 映射。
- `@Query` 使用 `:param` 或 `?1`，调用方没有拼接查询字符串。
- 只有 Repository 方法名派生查询，例如 `findByName`，没有自定义 SQL/HQL 拼接。

## 输出证据要点

每个 Hibernate/JPA 风险项至少包含：

- 查询构造位置和执行 API 位置。
- 查询类型：HQL、JPQL、native SQL、Criteria、`@Query`。
- 用户参数来源和传递链。
- 是否有 `setParameter`、`setParameterList` 或类型安全 API。
- 动态标识符是否有白名单。
- `nativeQuery`、数据库方言、分支和环境条件。
- 结论状态和限制。
