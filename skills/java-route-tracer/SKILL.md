---
name: java-route-tracer
description: 当用户要求从已知 Java Web/RPC 路由、入口方法、structured trace 任务或 pipeline 批次追踪请求参数到 SQL/FILE/XML/COMMAND/HTTP/LDAP/EXPRESSION/DESERIALIZE/RESPONSE 等 sink，并输出调用链证据、可控性、分支条件和结构化 trace 结果时使用；只提取路由、判断具体漏洞、鉴权审计或依赖风险扫描时不要使用。
---

# Java Route Tracer

## 当前定位

`java-route-tracer` 是 Java 审计技能集的调用链证据层。它从已知入口出发，回答：

- 请求从哪个 route/operation/sub-function 进入。
- `REQUEST_PARAM` 在入口、业务层、数据层、工具层和配置映射之间如何传递、改名、转换或覆盖。
- 参数是否到达 `SINK_CATEGORY`。
- 到达前有哪些分支、默认值、白名单、规范化、异常路径或阻断条件。
- 证据是否足够交给专项漏洞 skill 判断。

本 skill 不直接下漏洞结论。它输出 Markdown 报告和 `structured/trace_sinks.jsonl`，供专项 skill 复核。

## 触发条件

用户意图包含以下任一项时触发：

- 追踪某个入口参数到 SQL/FILE/XML/COMMAND/HTTP/LDAP/EXPRESSION/DESERIALIZE/RESPONSE 等 sink。
- 基于 route mapper 输出继续分析一条或一批入口的参数流向。
- 基于 `structured/trace_tasks.jsonl` 或 `structured/candidate_packages.jsonl` 处理高价值候选。
- 为专项漏洞审计准备可复用调用链证据。
- pipeline 中 `agent-5-N` 被分配批次调用链追踪任务。

必须存在明确边界：具体 route、operation、入口方法、trace task、candidate package、用户点名参数/sink，或有限批次。只给项目路径并要求“全项目所有调用链”时，不要自行展开；先要求 route mapper 或批次输入。

## 成功标准

合格输出必须让下游审计员可以不重新猜入口，直接回答“哪个参数、经过哪条链、到达哪个 sink、受什么条件限制”。

最低要求：

- 每条被分配入口都有追踪结果或 blocked 原因。
- 入口定位来自结构化路由、配置、注解、服务描述、反编译证据或用户指定方法。
- 批量任务、高风险候选和重复调用链模式必须使用项目专用 trace helper；不得只把大量源码投喂给 AI 写文档。
- trace helper 产出调用边、方法实现候选、参数传递、配置映射、接口实现和 sink 候选。
- `structured/trace_sinks.jsonl` 引用 trace helper 或人工追踪证据来源。
- sink 类型、位置、参数到达关系、可控性、分支条件清楚。
- 未看到真实 sink 代码时不得推断为具体 sink，只能写 `UNCONFIRMED` 或 blocked。
- 不把“参数到达 sink”写成“漏洞已确认”；漏洞结论交给专项 skill。
- pipeline 输入中的鉴权状态只透传，不自行鉴权。

## 输入与模式判断

| 模式 | 触发条件 | 输出责任 |
|------|----------|----------|
| Standalone single-route | 用户指定一个入口或 operation | 允许人工追踪，必要时写轻量 helper |
| Standalone batch | 用户给出多个入口或路由清单 | 必须脚本辅助，生成批次索引 |
| Pipeline worker | prompt 中出现 `agent-5-N`、batch id 或输出目录 | 只处理本批次，写 worker 专属结果 |
| Structured candidate | 输入包含 trace task 或 candidate package | 只处理结构化任务，追加 `trace_sinks.jsonl` |
| Evidence refresh | 用户要求复查旧报告 | 读取旧证据和源码，更新对应入口 |

缺少源码路径、输出目录或入口定位信息，且无法从当前仓库或上游结构化文件推导时，停止要求补齐。

## 脚本化追踪工作流

1. 确认模式、源码路径、输出路径、入口清单和上游结构化文件。
2. 读取 `structured/trace_tasks.jsonl`、`structured/candidate_packages.jsonl` 或 `structured/routes.jsonl`。
3. 判定是否需要 trace helper：
   - 单入口、小范围、调用层级少：可人工追踪。
   - 批量入口、高风险候选、重复模式、配置映射、接口实现复杂：必须编写 helper。
4. 在允许目录中创建项目专用 trace helper。
5. helper 收集：
   - 入口方法候选。
   - 调用边和被调用方法位置。
   - 参数名、字段名、变量改名、赋值和覆盖。
   - 配置映射、接口实现、动态分发候选。
   - sink 候选及类别。
6. AI 基于 helper 输出做语义判断，补充分支条件、可控性和证据解释。
7. 将结果写入 Markdown 和 `structured/trace_sinks.jsonl`。
8. 对未追踪、未定位、源码不可读、实现缺失、sink 未确认项写入 coverage blocked。
9. 运行适用 validator；失败时修正 helper 或报告，不交付半成品。

## trace helper 目录约定

Standalone 模式：

- 写入 `{output_path}/scripts/trace_helpers/`。

Pipeline worker 模式：

- `agent-5-N` 只写 `{output_path}/scripts/trace_helpers/agent-5-{N}/`。
- 不修改 route mapper、auth audit、vuln report、专项漏洞报告或其他 worker 目录。
- helper 输出可放在 worker 输出目录或 `structured/` 中，但必须可被报告引用。

