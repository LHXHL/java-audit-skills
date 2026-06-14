# 结构化证据流

本文件定义 `java-audit-pipeline`、`java-route-mapper`、`java-route-tracer` 和专项漏洞 skill 之间的机器可校验证据。Markdown 报告仍用于交付，但不得作为唯一事实来源。

## 命名边界

本 reference 定义 pipeline 结构化证据的文件、字段和闭环关系。

通用占位：

- `ENTRY_ROOT`
- `ENTRY_OPERATION`
- `DISPATCH_KEY`
- `REQUEST_PARAM`
- `SOURCE_FIELD`
- `HANDLER_CLASS`
- `HANDLER_METHOD`
- `TRACE_HELPER`
- `SINK_CATEGORY`
- `SINK_API_CATEGORY`
- `EVIDENCE_FILE`

## 目录与文件

结构化产物写入 `{output_path}/structured/`：

| 文件 | 责任阶段 | 用途 |
|---|---|---|
| `route_mechanisms.json` | route mechanism discovery | 记录项目实际入口机制、解析规则和证据 |
| `routes.jsonl` | route extractor | 逐入口、逐 operation、逐 dispatcher 分支索引 |
| `dispatchers.jsonl` | route extractor | 动态 dispatcher、分发字段和目标候选 |
| `sink_candidates.jsonl` | sink-first scanner | 全局高危 sink 候选和包装链 |
| `trace_tasks.jsonl` | risk classifier | 需要 route-tracer 深挖的最小任务 |
| `trace_sinks.jsonl` | route-tracer | 入口到 sink 的结构化调用链证据 |
| `candidate_packages.jsonl` | risk classifier | 交给 LLM 深审的高价值候选包 |
| `coverage_report.json` | QA / validator | 数量闭合、跳过原因、blocked 原因和专项派发状态 |

## route_mechanisms.json

顶层对象：

```json
{
  "schema_version": 1,
  "source_path": "<SOURCE_PATH>",
  "generated_at": "ISO8601",
  "mechanisms": []
}
```

每个 mechanism 至少包含：

| 字段 | 说明 |
|---|---|
| `mechanism_id` | 稳定 ID |
| `type` | `ANNOTATION_ROUTE`、`CONFIG_ROUTE`、`SERVLET_ROOT`、`SERVICE_ENDPOINT`、`CUSTOM_DISPATCHER` 等泛化类型 |
| `entry_root` | 入口根、namespace、服务根或 dispatcher 根 |
| `config_files` | 配置、源码、反编译源码或服务描述路径数组 |
| `route_rule` | path/endpoint 组合规则 |
| `operation_rule` | operation/sub-function 枚举规则；无则写 `none` |
| `dispatch_keys` | 动态分发字段数组 |
| `evidence` | 可复核证据数组 |
| `confidence` | `high`、`medium`、`low`、`blocked` |

## routes.jsonl

每行一个最终入口。服务 operation 和自定义 dispatcher sub-function 必须逐条展开。

必填字段：

```json
{
  "schema_version": 1,
  "route_id": "stable-route-id",
  "mechanism_id": "stable-mechanism-id",
  "entry_type": "SERVICE_ENDPOINT",
  "context_path": "<CONTEXT_PATH>",
  "path": "<ENTRY_PATH>",
  "http_method": "POST",
  "operation": "ENTRY_OPERATION",
  "class": "HANDLER_CLASS",
  "method": "HANDLER_METHOD",
  "params": ["REQUEST_PARAM"],
  "source_files": ["EVIDENCE_FILE"],
  "evidence": ["EVIDENCE_FILE:LINE"],
  "confidence": "high",
  "status": "discovered"
}
```

禁止：

- 用 root/dispatcher/template 代替最终 operation。
- 在 `operation`、`method`、`params` 中写摘要词、省略词或估算。
- 把未确认 helper 方法写成真实入口。

## dispatchers.jsonl

用于动态分发和自定义网关。

必填字段：

```json
{
  "schema_version": 1,
  "dispatcher_id": "stable-dispatcher-id",
  "mechanism_id": "stable-mechanism-id",
  "entry_route_id": "optional-root-route-id",
  "dispatch_type": "PARAMETER",
  "dispatch_keys": ["DISPATCH_KEY"],
  "target_rule": "DISPATCH_RULE",
  "target_methods": ["ENTRY_OPERATION"],
  "evidence": ["EVIDENCE_FILE:LINE"],
  "confidence": "medium",
  "status": "needs_expansion"
}
```

如果目标无法精确枚举，`status` 写 `blocked` 或 `needs_expansion`，并在 `coverage_report.json` 记录原因；不得写估算数量。

## sink_candidates.jsonl

来自 sink-first 扫描，用于找高价值追踪目标。

必填字段：

