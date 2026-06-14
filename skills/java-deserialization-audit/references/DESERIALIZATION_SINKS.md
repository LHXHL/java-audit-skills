# 对象解码 sink 分类

本文件不列具体库 API。Agent 应从项目证据中识别 `OBJECT_DECODER` 的能力类别。

## decoder category

| category | 关注点 |
|----------|--------|
| `BINARY_OBJECT_DECODER` | 二进制对象图是否由外部输入控制 |
| `TEXT_OBJECT_DECODER` | 文本格式是否允许构造对象或设置类型 |
| `XML_OBJECT_DECODER` | XML 输入是否进入对象构造；XXE 维度交给 XML 专项 |
| `MESSAGE_OBJECT_DECODER` | 消息、缓存、任务、队列或远程调用对象是否可控 |
| `DYNAMIC_TYPE_BINDER` | 类型元数据、多态字段或类名是否可控 |
| `WRAPPER_DECODER` | 项目自定义封装是否继续调用真实 decoder |

## sink 成立条件

必须记录：

- 输入来源和可控性。
- decoder 位置。
- 类型控制方式。
- 过滤、白名单、签名、加密或固定类型限制。
- 解码后自动触发点或后续危险原语。

只有配置、注解、组件或类名时，只能作为候选。

## blocked

无法确认 decoder 实现、类型过滤或触发链时，写 blocked 或不可确认，不得猜测。
