---
name: java-route-mapper
description: 当用户要求从 Java Web 源码、部署产物、反编译目录或 pipeline worker 中发现、建模、枚举路由入口、端点、operation、dispatcher 分支和请求参数，并为后续鉴权、调用链或专项漏洞审计提供结构化入口证据时使用；只做漏洞判定、调用链追踪、鉴权判断、依赖风险扫描或文档润色时不要使用。
---

# Java Route Mapper

## 当前定位

`java-route-mapper` 是 Java 审计技能集的入口面数据底座。它不维护一套固定框架规则，而是让 AI 先理解当前项目如何构造入口，再生成项目专用 extractor 完成批量枚举。

本 skill 只回答：

- 外部请求从哪些入口根进入。
- 入口根后是否存在二级、三级或自定义分发。
- 每个最终 operation/sub-function 对应哪个入口方法。
- 请求参数从哪里来，能否交给后续调用链或专项漏洞审计。

本 skill 不做漏洞结论、不判断鉴权是否正确、不追踪完整调用链、不扫描依赖风险。

## 成功标准

完成后必须能让下游 agent 精确回答：“从哪个入口进入，用户可控参数叫什么，入口代码在哪里。”

最低合格输出：

- 覆盖所有发现的 Web/RPC/服务入口，不只列关键接口。
- 先生成 `structured/route_mechanisms.json`，说明项目实际入口机制和分发规则。
- 生成 `structured/routes.jsonl`、`structured/dispatchers.jsonl`、`structured/coverage_report.json`。
- Markdown 只作为阅读报告，不能作为唯一事实来源。
- 每个最终入口都有 HTTP/协议方法、完整入口路径或服务地址、operation/sub-function、入口类方法、参数结构、证据位置。
- 泛化入口根、通配符、网关、服务根、动作模式、反射分发、表驱动分发不能冒充最终路由。
- 无法展开的机制必须写入 dispatcher 或 coverage blocked，说明原因、证据和下一步；不得只写“需进一步分析”。
- 所有数量必须是精确可复核数字；没有精确枚举时写 blocked 或 `不可确认`，不得写估算。

## 输入与模式判断

先判断执行模式：

| 模式 | 触发条件 | 输出责任 |
|------|----------|----------|
| Standalone | 用户直接要求对项目做路由映射 | 生成结构化入口索引和阅读报告 |
| Pipeline worker | prompt 中出现 `agent-1-{N}`、指定模块和状态文件 | 只生成该 worker 负责范围内的产物 |
| Pipeline merge | prompt 中出现 `agent-1-merge` 或只要求合并 worker 产物 | 不重新扫描源码，只合并已通过 worker 输出 |

如果可从用户给出的源码路径、输出路径或模块路径推导输入范围，直接执行；缺少源码路径或无法访问文件时再询问。

## 自主发现工作流

1. 确认源码路径、输出路径、可写范围和 worker 边界。
2. 读取 `references/ROUTE_MECHANISM_DISCOVERY.md`。
3. 抽样读取入口注册点、配置、注解、反编译源码、页面脚本、服务描述、分发表和网关代码。
4. 建立入口机制模型：`ENTRY_ROOT -> DISPATCH_RULE -> ENTRY_OPERATION -> REQUEST_PARAM -> EVIDENCE`。
5. 根据模型编写或修正项目专用 extractor，不套固定万能正则。
6. 运行 extractor，写入结构化文件；大规模枚举必须脚本化。
7. 对每个 high/medium 置信机制检查是否已经展开为 route、dispatcher 或 blocked。
8. 生成 Markdown 报告，报告数量必须与结构化文件一致。
9. 运行适用 validator；失败时回到机制模型或 extractor 修正，不交付半成品。

## 按需读取的 references

- 路由机制识别和项目 extractor：`references/ROUTE_MECHANISM_DISCOVERY.md`
- 结构化证据 schema：`../java-audit-pipeline/references/STRUCTURED_EVIDENCE_FLOW.md`
- 需要反编译：`references/DECOMPILE_STRATEGY.md`
- 输出模板：`references/OUTPUT_TEMPLATE_INDEX.md`、`references/OUTPUT_TEMPLATE_MODULE.md`、`references/OUTPUT_TEMPLATE_README.md`
- 通用输出规范：`../java-shared/OUTPUT_STANDARD.md`

框架专项 reference 只作为启发，不作为固定规则来源；优先相信当前项目证据和 extractor 运行结果。

## 强制规则

### 1. 入口根不是最终路由

以下都只能视为 root 或 dispatcher，不能直接交付为最终入口：

- 泛化服务根。
- 泛化动作模式。
- 泛化网关路径。
- 带通配符的 URL 模板。
- 通过参数、请求体字段、路径片段、配置键、表记录或反射键再分发的入口。

