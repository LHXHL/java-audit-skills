# 多入口 trace 索引模板

适用场景：一个批次、一个 dispatcher 或一组高风险候选对应多个 trace task。

硬约束：

1. 批量任务必须有 trace helper。
2. 每个 task 必须是 `done`、`blocked` 或 `unconfirmed`。
3. `trace_sinks.jsonl` 必须引用 helper 或 manual evidence。
4. 不得把 root 入口当成 operation。

---

# 【项目名】trace 批次索引

## 1. 批次范围

| 项目 | 内容 |
|------|------|
| batch_id | 【填写】 |
| 输入来源 | 【填写】 |
| trace helper | 【填写路径】 |
| 输出目录 | 【填写】 |

## 2. 追踪结果

| trace_id | route_id | operation | 参数 | sink summary | evidence | status |
|----------|----------|-----------|------|--------------|----------|--------|
| 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【done/blocked/unconfirmed】 |

## 3. blocked 闭环

| item_id | item_type | reason | evidence | next_action |
|---------|-----------|--------|----------|-------------|
| 【填写或无】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 |

## 4. 结构化产物

- `structured/trace_sinks.jsonl`: 【填写】
- `structured/coverage_report.json`: 【填写】
