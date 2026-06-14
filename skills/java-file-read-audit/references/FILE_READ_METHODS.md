# 文件读取 sink 分类

本文件不列具体库 API。Agent 应从项目证据中识别 `FILE_READ_API` 能力类别。

## category

| category | 关注点 |
|----------|--------|
| `LOCAL_FILE_READ` | 本地路径是否受外部输入影响 |
| `RESOURCE_READ` | 资源名、资源路径或资源根是否可控 |
| `DOWNLOAD_STREAM` | 文件或资源是否返回给响应通道 |
| `TEMPLATE_OR_CONFIG_READ` | 模板、配置或脚本文件是否可由输入选择 |
| `WRAPPER_READ` | 项目封装是否继续调用真实读取 API |

只有输出通道而没有文件/资源来源时，不是 `FILE_READ_API`。

## 必查证据

- 路径或资源名来源。
- `BASE_DIRECTORY` 来源。
- `PATH_JOIN` 方式。
- `NORMALIZATION_GUARD` 是否在读取前生效。
- 输出或敏感后续使用条件。

## blocked

缺读取实现、缺路径来源或缺输出条件时写待验证、不可确认或 blocked。
