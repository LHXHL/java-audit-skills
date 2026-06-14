# 路由识别说明模板

硬约束：

1. 只说明本项目实际发现的入口机制。
2. 只说明本项目实际发现的入口机制和结构化产物。
3. 数量必须精确；无法精确时写 `不可确认` 并给 blocked 证据。
4. README 不能替代结构化文件。

---

# 【项目名】入口识别说明

生成时间：【YYYY-MM-DD HH:MM:SS】

## 1. 入口机制模型

| mechanism_id | ENTRY_ROOT 来源 | DISPATCH_RULE | ENTRY_OPERATION 枚举 | REQUEST_PARAM 枚举 | extractor |
|--------------|-----------------|---------------|----------------------|--------------------|-----------|
| 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 |

## 2. 覆盖结果

| 项目 | 数量 |
|------|------|
| final routes | 【填写】 |
| dispatchers | 【填写】 |
| blocked | 【填写】 |
| high/medium mechanisms closed | 【填写】 |

## 3. 无法展开项

| id | 类型 | 原因 | 证据 | 下一步 |
|----|------|------|------|--------|
| 【填写或无】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 |

## 4. 结构化产物

- `structured/route_mechanisms.json`: 【填写】
- `structured/routes.jsonl`: 【填写】
- `structured/dispatchers.jsonl`: 【填写】
- `structured/coverage_report.json`: 【填写】

## 5. 下游使用方式

- route tracer 从 `routes.jsonl` 读取最终入口。
- 鉴权审计从 route、dispatcher 和 blocked 覆盖状态判断入口面是否完整。
- 专项漏洞审计不得使用未展开 root 作为最终入口。
