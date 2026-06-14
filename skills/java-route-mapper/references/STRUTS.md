# 动作映射入口兼容参考

本文件作为动作映射入口的机制参考。

## 泛化模型

```text
ACTION_PATTERN
  -> NAMESPACE_OR_GROUP
  -> DISPATCH_KEY
  -> ENTRY_OPERATION
  -> HANDLER_METHOD
```

## 处理要求

- 动作模板、通配符、后缀规则和命名约定都只能作为 `DISPATCH_RULE`。
- 能从配置、源码或构建产物枚举具体 operation 时，必须展开。
- 无法枚举时，写入 `dispatchers.jsonl`，并在 coverage blocked 中说明缺口。
- 参数字段来自 setter、字段绑定、请求对象或自定义绑定器时，extractor 需要标明来源。

## 禁止

- 不得只交付动作模板。
- 不得根据方法命名猜测 operation。
- 不得把未验证的动态方法当成已覆盖入口。
