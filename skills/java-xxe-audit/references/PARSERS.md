# XML parser 能力与防护规则

本文件不列具体 parser API。Agent 应从当前项目证据中识别 parser 能力类别。

## parser category

| category | 关注能力 |
|----------|----------|
| `TREE_PARSER` | 构建 XML 树或文档对象 |
| `EVENT_PARSER` | 事件式读取 XML |
| `STREAM_PARSER` | 流式读取 XML |
| `TRANSFORMER` | XML 转换、样式或模板处理 |
| `SCHEMA_VALIDATOR` | schema、DTD 或结构校验 |
| `OBJECT_BINDER` | XML 到对象的绑定或对象构造 |
| `WRAPPER` | 项目自定义 XML 工具封装 |

## 防护能力

检查 parser 是否禁用或限制：

- 外部通用实体。
- 外部参数实体。
- 外部 DTD 或 schema。
- 外部样式、导入或包含。
- 外部资源解析器。
- 网络、文件或自定义协议加载。

安全配置必须作用于实际解析实例，并且发生在解析调用前。

## 判定矩阵

| 条件 | 结论倾向 |
|------|----------|
| 可控 XML 到达 parser，外部资源未禁用 | 确认漏洞或条件成立 |
| parser 行为未知，配置不可读 | 待验证或不可确认 |
| XML 来自服务端常量或固定配置 | 非漏洞或加固建议 |
| parser 已明确禁用外部资源 | 非漏洞 |
| 只有对象构造风险，外部资源行为未知 | XXE 待验证，反序列化专项继续 |

## 禁止

- 不得凭 parser 类名、工具方法名或服务类型直接下结论。
- 不得把对象类型白名单缺失写成 XXE 防护缺口。
- 不得把候选 XML 文件或服务描述当作 parser sink。
