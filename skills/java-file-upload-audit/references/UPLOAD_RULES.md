# 文件写入/上传判定规则

本文件不列具体库 API。Agent 应从项目证据中识别 `FILE_WRITE_API` 能力类别。

## category

| category | 关注点 |
|----------|--------|
| `UPLOAD_SAVE` | 上传内容是否落盘 |
| `IMPORT_WRITE` | 导入、解包或转换是否写文件 |
| `EXPORT_WRITE` | 导出是否由外部输入控制目标 |
| `OVERWRITE` | 是否可覆盖已有文件 |
| `WRAPPER_WRITE` | 项目封装是否继续调用真实写入 API |

## 必查证据

- `UPLOAD_CONTENT` 来源。
- `FILENAME_SOURCE` 是否来自外部输入。
- `PATH_JOIN` 和 `STORAGE_DIRECTORY`。
- `TYPE_GUARD`、大小限制和内容校验。
- 是否重命名。
- 是否可通过 `ACCESS_PATH` 访问或被后续执行/解析。

## 有效防护

- 服务端生成文件名。
- 固定隔离目录且规范化后校验。
- 闭合集合后缀和内容校验。
- 不可执行存储和严格访问控制。
- 覆盖保护。

## 不充分防护

- 只检查文件名非空。
- 只看客户端类型。
- 只替换少数字符。
- 保存后仍可通过公开路径直接访问。
