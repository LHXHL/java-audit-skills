# SQL 审计反编译策略

源码缺失、只有 `.class/.jar/.war` 或上游调用链停在接口/Manager/DAO 名称时加载本文件。目标是补足 SQL 实现证据，不是全量反编译项目。

通用反编译工具选择、CFR 获取方式和失败处理可参考 `../java-shared/DECOMPILE_STRATEGY.md`。本文件只描述 SQL 审计的目标选择和证据记录。

## 何时需要反编译

必须考虑反编译：

- `java-route-tracer` 只追踪到 `Manager`、`DAO`、`Repository`、`Mapper` 接口或 `UNCONFIRMED` sink。
- 源码中缺少实现类，但 `WEB-INF/classes`、`BOOT-INF/classes`、`target/classes`、`build/classes` 中存在字节码。
- SQL 构造逻辑在第三方业务 jar、内部公共 DAO jar 或部署包中。
- 需要确认 MyBatis Provider、Hibernate Repository、自定义 BaseDao 的真实实现。

不需要反编译：

- 源码、Mapper XML 或注解实现已经可读。
- 只缺少框架核心类，例如 Hibernate/MyBatis/JDBC 标准库。
- 当前任务只做路由枚举或调用链追踪，不做 SQL 判定。

## 目标优先级

| 优先级 | 目标 | 原因 |
|--------|------|------|
| P0 | 上游调用链直接命中的实现类 | 最可能决定当前结论 |
| P0 | Mapper XML 和 Provider 类 | MyBatis SQL 常在这里 |
| P1 | `*Dao*`、`*Repository*`、`*Mapper*`、`*ManagerImpl*` | 常见 SQL 执行层 |
| P1 | `BaseDao`、`AbstractDao`、`JdbcSupport`、`SqlBuilder` | 通用拼接和执行封装 |
| P2 | Service/Manager 实现 | 补足参数处理、白名单、默认值覆盖 |
| P2 | Entity/Model | 仅在 Hibernate/JPA 映射不清时读取 |

## 定位方法

先用轻量搜索定位候选，不要一上来全量反编译：

```bash
rg -n "class .*Dao|class .*Repository|class .*ManagerImpl|interface .*Mapper" .
find . -name "*Dao.class" -o -name "*Repository.class" -o -name "*Mapper.class" -o -name "*ManagerImpl.class"
find . -name "*Mapper.xml" -o -name "*Dao.xml"
```

从配置中定位类：

- Spring XML `<bean class="com.example.SomeClass">`
- MyBatis `<mapper resource="mapper/UserMapper.xml">`、`<package name="com.example.mapper">`
- Spring Boot `mapper-locations`
- JPA repository package 配置
- WebService/Servlet/Controller 调用链中的实际实现类

## 反编译范围控制

推荐顺序：

1. 只反编译当前入口调用链上的 1 到 3 个候选实现类。
2. 如果实现类调用公共 DAO/BaseDao，再补充反编译该公共类。
3. 如果 SQL 由 Provider/Builder 构造，再补充反编译 Provider/Builder。
4. 若仍找不到 SQL sink，记录“实现未确认”，不要扩大为确认漏洞。

避免：

- 无条件反编译整个依赖目录。
- 因类名包含 `Dao` 就批量输出漏洞。
- 在反编译失败时编造源码行号或 SQL 语句。

## 证据记录

报告中必须标注反编译来源：

| 项目 | 写法 |
|------|------|
| 来源文件 | `来源：反编译 WEB-INF/classes/com/acme/UserDao.class` |
| 行号 | 有行号写反编译文件行号；无行号写“反编译结果无可靠源码行号” |
| 可信度 | 说明是否存在混淆、反编译失败、注解缺失 |
| 限制 | 缺少依赖、接口未解析、多态实现不完整时明确标注 |

证据路径必须真实存在，或能明确指向已读取的 class/jar 来源。禁止写不存在的 `decompiled` 路径作为证据。若只看到 class 文件但未成功反编译，实现证据仍为缺失，结论应为“不可确认”。

## SQL 证据提取

反编译后优先提取：

- SQL 字符串常量和拼接位置。
- 执行 API：`executeQuery`、`executeUpdate`、`JdbcTemplate`、`createQuery`、`createNativeQuery`。
- MyBatis 注解：`@Select`、`@Update`、`@Insert`、`@Delete`、`@*Provider`。
- Provider/Builder 的参数来源和返回 SQL。
- 白名单、枚举、Map 映射、强类型转换。
- 数据库类型分支、早返回、异常路径。

## 失败处理

| 情况 | 处理 |
|------|------|
| 找不到 class/jar | 记录缺失实现，不下漏洞结论 |
| 反编译失败 | 记录“未取得可用反编译结果”和受影响类，结论降为不可确认；正式报告不展开工具授权、权限弹窗或运行环境细节 |
| 代码混淆 | 只引用可确认 SQL/API 片段，不推断业务含义 |
| 注解丢失 | 回查 Mapper XML、配置或运行时元数据；仍缺失则不可确认 |
| 多个实现类 | 分别列出已确认和未确认实现，不混成一个结论 |
| 只反编译到相邻类 | 不能按相邻类风格推断目标类安全，目标类仍为不可确认 |
| 反编译文件路径不存在 | 删除该证据或改为 class/jar 候选；不得作为确认漏洞依据 |

## 与 `UNCONFIRMED` 的关系

如果上游 `java-route-tracer` 把 sink 标为 `UNCONFIRMED`，本 skill 必须先完成以下任一项后才能判 SQL 注入：

- 找到源码实现并确认 SQL sink。
- 找到 Mapper XML/注解并确认 statement。
- 找到反编译实现并确认 SQL sink。

若三者都没有，输出“不可确认：缺少 SQL 实现证据”，不得写“疑似 SQL 注入已确认”。

正式报告中不要写 `CFR`、`javap`、`procyon` 等工具不可用、网络受限、命令受限或权限失败；这些属于测试过程。面向开发单位的写法应是“本轮未取得关键类可读实现/反编译方法体，无法确认参数来源和执行路径”。