发现这些入口后，必须继续识别 operation/sub-function 枚举规则。能枚举则写入 `routes.jsonl`；不能枚举则写入 `dispatchers.jsonl` 和 `coverage_report.blocked`。

### 2. 项目专用 extractor 优先

AI 可以自由选择解析策略和脚本实现，但批量枚举必须由项目专用 extractor 负责。extractor 需要：

- 读取真实配置、源码和反编译源码。
- 组合真实 context、root、namespace、service address、operation 或分发键。
- 输出稳定 ID、参数、证据、置信度和状态。
- 记录未覆盖机制和 blocked 原因。

不得让 LLM 通过长上下文人工读取全量源码后直接写最终清单。

### 3. 动态分发必须闭环

动态分发包括但不限于：

- URL 模式把片段映射到类或方法。
- 参数或请求体字段选择业务方法。
- 配置表、注册表、映射表或脚本生成入口。
- 网关方法承载多个业务 sub-function。
- 服务端点下再暴露多个 operation。

每个精确目标都作为独立入口计数；无法精确目标时不得猜测。

### 4. URL 和参数只能来自证据

完整入口只能由真实配置、注解、源码、反编译源码、服务描述或运行产物组合。不得凭类名、文件名、bean id、方法名或业务语义猜路径。

每个入口至少标注：

- 路径/协议参数。
- Query/Form/Body 参数。
- Header/Cookie 中由代码显式读取的业务参数。
- 文件参数。
- 服务 operation 参数。

类型未知时写 `unknown` 和证据原因；不得编造类型。

### 5. Pipeline worker 隔离

在 `agent-1-N` worker 模式下：

- 只扫描分配范围，但可只读公共配置、公共基类和依赖。
- 只写 `{output_path}/route_mapper/{module_name}/`。
- 只写 `{output_path}/decompiled/agent-1-{N}/`。
- 只写 `{output_path}/scripts/route_extractors/agent-1-{N}/`。
- 不写主索引、项目 README、其他 worker 子目录或共享脚本根目录。
- 完成后写 `.status/agent-1-{N}.json`，数字字段使用 JSON number。
- 发现规模异常增长时写 overflow 状态，等待重新拆分。

### 6. 输出校验

交付前必须检查：

- `route_mechanisms.json` 中每个 high/medium 机制有 route、dispatcher 或 blocked 覆盖。
- `routes.jsonl` 中最终入口不是 root/dispatcher 模板。
- `dispatchers.jsonl` 中每个未展开 dispatcher 有状态和证据。
- `coverage_report.json` 数量与实际文件一致。
- Markdown 报告与结构化数量一致。
- 文件中不含占位符、估算数量或省略替代枚举。

自检失败时继续修正；只有输入文件缺失、源码不可读、反编译失败且无法恢复时，才记录 blocked。

## 输出文件

Standalone 模式：

- `structured/route_mechanisms.json`
- `structured/routes.jsonl`
- `structured/dispatchers.jsonl`
- `structured/coverage_report.json`
- `route_mapper/...` 阅读报告

Pipeline worker 模式：

- 只写分配模块报告和 worker 状态。
- 追加或生成结构化文件时遵守 worker 边界。

Pipeline merge 模式：

- 只合并已通过 worker 输出，不重新扫描源码。

## 常见失败形态

| 失败表现 | 风险 | 正确处理 |
|----------|------|----------|
| 只输出泛化入口根 | 下游无法定位 operation | 继续展开或写 blocked |
| 用 URL 模板代替实例 | 漏掉实际入口 | extractor 枚举实例 |
| 用类名/方法名猜路径 | 路径错误 | 从真实配置组合 |
| 只写参数对象名 | 下游无法追踪字段 | 展开字段或写 unknown 原因 |
| 未展开动态分发却写完成 | 漏扫 | 写 dispatcher 和 coverage blocked |

## Evals

### 正例：应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “提取这个 Java Web 项目的所有入口和参数，输出 route_mapper。” | 触发 | 明确要求入口映射 |
| “这个项目路由是动态拼出来的，帮我展开成具体入口。” | 触发 | 动态分发闭环是核心职责 |
| “agent-1-4 只处理某模块，生成状态 JSON。” | 触发 | pipeline worker 场景 |
| “列出服务端点和每个 operation 参数。” | 触发 | 服务 operation 映射 |

### 反例：不应触发

| 用户输入 | 预期 | 理由 |
|----------|------|------|
| “判断某接口是否越权。” | 不触发 | 使用鉴权审计 |
| “扫描依赖风险。” | 不触发 | 使用依赖风险扫描 |
| “把接口文档润色成 Markdown。” | 不触发 | 文档转换任务 |
| “追踪这个参数到危险调用。” | 不触发 | 使用 route tracer |