trace helper 可以自由选择实现方式，但必须输出机器可读证据，不能只打印自然语言。

## 按需读取的 references

- 多入口和多方法展开：`references/multi-method-tracing.md`
- 参数可控性和 sink 分类：`references/CONTROLLABILITY_ANALYSIS.md`
- 分支和提前退出：`references/BRANCH_TRACING.md`
- 报告模板：`references/OUTPUT_TEMPLATE_FULL.md`、`references/OUTPUT_TEMPLATE_SIMPLE.md`、`references/OUTPUT_TEMPLATE_INDEX.md`
- 结构化证据 schema：`../java-audit-pipeline/references/STRUCTURED_EVIDENCE_FLOW.md`
- 需要反编译：`../java-shared/DECOMPILE_STRATEGY.md`

## 强制规则

### 1. 只给证据，不替专项 skill 下结论

允许写：

- `REQUEST_PARAM` 到达 `SINK_CATEGORY`。
- 参数在某个分支下可控。
- 某个 guard 限制了参数范围。

禁止写：

- 漏洞已确认。
- 可直接利用。
- 无需专项复核。
- 未经专项 skill 支持的复现材料或修复结论。

### 2. 入口必须真实可达

每条调用链都必须绑定真实入口：

- 注解路由入口。
- XML/配置路由入口。
- 运行容器/过滤器入口。
- 服务端点 + operation。
- 自定义 dispatcher 的 sub-function。

找不到入口时写“入口未定位”或 blocked，不把内部 helper 方法伪装成 Web 路由。

### 3. 调用链不能跳层

必须记录每一层的文件位置、类名、方法签名、关键调用语句和参数传递关系。接口、抽象类、父类、配置映射、工具封装、动态分发都要追到真实实现或明确标注无法确认。

代码片段必须是真实片段或准确摘录，不得用省略替代关键传递语句。

### 4. 可控性必须考虑覆盖和校验

必须检查：

- 硬编码覆盖。
- 默认值覆盖。
- 白名单或枚举约束。
- 类型转换。
- 路径或结构规范化。
- 安全配置。
- 提前返回、异常或分支阻断。

### 5. 鉴权信息只透传

若上游提供鉴权状态、优先级或发现编号，报告中原样透传并注明来源。未提供时写“未提供上游鉴权信息”。不得自行分析认证、口令、网关、传输或部署基线。

### 6. Sink 必须有代码证据

只有看到真实危险调用、配置映射、查询构造、文件操作、XML/对象解析、命令执行、外连、表达式执行、响应输出等证据时，才能写具体 `SINK_CATEGORY`。

以下情况不得推断为具体 sink：

- 只有业务方法名。
- 只有数据层/服务层类名。
- 只有保存、查询、删除等业务语义。
- 只有 class 文件但未取得可读方法体。

这类情况写 `UNCONFIRMED`，并说明需要补源码或反编译。

### 7. 范围上限

- 单入口任务只分析当前入口真实可达链。
- 批量任务按批次处理，不自行扩大范围。
- 发现相邻接口或同类 sink 候选时，只记录为超出范围，不写入当前链路证据。
- 任务规模过大时写拆分建议或 blocked，不生成半成品。

### 8. 输出校验

交付前检查：

- 每个 trace task 有 trace result 或 blocked。
- `trace_sinks.jsonl` 字段完整，包含 helper/evidence 引用。
- 报告不含内部自检、模型验收、测试提示词或 skill 规则名。
- Markdown、结构化结果和 coverage 数量一致。

## 输出文件

Standalone 模式：

- `route_tracer/...` 报告。
- 必要时写 `{output_path}/scripts/trace_helpers/`。
- 有结构化输出目录时追加 `structured/trace_sinks.jsonl` 和 coverage 更新。

Pipeline worker 模式：

- 只写本 batch 的 route tracer 目录。
- 只写本 worker 的 trace helper 目录。
- 追加结构化 trace 结果和 blocked 记录。

## 常见失败形态

| 失败表现 | 风险 | 正确处理 |
|----------|------|----------|
| 批量任务只靠 LLM 读代码写报告 | 漏链和不可复核 | 先写 trace helper |
| 只写入口到 sink，中间层缺失 | 下游无法复核 | 补齐调用边 |
| 未见 sink 代码却写具体 sink | 误报 | 写 UNCONFIRMED |
| 参数被覆盖仍写完全可控 | 误导专项审计 | 重新判定可控性 |
| 自行写鉴权结论 | 越界 | 只透传上游鉴权 |
| 把相邻方法写入当前入口 | 污染证据 | 只保留真实可达链 |

## Evals

### 正例：应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “追踪某入口的排序字段到 SQL 类 sink。” | 触发 | 明确参数流向 |
| “对 trace batch 生成 route tracer 报告。” | 触发 | pipeline worker 场景 |
| “这个服务 operation 的请求字段是否进入 XML/对象解析类 sink？” | 触发 | operation 参数追踪 |
| “只输出可控性和分支条件，不做漏洞结论。” | 触发 | 调用链证据层职责 |

### 反例：不应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “提取项目所有入口和参数。” | 不触发 | route mapper 职责 |
| “判断这个入口是否存在漏洞。” | 不直接触发 | 专项 skill 下结论 |
| “检查鉴权配置。” | 不触发 | 鉴权审计职责 |
| “扫描依赖风险。” | 不触发 | 依赖风险扫描职责 |
