# 路由机制识别与项目专用 extractor

本文件用于 route-mapper 在全量枚举前先识别项目实际入口机制。目标不是维护万能规则库，而是让 AI 根据当前项目证据生成可脚本化模型和项目专用 extractor。

## 命名边界

本 reference 用于指导入口机制发现、项目专用 extractor 编写和 coverage 闭环。

通用占位：

- `ENTRY_ROOT`
- `DISPATCH_RULE`
- `DISPATCH_KEY`
- `ENTRY_OPERATION`
- `HANDLER_CLASS`
- `HANDLER_METHOD`
- `REQUEST_PARAM`
- `MAPPING_CONFIG`
- `EVIDENCE_FILE`

## 识别输入

优先抽样读取能证明入口机制的材料：

- Web 入口注册配置。
- 注解式入口样本。
- XML/YAML/properties 等配置式入口样本。
- 服务端点、服务描述和 operation 暴露样本。
- 页面脚本、模板、前端资源中的 URL 样本。
- 通过路径片段、参数、请求体字段、配置键、表记录、注册表或反射键继续分发的代码。
- 已存在源码或可读反编译源码。

源码不完整、部署产物与源码不一致、class/JAR 无源码时，先按共享反编译策略取得可读源码，再建模。

## route_mechanisms.json 输出

写入 `{output_path}/structured/route_mechanisms.json`。每个机制必须回答：

| 问题 | 泛化示例 |
|---|---|
| 入口根来自哪里 | `ENTRY_ROOT` 来源于配置、注解、服务描述或注册表 |
| 路由如何组合 | context + root + rule + operation |
| operation 如何枚举 | 接口声明、实现方法、服务描述、注册表、配置键 |
| 是否存在动态分发 | `DISPATCH_KEY`、路径片段、请求体字段、配置 key、注册表 |
| 哪些文件可作为证据 | `EVIDENCE_FILE`、反编译源码、配置片段、服务描述 |
| 置信度为何 | high / medium / low / blocked |

不得把“识别到 ENTRY_ROOT”当作完成。只要机制存在 operation/sub-function 规则，就必须继续展开或记录 blocked。

## 项目专用 extractor

route-mapper 不维护固定万能正则。识别机制后，按项目生成或修正 extractor，脚本负责大规模枚举并输出：

- `routes.jsonl`
- `dispatchers.jsonl`
- `coverage_report.json`
- 必要时输出入口侧 sink 候选或待追踪任务

extractor 脚本目录固定为 `{output_path}/scripts/route_extractors/`：

- `agent-1-recon` 可写共享 extractor、机制 manifest 和任务规划脚本到根部。
- `agent-1-N` worker 只能写自己的 `{output_path}/scripts/route_extractors/agent-1-{N}/` 子目录。
- worker 不得覆盖共享 extractor；如果发现规则需要修正，写入自己的子目录并在状态 JSON 记录。
- extractor 不得写入源码目录、系统临时目录、其他 worker 目录或报告目录。

extractor 必须具备以下行为：

- 按真实证据组合入口，不凭命名猜 path。
- 对服务 endpoint 逐 operation 输出 route。
- 对通配符、网关、自定义 dispatcher 输出 sub-function 或 blocked 状态。
- 对源码缺失的类先查反编译源码；无法取得可读方法体时标 blocked。
- 保留 `source_files`、`evidence`、`confidence`、`status` 和 extractor 运行证据。

## 自定义 dispatcher 标记

出现以下任一模式时标记为 `CUSTOM_DISPATCHER` 或等价类型：

- 从参数、请求体字段、路径片段或上下文读取分发键。
- 通过条件分支选择业务方法。
- 通过反射、注册表、配置键、容器对象或 handler map 调用目标。
- 一个入口方法承载多个业务 sub-function。

输出要求：

- 能精确枚举目标时，每个目标写入 `routes.jsonl`。
- 只能识别分发字段但不能枚举目标时，写入 `dispatchers.jsonl`，`status=needs_expansion` 或 `blocked`。
- 不把 dispatcher 根路径下所有 public/helper 方法都当入口。

## 半成品入口门禁

以下情况必须失败或 blocked，不能交付为完成：

- 只记录 root/通配符/服务根/网关根。
- 报告写“需进一步分析”，但没有 `dispatchers.jsonl` 或 `coverage_report.blocked`。
- high/medium 机制没有 route、dispatcher 或 blocked 覆盖。
- Markdown 数量和结构化文件数量不一致。
- operation 数、sub-function 数或实例数用估算、范围、摘要词代替。

质量门禁以结构化文件为准；Markdown 不一致时返工。