```json
{
  "schema_version": 1,
  "sink_id": "stable-sink-id",
  "route_id": null,
  "source_param": "SOURCE_FIELD",
  "sink_types": ["SINK_CATEGORY"],
  "sink_api": "SINK_API_CATEGORY",
  "wrapper_chain": ["CALL_EDGE"],
  "class": "HANDLER_CLASS",
  "method": "HANDLER_METHOD",
  "source_files": ["EVIDENCE_FILE"],
  "evidence": ["EVIDENCE_FILE:LINE"],
  "controllability": "unknown",
  "dispatch_to": ["java-sql-audit"],
  "status": "candidate"
}
```

跨专项 sink 必须用多标签表达类别，不靠真实 API 名判断。例如：

- XML 对象解析类 sink：`sink_types` 同时包含 `XML` 和 `DESERIALIZE`，并派发到对应两个专项。
- SQL 结构类 sink：`sink_types` 包含 `SQL`，并标注 `source_param` 是否来自入口参数、JSON 字段、query/form 参数或 dispatcher 字段。
- 文件读取类 sink：`sink_types` 包含 `FILE_READ` 或 `FILE`。
- 上传或外部文件写入类 sink：`sink_types` 包含 `UPLOAD` 或 `FILE_WRITE`。

## trace_tasks.jsonl

风险分级阶段生成的最小追踪任务。

必填字段：

```json
{
  "schema_version": 1,
  "task_id": "stable-trace-task-id",
  "route_id": "stable-route-id",
  "source_param": "REQUEST_PARAM",
  "target_sink_id": "optional-sink-id",
  "priority": "P0",
  "reason": "why-this-is-worth-tracing",
  "evidence": ["EVIDENCE_FILE:LINE"],
  "status": "queued"
}
```

## trace_sinks.jsonl

route-tracer 输出的入口到 sink 证据。批量任务、高风险候选和重复模式必须引用 trace helper 证据。

必填字段：

```json
{
  "schema_version": 1,
  "trace_id": "stable-trace-id",
  "task_id": "optional-task-id",
  "route_id": "stable-route-id",
  "source_param": "REQUEST_PARAM",
  "sink_types": ["SINK_CATEGORY"],
  "sink_api": "SINK_API_CATEGORY",
  "call_chain": ["CALL_EDGE"],
  "guards": ["GUARD_CONDITION"],
  "class": "HANDLER_CLASS",
  "method": "HANDLER_METHOD",
  "source_files": ["EVIDENCE_FILE"],
  "evidence": ["EVIDENCE_FILE:LINE"],
  "helper": {
    "script": "TRACE_HELPER",
    "output": "TRACE_HELPER_OUTPUT",
    "mode": "scripted"
  },
  "controllability": "unknown",
  "dispatch_to": ["java-sql-audit"],
  "status": "candidate"
}
```

单入口小任务可写 `helper.mode="manual"`，但必须有人工追踪证据。批量或 structured candidate 模式不得缺少 helper 信息。

## coverage_report.json

顶层对象：

```json
{
  "schema_version": 1,
  "route_total": 0,
  "route_processed": 0,
  "dispatcher_total": 0,
  "sink_total": 0,
  "trace_task_total": 0,
  "trace_sink_total": 0,
  "candidate_package_total": 0,
  "skipped": [],
  "blocked": [],
  "cross_specialty_checks": []
}
```

`skipped` / `blocked` 每项必须包含：

- `item_id`
- `item_type`
- `reason`
- `evidence`
- `next_action`

必须记录的 blocked 场景：

- root/dispatcher 无法展开 operation。
- trace task 未追踪。
- 源码不可读或反编译不可用。
- 实现类缺失。
- sink 候选无法确认真实调用。
- schema 不一致导致下游不能消费。

`cross_specialty_checks` 记录多标签 sink 是否被派发到所有对应专项，不依赖真实 API 名。

## 反编译优先规则

源码缺失、源码不完整、部署产物与源码不一致时，先生成可读反编译源码，再让 extractor、trace helper 和专项技能消费。

允许使用底层字节码线索的情况仅限：

- 反编译失败。
- 反编译结果缺方法体。
- 需要确认反编译是否遗漏关键调用。

正式报告写“已检查可读反编译源码”或“未取得关键类可读反编译结果”，不要写内部命令或工具失败细节。

## 风险评分输入

候选评分至少考虑：

- 外部可达或 dispatcher 可达。
- 上游鉴权弱或未提供鉴权信息。
- sink 类型危险度。
- 输入是否来自 HTTP/RPC/上传/导入/配置。
- 是否处于动态分发、反射分发、源码缺失或反编译场景。
- trace helper 是否已确认入口到 sink 的调用边。

只把高价值候选写入 `candidate_packages.jsonl` 交给 LLM 深审；低分候选保留索引和状态。
