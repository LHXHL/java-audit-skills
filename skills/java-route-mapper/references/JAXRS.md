# 元数据路径机制兼容参考

此文件仅为旧引用路径保留，内容已泛化。不要把具体框架、注解或库 API 名称作为通用规则写入 skill。

## 识别思路

有些项目通过代码元数据声明路径片段、请求动作、参数位置和资源对象。处理这类机制时：

- 将所有路径片段归一为 `ENTRY_ROOT` 和 `ENTRY_OPERATION`。
- 将请求动作归一为 `PROTOCOL_METHOD`。
- 将参数位置归一为 `REQUEST_PARAM.location`。
- 若元数据指向子资源、代理对象或动态返回类型，继续追踪到具体 handler；无法确认则 blocked。

## extractor 责任

- 组合根路径、类级片段、方法级片段和 operation。
- 输出每个最终 operation 的 `route_id`。
- 对只声明分发根而未指向最终 handler 的项写入 `dispatchers.jsonl`。
- 记录所有组合证据，避免凭命名猜测。
