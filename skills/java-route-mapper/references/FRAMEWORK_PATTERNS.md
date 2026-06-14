# 入口机制抽样参考

本文件已从固定框架规则改为机制发现参考。它不规定某类项目必须怎样解析；Agent 应根据当前源码自行归纳入口机制并编写 extractor。

## 抽样目标

在开始批量枚举前，抽样读取：

- 入口注册文件。
- 入口声明代码。
- 根分发器代码。
- 服务描述或接口描述。
- operation 映射配置。
- 参数绑定、对象绑定或请求体解析位置。

## 机制建模

每种入口机制都要写入 `route_mechanisms.json`：

```json
{
  "mechanism_id": "MECH-001",
  "entry_root_rule": "ENTRY_ROOT 来源",
  "dispatch_rule": "DISPATCH_KEY 如何选中 operation",
  "operation_rule": "ENTRY_OPERATION 如何枚举",
  "params_rule": "REQUEST_PARAM 如何枚举",
  "extractor": "scripts/route_extractors/.../extractor",
  "coverage": "high"
}
```

## 处理策略

| 发现形态 | 处理 |
|----------|------|
| 只有根入口 | 写 dispatcher，继续展开或 blocked |
| 有固定 operation 清单 | extractor 枚举到 `routes.jsonl` |
| operation 来自配置或表 | extractor 读取配置或表导出 |
| operation 由代码动态组合 | extractor 收集候选并标置信度 |
| 源码不可读或实现缺失 | 写 `coverage_report.blocked` |

## 失败门禁

以下结果不合格：

- 只列 root、通配入口或服务根。
- 报告写“需要进一步分析”但没有 blocked 记录。
- extractor 未运行，只有人工整理的自然语言路由表。
- high/medium 机制没有 route、dispatcher 或 blocked 闭合。
