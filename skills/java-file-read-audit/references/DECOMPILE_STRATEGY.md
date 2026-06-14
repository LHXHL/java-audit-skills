# 文件读取反编译策略

只在读取实现、路径构造、参数对象或输出通道不可读时使用。

## 优先补齐

- `ENTRY_ROUTE` 到 `FILE_READ_API` 的调用链。
- `PATH_JOIN`、`BASE_DIRECTORY`、`NORMALIZATION_GUARD` 所在实现。
- 参数对象、ID 映射、资源映射和输出通道。

## 证据要求

记录编译产物来源、反编译输出路径、仍缺失的方法体和 blocked 下一步。
