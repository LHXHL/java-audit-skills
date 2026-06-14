---
name: java-deserialization-audit
description: 当用户要求审计 Java 源码、反编译源码、部署产物或 pipeline 结构化证据中的 DESERIALIZE sink、对象解码、类型元数据、多态对象构造、自动触发链或对象构造后危险原语可达性时使用；纯组件风险查询、XXE 或 SQL 注入审计不触发。
---

# Java Deserialization Audit

## 当前定位

`java-deserialization-audit` 是对象解码与反序列化专项判定层。它消费 route、trace、源码、反编译源码、组件线索和结构化 sink，回答：

- `REQUEST_PARAM` 是否到达真实 `OBJECT_DECODER`。
- 输入是否可控制类型、对象图、二进制对象、文本对象或多态字段。
- 解码后是否存在 `AUTO_TRIGGER_METHOD`、`GADGET_CONDITION` 或 `DANGEROUS_PRIMITIVE`。
- 白名单、过滤器、类型限制、签名、加密、固定类型或分支条件是否阻断。
- 结论应为：确认漏洞、条件成立、待验证、不可确认、非漏洞。

本 skill 不负责全量路由枚举、不替代调用链追踪、不判断 XXE 外部实体、不扫描组件 CVE。

## 触发条件

- 用户要求判断反序列化、对象解码、多态对象构造或 gadget 条件。
- 上游结构化证据包含 `sink_types: ["DESERIALIZE"]` 或 `dispatch_to` 包含本 skill。
- route tracer 已证明输入到达对象解码类 sink。
- 组件扫描只提供候选时，本 skill 可用于验证入口、sink 和链条条件。

以下情况不触发：

- 只查组件版本或 CVE。
- 只判断 XML 外部实体。
- 只追踪调用链但不做漏洞判定。
- 只有组件存在，没有入口、sink 或类型控制证据。

## 工作流

1. 读取 route、trace、sink、component 和 coverage 证据。
2. 缺少端到端数据流时先要求或执行 route tracer。
3. 读取 `references/DESERIALIZATION_SINKS.md` 和 `references/COMPONENT_PATTERNS.md`。
4. 源码缺失时按共享反编译策略补关键实现。
5. 判定输入控制、类型控制、自动触发、危险原语和过滤条件。
6. 需要授权复核材料时读取 `references/PAYLOAD_GUIDE.md`。
7. 使用 `references/OUTPUT_TEMPLATE.md` 输出报告。

## 成功标准

- 每个结论都有入口、参数、trace 证据、decoder、类型控制、防护和链条条件。
- 不把组件命中、类名、注解、配置或缺实现写成确认漏洞。
- 明确区分完整链条、缺入口、缺 sink、缺类型控制、缺危险原语、被过滤器阻断。
- 确认漏洞或条件成立项的复核材料必须限定授权环境、低破坏、可回滚。
- 报告不写内部规则、validator 结果或组件版本清单。

## Hard Rules

1. 没有真实 `OBJECT_DECODER`，不得下反序列化结论。
2. 没有用户可控对象数据或类型元数据，不得下确认漏洞。
3. 没有自动触发或危险原语证据，不得下远程代码执行类结论。
4. 组件存在只是候选，不是漏洞。
5. XML 外部实体风险交给 XXE 专项；本 skill 只判断对象构造和触发链。
6. 结论状态只能使用：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 按需读取

- sink 分类：`references/DESERIALIZATION_SINKS.md`
- 组件与链条条件：`references/COMPONENT_PATTERNS.md`
- 授权复核边界：`references/PAYLOAD_GUIDE.md`
- 输出模板：`references/OUTPUT_TEMPLATE.md`

## Evals

| 类型 | 场景 | 预期 |
|------|------|------|
| 正例 | trace 显示 `REQUEST_PARAM` 到达 `OBJECT_DECODER` | 判断类型控制、过滤和链条条件 |
| 正例 | 组件候选存在但入口未知 | 写待验证或要求 trace |
| 反例 | 只问 XML 外部实体 | 交给 XXE |
| 反例 | 只有组件版本 | 交给组件扫描或标候选 |
