# 文件写入反编译策略

只在上传/写入实现、路径构造、参数对象或访问路径不可读时使用。

## 优先补齐

- `ENTRY_ROUTE` 到 `FILE_WRITE_API` 的调用链。
- `FILENAME_SOURCE`、`PATH_JOIN`、`STORAGE_DIRECTORY`、`TYPE_GUARD` 所在实现。
- 文件访问映射、任务处理、导入/解包和后续解析逻辑。

## 证据要求

记录编译产物来源、反编译输出路径、仍缺失的方法体和 blocked 下一步。
