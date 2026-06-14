# 元数据入口参考

本文件只作为兼容入口保留。不要把任何具体元数据、框架或库 API 名称写入 skill 通用说明；实际项目中的真实名称只能出现在审计输出证据里。

## 使用原则

- 先识别项目中哪些文件或代码片段承担“入口声明”作用。
- 把声明内容抽象为 `ENTRY_ROOT`、`DISPATCH_RULE`、`ENTRY_OPERATION`、`REQUEST_PARAM`。
- 若声明只给出根路径、服务根、通配模式或分发容器，必须继续追踪内部 `DISPATCH_KEY`。
- 项目专用 extractor 应从真实源码中读取声明结构，不套用固定规则表。

## extractor 应提取

| 字段 | 说明 |
|------|------|
| `source_file` | 入口声明所在文件 |
| `source_line` | 可定位行号；无法定位写 `unknown` 并说明原因 |
| `entry_root` | 外部可达根入口 |
| `dispatch_rule` | 如何映射到具体 operation |
| `operation_rule` | 可枚举 operation 的来源 |
| `params_rule` | 参数来源和字段枚举方式 |
| `confidence` | `high` / `medium` / `low` |

## 禁止

- 不得因为发现入口声明就直接交付最终路由。
- 不得凭类名、方法名、文件名或业务语义猜测 URL。
- 模板只保留机制字段和证据字段。
