---
name: java-xxe-audit
description: 当用户要求审计 Java 源码、反编译源码、部署产物或 pipeline 结构化证据中的 XML 外部实体、XML 解析安全配置、XML 输入可控性、XML 转换/校验/对象绑定 sink 时使用；只做路由、调用链、SQL、文件、反序列化、鉴权或组件风险扫描时不要使用。
---

# Java XXE Audit

## 当前定位

`java-xxe-audit` 是 XML 外部实体与 XML 解析安全的专项判定层。它消费 route、trace、源码、反编译源码和结构化 sink 证据，回答：

- `REQUEST_PARAM` 是否作为 XML 输入到达真实 `XML_PARSER`。
- `XML_PARSER` 是否允许外部实体、外部资源、外部 schema、外部样式或等价资源加载。
- 安全配置是否在实际 parser 实例、实际调用前生效。
- 结论应为：确认漏洞、条件成立、待验证、不可确认、非漏洞。

本 skill 不负责全量路由枚举、不替代调用链追踪、不判断鉴权漏洞、不扫描依赖 CVE。

## 触发条件

- 用户要求判断 XXE、外部实体、XML 解析安全配置或 XML 输入风险。
- 上游结构化证据包含 `sink_types: ["XML"]` 或 `dispatch_to` 包含本 skill。
- route tracer 已证明用户输入到达 XML category sink。
- 用户给出 XML 处理代码，要求判断外部资源解析风险。

以下情况不触发：

- 只列服务 operation 或路由。
- 只追踪参数但不判断 XML 解析风险。
- 只看到 XML 文件、服务描述或配置，没有 `XML_PARSER` 证据。
- 只判断对象反序列化 gadget 或组件版本。

## 工作流

1. 读取 route、trace、sink 和 coverage 证据。
2. 若缺少输入到 parser 的数据流，先要求或执行 route tracer。
3. 读取 `references/PARSERS.md`，按能力类别判断 parser。
4. 源码缺失时读取 `references/DECOMPILE_STRATEGY.md`。
5. 确认 `XML_PAYLOAD` 来源、parser 实例、外部资源配置和输出条件。
6. 需要授权复核材料时读取 `references/VALIDATION_GUIDE.md`。
7. 使用 `references/OUTPUT_TEMPLATE.md` 输出 6 个编号章节。

## 成功标准

- 每个结论都有入口、XML 输入、trace 证据、parser 位置、防护状态和代码位置。
- 不把 XML 字符串、服务根、配置文件、类名或未读实现写成 XXE。
- 对 parser 创建、配置、解析调用和输出条件给出证据。
- 待验证、不可确认和非漏洞项不得输出可复制攻击请求。
- 报告不写组件版本、CVE、内部规则或 validator 结果。

## Hard Rules

1. 没有真实 `XML_PARSER` 或 `XML_OBJECT_DECODER` 证据，不得下 XXE 结论。
2. 没有用户可控 XML 输入，不得下 XXE 结论。
3. 没有防护缺失或不足证据，不得下确认漏洞。
4. 对象构造、类型白名单和 gadget 风险交给反序列化专项；本 skill 只判断 XML 外部资源解析维度。
5. 结论状态只能使用：确认漏洞、条件成立、待验证、不可确认、非漏洞。
6. 授权复核 payload 不得包含真实敏感文件、内网探测、外带或拒绝服务内容。

## 按需读取

- parser 能力与防护：`references/PARSERS.md`
- 反编译策略：`references/DECOMPILE_STRATEGY.md`
- 授权复核边界：`references/VALIDATION_GUIDE.md`
- 输出模板：`references/OUTPUT_TEMPLATE.md`

## Evals

| 类型 | 场景 | 预期 |
|------|------|------|
| 正例 | trace 证据显示 XML 输入到达 `XML_PARSER` | 判断外部资源防护和结论 |
| 正例 | parser 配置缺失但入口需特定条件 | 标为条件成立或待验证 |
| 反例 | 只有服务根没有业务 parser | 不下 XXE 结论 |
| 反例 | 只问对象 gadget 条件 | 交给反序列化专项 |
