# Agent-5：调用链追踪分批

## 职责

`agent-5` 把阶段2的待追踪入口拆成明确批次，供 `java-route-tracer` worker 逐批处理。它不追踪代码、不判断漏洞、不修改鉴权结论。批量、高风险候选和重复调用链模式必须要求下游 worker 先编写项目专用 trace helper，再基于 helper 证据生成报告。

## 输入

- `{output_path}/cross_analysis/high_risk_routes.md`
- `{output_path}/cross_analysis/auth_bypass_findings.md`
- `{output_path}/cross_analysis/component_version_evidence.md`

## 选择规则

1. P0 和 P1 必须全部进入追踪批次。
2. C1 仅作为附加候选；当能定位具体入口时进入批次，不能定位时写入限制说明。
3. P0+P1+C1 均为空时，才启用 P2 兜底；P2 数量过大时先要求用户确认范围。
4. 每批建议 `1-10` 个入口；复杂服务端点、网关方法或参数分支多的入口单独成批。
5. 批次内容必须包含入口、方法、参数摘要、上游鉴权标签和证据文件路径。
6. 每批必须标注 `helper_required`：单入口小任务可为 `false`，批量、候选包、动态分发、配置映射、接口实现复杂或 sink-first 任务必须为 `true`。

## 输出文件

写入 `{output_path}/cross_analysis/trace_batch_plan.md`。

```markdown
# 调用链追踪分批方案

## 1. 输入来源

| 来源 | 文件 | 状态 |
|---|---|---|
| 高危路由分级 | {path} | {已读取/缺失} |
| 鉴权绕过发现 | {path} | {已读取/未提供} |
| 组件版本证据 | {path} | {已读取/未提供} |

## 2. 分批统计

| 指标 | 数量 |
|---|---:|
| P0 路由 | {number} |
| P1 路由 | {number} |
| C1 入口 | {number} |
| P2 兜底入口 | {number} |
| 实际追踪入口 | {number} |
| 批次数 | {number} |
| 需要 trace helper 的批次 | {number} |

## 3. 批次清单

### Batch-{N}

| 序号 | 优先级 | 入口 | 方法 | 参数摘要 | 上游鉴权标签 | helper_required | 证据文件 |
|---:|---|---|---|---|---|---|---|
| {number} | P0/P1/C1/P2 | {entry} | {method} | {params} | {upstream tag} | true/false | {path/section} |

#### 透传给 java-route-tracer 的上下文

- 鉴权状态：{仅引用上游标签，不新增判断}
- 鉴权发现：{finding_id + 报告路径，或 未提供}
- 组件证据：{component + 状态 + 报告路径，或 未提供}
- 输出目录：写本轮实际 batch 输出目录，例如当前输出目录下的 `route_tracer/batch-N/`；不得保留模板占位符。
- trace helper 目录：写当前输出目录下的 `scripts/trace_helpers/agent-5-{N}/`；当 `helper_required=true` 时必须先产出机器可读 helper 证据。

## 4. 未纳入追踪的条目

| 条目 | 原因 | 后续动作 |
|---|---|---|
| {route/component} | {无法定位入口/等待用户确认/上游证据缺失} | {回到对应阶段或人工确认} |

## 5. 限制说明

- 本文件只是分批方案，不包含调用链结论。
- 下游 worker 必须使用 `java-route-tracer`，且只处理本批次入口。
- 对 `helper_required=true` 的批次，worker prompt 必须要求先写项目专用 trace helper，再写 Markdown 与 `structured/trace_sinks.jsonl`。
- 对 `helper_required=false` 的批次，worker 仍需在报告中说明证据来源；如追踪过程中发现重复模式或复杂映射，必须升级为 helper 辅助。
```

## Worker Prompt 要点

负责人生成 `java-route-tracer` worker 任务时只传递以下内容：

- 当前批次表格。
- 上游鉴权标签和证据路径。
- 组件版本证据路径。
- 指定输出目录。

不得要求 route-tracer 判断漏洞是否成立；不得要求其生成 Burp 请求或 payload。

## 强制要求

- 输出文件不得保留 `{...}`、`${...}` 或其他模板占位符。
- 不得写尾随加号、范围数量、波浪线数量或估算词；无法精确统计时写“未精确统计”。
- 多个方法或端点无法逐项枚举时，不写模糊数量，改写为“方法清单未精确统计，交给 batch worker 精确展开”。
- 阶段3启动前必须确认阶段2 QA 已通过；缺少 QA 时写阻塞，不生成分批方案。
- 批量或候选包任务没有 trace helper 目录、helper 输出或 `trace_sinks.jsonl` helper 引用时，阶段3 QA 必须判不通过。
