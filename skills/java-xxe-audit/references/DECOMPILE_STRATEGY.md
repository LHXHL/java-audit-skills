# XML 专项反编译策略

只在源码缺失、不完整、parser 实现不可读或结构化候选来自编译产物时读取本文件。

## 优先补齐

- `ENTRY_ROUTE` 到 `XML_PARSER` 的调用链节点。
- XML 输入封装、转换、校验、对象绑定和工具封装。
- `ENTITY_RESOLUTION_CONFIG`、`EXTERNAL_RESOURCE_GUARD` 所在实现。
- 输出通道或错误处理路径。

## 证据要求

记录：

- 编译产物来源。
- 反编译输出路径。
- parser、配置、解析调用是否在同一实例或真实调用链上。
- 仍缺失的实现、配置或消息结构。

只有字符串线索或类名线索时，只能作为候选，不能作为确认漏洞证据。

## blocked

关键实现不可读时写 blocked，包含 reason、evidence 和 next_action。
