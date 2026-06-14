# 路由索引输出模板

适用场景：生成项目级入口索引。Markdown 只用于阅读，事实来源以 `structured/` 为准。

硬约束：

1. 章节顺序不得调整。
2. 所有占位符必须替换；无内容写 `无` 或 `不可确认`。
3. 不得写真实框架或库 API 示例作为模板说明。
4. 数量必须与结构化文件一致。
5. root、通配入口、网关根、服务根、动作模板不能作为最终 route 计数。

---

# 【项目名】入口索引

生成时间：【YYYY-MM-DD HH:MM:SS】

## 1. 输入范围

| 项目 | 内容 |
|------|------|
| 源码路径 | 【填写】 |
| 输出路径 | 【填写】 |
| 分析范围 | 【填写】 |
| extractor 位置 | 【填写：scripts/route_extractors/... 或无】 |

## 2. 机制覆盖

| mechanism_id | entry root | dispatch rule | operation rule | coverage | 状态 |
|--------------|------------|---------------|----------------|----------|------|
| 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【high/medium/low】 | 【routes/dispatcher/blocked】 |

## 3. 最终入口统计

| 类型 | 数量 |
|------|------|
| final routes | 【填写精确数字】 |
| dispatchers | 【填写精确数字】 |
| blocked items | 【填写精确数字】 |
| unknown params | 【填写精确数字】 |

## 4. 最终入口清单

| route_id | entry root | operation | protocol method | handler | params | evidence |
|----------|------------|-----------|-----------------|---------|--------|----------|
| 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 |

## 5. 未展开入口

| dispatcher_id | entry root | dispatch key source | blocked reason | evidence | next action |
|---------------|------------|---------------------|----------------|----------|-------------|
| 【填写或无】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 | 【填写】 |

## 6. 下游交接

- `structured/routes.jsonl`: 【填写路径】
- `structured/dispatchers.jsonl`: 【填写路径】
- `structured/route_mechanisms.json`: 【填写路径】
- `structured/coverage_report.json`: 【填写路径】
