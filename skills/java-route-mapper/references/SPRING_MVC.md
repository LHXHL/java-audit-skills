# 声明式 Web 入口兼容参考

本文件作为声明式 Web 入口的机制参考；以项目实际声明机制和 extractor 输出为准。

## 泛化模型

```text
ENTRY_ROOT
  -> DECLARED_PATH_SEGMENT
  -> PROTOCOL_METHOD
  -> HANDLER_METHOD
  -> REQUEST_PARAM
```

如果声明式入口内部继续根据 `DISPATCH_KEY` 分发，则最终 route 必须展开到 `ENTRY_OPERATION`。

## 检查点

- 路径片段是否来自真实声明。
- 是否存在类级、方法级、配置级或组合式声明。
- 请求参数是否来自查询、表单、请求体、头、会话、文件或自定义解析器。
- 对象参数是否需要展开字段。
- 自定义元数据是否需要递归解析。

## 输出

extractor 应输出结构化 route；Markdown 只解释机制和覆盖率。
