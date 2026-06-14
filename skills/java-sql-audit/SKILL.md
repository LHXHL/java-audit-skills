---
name: java-sql-audit
description: 当用户要求审计 Java 源码、反编译源码、部署产物或 pipeline 结构化证据中的 SQL 注入、动态查询构造、查询片段拼接、动态标识符、动态排序或 SQL sink 可控性时使用；只做路由、调用链、鉴权、XML、文件、反序列化或组件风险扫描时不要使用。
---

# Java SQL Audit

## 当前定位

`java-sql-audit` 是 SQL 类 sink 的专项判定层。它消费源码、反编译源码、`route_mapper`、`route_tracer`、`structured/sink_candidates.jsonl` 或 `structured/trace_sinks.jsonl`，回答：

- `REQUEST_PARAM` 是否到达真实 `SQL_EXECUTOR`。
- 到达位置是值、标识符、排序字段、查询片段还是完整查询。
- 参数是否被绑定、映射、白名单、类型转换、默认值或分支阻断保护。
- 结论应为：确认漏洞、条件成立、待验证、不可确认、非漏洞。

本 skill 不负责枚举入口、不替代调用链追踪、不判断鉴权漏洞、不扫描依赖风险。

## 触发条件

满足任一条件时触发：

- 用户明确要求判断 SQL 注入或动态查询风险。
- 上游结构化证据包含 `sink_types: ["SQL"]` 或 `dispatch_to` 包含本 skill。
- route tracer 已证明参数到达 `SQL` category sink。
- 用户给出查询构造代码并要求判断外部输入影响。

以下情况不触发：

- 只要求找路由或追踪调用链。
- 只看到命名类似数据访问的方法，但没有 `SQL_EXECUTOR` 证据。
- 只做组件、鉴权、文件、XML 或反序列化审计。

## 工作流

1. 读取上游 route、trace、sink 和 coverage 证据。
2. 若缺少端到端数据流，先要求或执行 route tracer；不要凭方法名判断。
3. 读取 `references/SQL_DETECTION_RULES.md`。
4. 源码缺失时读取 `references/DECOMPILE_STRATEGY.md`，只补直接相关实现。
5. 判定 `REQUEST_PARAM` 到达 `SQL_EXECUTOR` 的位置类型。
6. 检查 `VALUE_BINDING`、闭合集合映射、类型转换、默认值覆盖和 `GUARD_CONDITION`。
7. 需要授权复核材料时读取 `references/VALIDATION_GUIDE.md`。
8. 使用 `references/OUTPUT_TEMPLATE.md` 输出 6 个编号章节。

## 成功标准

- 每个结论都有入口、参数、trace 证据、SQL sink、参数位置、防护和代码位置。
- `UNCONFIRMED`、缺实现、缺入口或只命中候选时不得写确认漏洞。
- 动态标识符、排序字段和查询片段必须检查闭合集合映射；值绑定不能保护已经拼入查询结构的部分。
- 结论统计与映射表状态数量一致。
- 确认漏洞或条件成立项可以给授权测试环境的低风险复核请求；待验证、不可确认和非漏洞项不得输出可复制攻击请求。
- 报告不写内部规则、模型自检、工具失败细节、组件版本或 CVE。

## Hard Rules

1. 没有真实 `SQL_EXECUTOR` 证据，不得下 SQL 注入结论。
2. 没有用户可控数据流，不得下 SQL 注入结论。
3. 没有防护缺失或不足证据，不得下确认漏洞。
4. 值绑定通常只保护值位置；结构位置必须独立判断。
5. 白名单必须是闭合集合或等价严格映射；宽松过滤不是充分防护。
6. 结论状态只能使用：确认漏洞、条件成立、待验证、不可确认、非漏洞。
7. 正式报告不得包含通用 skill 的占位例子、测试过程或 validator 结果。

## 按需读取

- SQL 判定规则：`references/SQL_DETECTION_RULES.md`
- 反编译策略：`references/DECOMPILE_STRATEGY.md`
- 授权复核材料边界：`references/VALIDATION_GUIDE.md`
- 输出模板：`references/OUTPUT_TEMPLATE.md`

## Evals

| 类型 | 场景 | 预期 |
|------|------|------|
| 正例 | trace 证据显示 `REQUEST_PARAM` 到达 `DYNAMIC_ORDER_FIELD` | 判断结构位置、防护和结论 |
| 正例 | 代码片段显示 `QUERY_FRAGMENT` 由外部输入组成 | 追证据并按状态输出 |
| 反例 | 只有数据访问方法命名，没有实现 | 写不可确认或要求 trace，不下结论 |
| 反例 | 参数只进入绑定值且无结构拼接 | 记录非漏洞依据 |
