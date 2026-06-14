# 多入口与多方法追踪

本文件描述批量入口追踪的通用流程。不要使用固定框架规则；先让 AI 识别项目自己的入口机制，再编写 trace helper。

## 何时必须写 helper

以下任一情况必须先写项目专用 trace helper：

- 一个 `ENTRY_ROOT` 对应多个 `ENTRY_OPERATION`。
- 一个 operation 可落到多个 handler 实现。
- 多个入口共享相同中间层或工具层。
- 参数通过配置、映射表、代理、接口实现或动态调用继续传递。
- 批次中入口数量超过单条人工追踪的合理范围。
- 下游需要 `trace_sinks.jsonl` 作为事实来源。

## helper 任务

| 任务 | 输出 |
|------|------|
| 入口绑定 | route_id、operation、handler 位置 |
| 调用边 | from、to、argument_map、evidence |
| 实现解析 | 接口/抽象/代理/配置映射到候选实现 |
| 参数流 | source field、local variable、object field、覆盖点 |
| sink 候选 | category、location、argument、confidence |
| 缺口 | blocked reason、missing evidence、next action |

## 多方法展开

当一个入口可能对应多个真实方法：

1. 先从 route mapper 的 `routes.jsonl` 或 `dispatchers.jsonl` 读取边界。
2. 用 helper 枚举候选 handler。
3. 对每个 handler 生成独立 trace task。
4. 同一 sink 被多个入口共享时，保留多条 route-to-sink 关系。
5. 缺实现时写 `UNCONFIRMED` 或 blocked，不合并成猜测结论。

## 输出索引

批量追踪应生成索引表：

| trace_id | route_id | operation | helper evidence | sink summary | status |
|----------|----------|-----------|-----------------|--------------|--------|
| 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【done/blocked/unconfirmed】 |

## 常见失败

- 只追 root handler，没有展开 operation。
- 把一条共享中间层调用链复制给所有入口但未证明可达。
- 未记录参数在对象字段和局部变量之间的映射。
- helper 输出只有自然语言，没有结构化证据。
- `trace_sinks.jsonl` 没有引用 helper 文件或人工证据。
