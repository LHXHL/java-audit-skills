# Pipeline 质量门禁

## 通用报告结构

每个 worker 的校验报告写入 `{output_path}/qa_reports/qa_report_{agent_name}.md`。`agent_name` 必须对应真实被校验 agent，例如 `agent-3-vuln-scanner`、`agent-5-2`、`agent-6e-deserialization-auditor`；不得只写 `stage1`、`stage2` 这类泛化名称。

QA 报告措辞要求：

- 不得保留 `{...}`、`${...}` 或其他模板占位符。
- 不得引用禁用词本身来说明“未发现”；例如评分、具体整改版本、内部检查措辞都用概括描述。
- 预期列不要写模板文件名格式；改写为“项目名 + 固定后缀 + 时间戳”或直接写真实文件名。
- 实际列必须写可复核文件路径、章节或统计结果，不能写泛化模板说明。
- `agent-3-vuln-scanner` 的 QA 不得写带花括号的文件名模式；写“项目名 + `_vuln_scan_` + 时间戳”或真实文件名。
- QA 判定为“不通过”时，负责人必须立即返工并更新返工记录；本轮无法返工时必须写 `pipeline_blocked.md`，不得只停留在运行中状态。

```markdown
# 校验报告: {stage_or_agent}

## 1. 基本信息

| 字段 | 值 |
|---|---|
| 校验对象 | {stage_or_agent} |
| 输入文件 | {paths} |
| 输出文件 | {paths} |
| 对应 skill | {skill 或 pipeline reference} |
| 质检员 | {agent-7-x 编号} |

## 2. 逐项校验

| # | 校验项 | 预期 | 实际 | 状态 |
|---|---|---|---|---|
| {number} | {name} | {expected} | {actual} | {通过/不通过} |

## 3. 判定

- 状态：{通过/不通过/阻塞}
- 返工次数：{number}
- 阻塞或返工原因：{如无则写“无”}
```

## Team 执行记录门禁

完整流水线成功报告必须同时存在：

| # | 校验项 | 预期 |
|---|---|---|
| 1 | 初始化目录 | `scripts/`、`tmp/`、`decompiled/cache/` 和所有阶段目录均已在 agent 启动前创建 |
| 2 | 初始化配置 | `scripts/pipeline_config.json` 存在且为有效 JSON |
| 3 | 执行计划 | `pipeline_plan.md` 在创建 agent 前存在，并持续更新阶段门禁 |
| 4 | `team_execution.md` | 记录 Claude team 能力确认、完整生命周期能力、初始化状态、worker 池、质检员池、任务依赖、返工和关闭状态 |
| 5 | 质检员独立性 | QA 报告均记录 `agent-7-x`，且不是被校验 worker 自批自验 |
| 6 | agent 命名 | QA 文件名对应被校验 agent，不使用 `qa_report_stage*.md` 作为正式通过证据 |
| 7 | 阶段依赖 | 下游阶段只读取已通过 QA 的上游产物；阶段2前必须有 route worker QA、route merge QA、auth QA、vuln QA |
| 8 | 降级行为 | 无 Claude team/agent 能力时生成 `pipeline_blocked.md`，不得顺序模拟全流程 |

`team_execution.md` 缺失时，不能生成完整通过的 `quality_report.md`；只能生成阻塞报告。

如果 team 已创建但在 worker 回收、质检员启动或继续调度时失败，阻塞报告仍必须保持固定 4 个章节：

- 已落盘产物清单写入 `## 1. 已完成阶段` 的表格说明，或写入 `## 2. 阻塞点` 的证据字段。
- 不得新增 `## 4. 已生成产物清单`、`## 5. 继续条件` 等变体章节。
- 用户可见报告不得出现低层协议帧、清理命令、隐藏 team 状态目录或内部关闭错误原文；统一写“team 生命周期未能确认关闭/继续调度”。
- worker 自述“已完成”“已通过 validator”不是 QA 证据；未由 `agent-7-x` 或本地 validator 复核时写“未 QA”或“未复核”。
- 阻塞报告写入后立即结束本次响应；不要让 CLI 继续等待未启动的 QA 或后台 worker。
- 不得因为用户没有额外证明材料就阻塞；由 Claude 直接调用或平台提供 team 调度能力时，默认按可用推进。
- 不得把工具名、模型自称、计划文字或顺序执行结果写成完整生命周期证据；最终证据必须来自 agent 产物、QA 报告、返工记录和关闭记录。
- 只有实际无法创建独立 worker/质检员、无法等待、无法 QA、无法返工或无法关闭时，才写阻塞报告。
- 阻塞报告和 `team_execution.md` 中不要写具体低层工具名作为用户可见证据；统一写实际失败环节和可复核产物路径。

## 阶段门禁

### 阶段1：路由、鉴权、组件版本

| # | 校验项 | 预期 |
|---|---|---|
| 1 | route recon 输出存在 | `_recon/project_overview.md`、`_recon/module_inventory.md`、`_recon/route_worker_tasks.md` 均存在，不用单个 `recon_report.md` 替代 |
| 2 | route recon 边界 | 只写模块、入口配置和 worker 拆分；不写预估路由数、漏洞结论或鉴权结论 |
| 3 | route_mapper 输出存在 | 主索引和模块详情存在，且能追溯 source_path |
| 4 | auth_audit 输出存在 | 鉴权映射、发现详情和验证材料符合 `java-auth-audit` 当前模板 |
| 5 | vuln_report 输出存在 | 严格符合 `java-vuln-scanner` 六段模板，文件名符合 `{project_name}_vuln_scan_{YYYYMMDD_HHMMSS}.md` |
| 6 | 组件扫描边界 | 不含验证包、评分、具体版本建议、具体升级目标、修补历史、版本范围、确认性漏洞结论 |
| 7 | 数字精确性 | 所有 Markdown 产物不得使用估算词、尾随加号或范围写法代替精确数字；无法精确统计时写“不可确认”并说明缺失证据 |
| 8 | 阶段隔离 | 三类输出目录互不覆盖，无旧轮次报告混入 |
| 9 | 组件报告校验 | `vuln_report/` 必须通过 `tools/skill-maintenance/validators/validate_vuln_output.py`；脚本未输出的 CVE/规则不得出现在报告中 |
| 10 | 阶段2前置门禁 | 进入 `cross_analysis/` 前，必须存在 route worker QA、`qa_report_agent-1-merge.md`、`qa_report_agent-2-auth-audit.md`、`qa_report_agent-3-vuln-scanner.md`，且均通过 |

阶段 QA 报告的“预期/实际”列不得原样引用带 `{...}` 的模板变量。需要说明命名格式时，写“项目名 + `_vuln_scan_` + 时间戳”或直接写真实文件名。
阶段 QA 报告不得引用任何不合格写法的字面样例；通过时写“全部为精确数字”“未发现估算写法”，不要列出坏样例。
阶段 QA 报告可以使用精确算式对账；不得使用尾随加号、波浪线或估算词。

### 阶段2：交叉分析

| # | 校验项 | 预期 |
|---|---|---|
| 1 | `high_risk_routes.md` | P0/P1/P2/C1 分级清楚，P0/P1 全量进入待追踪列表 |
| 2 | `component_version_evidence.md` | 只聚合组件版本证据和触发面待核查，不写验证请求或漏洞确认 |
| 3 | `auth_bypass_findings.md` | 只引用 `java-auth-audit` 发现和验证材料位置，不新增结论 |
| 4 | 数量一致性 | 分级统计与表格行数一致，不使用估算词或尾随加号 |

### 阶段3：调用链追踪

| # | 校验项 | 预期 |
|---|---|---|
| 1 | `trace_batch_plan.md` | 批次入口、参数、上游标签和证据路径完整 |
| 2 | route_tracer 输出 | 符合 `java-route-tracer` 当前模板，只记录调用链和 sink 证据 |
| 3 | 边界 | 不新增鉴权结论，不写漏洞确认、验证包或具体版本建议 |
| 4 | 覆盖率 | 已追踪入口数 / 应追踪入口数达到本轮设定阈值；未达到时写明原因 |

### 阶段4：专项漏洞审计

| # | 校验项 | 预期 |
|---|---|---|
| 1 | 启动条件 | 只有存在对应 sink 或用户指定证据时才启动专项 skill |
| 2 | 输出模板 | 专项报告符合对应 skill 的当前 `OUTPUT_TEMPLATE`，不得多出内部检查、模型校验或模板占位段 |
| 3 | 结论分级 | 候选、条件成立、已确认、不可确认、未命中按子 skill 原语保留 |
| 4 | 验证材料 | 已确认或条件成立的漏洞按子 skill 要求包含 Burp 请求和 payload；不可确认项不得补写 |
| 5 | 多入口聚合 | 同根因可合并，但必须保留受影响入口表和差异条件 |

### 阶段5：最终汇总

| # | 校验项 | 预期 |
|---|---|---|
| 1 | `quality_report.md` | 汇总所有实际运行阶段、校验状态、返工次数和阻塞项 |
| 2 | 不伪造 | 未运行阶段写“未运行/阻塞/跳过原因”，不补结论 |
| 3 | 可追溯 | 每个结论都能回到具体子 skill 报告路径 |

## 最终质量报告模板

```markdown
# 审计流水线质量报告

## 1. 执行概览

| 字段 | 值 |
|---|---|
| source_path | {path} |
| output_path | {path} |
| 执行模式 | {完整流水线/从已有产物继续/阻塞计划} |
| pipeline_config | {scripts/pipeline_config.json 路径} |
| 临时目录 | {tmp 和 decompiled/cache 路径} |
| team_execution | {team_execution.md 路径} |
| 质检员模式 | {独立 agent-7-x 池/阻塞} |
| 开始时间 | {timestamp} |
| 结束时间 | {timestamp 或 未完成} |

## 2. 阶段状态

| 阶段 | 产物 | 状态 | 返工次数 | 说明 |
|---|---|---|---:|---|
| 初始化 | {scripts/pipeline_config.json, tmp, decompiled/cache} | {通过/不通过/阻塞} | {number} | {说明} |
| 阶段1 路由/鉴权/组件 | {paths} | {通过/不通过/阻塞/跳过} | {number} | {说明} |
| 阶段2 交叉分析 | {paths} | {通过/不通过/阻塞/跳过} | {number} | {说明} |
| 阶段3 调用链 | {paths} | {通过/不通过/阻塞/跳过} | {number} | {说明} |
| 阶段4 专项漏洞 | {paths} | {通过/不通过/阻塞/跳过} | {number} | {说明} |

## 2.1 Team 与质检员状态

| 项目 | 实际 | 状态 |
|---|---|---|
| Claude team 能力 | {可用/不可用/不可确认} | {通过/阻塞} |
| Worker 池 | {agent 列表或数量} | {通过/不通过/阻塞} |
| 质检员池 | {agent-7-x 列表或数量} | {通过/不通过/阻塞} |
| QA 报告命名 | {qa_report_agent-* 文件数量} | {通过/不通过} |
| 返工列表 | {为空/非空/不可确认} | {通过/不通过/阻塞} |

## 3. 数据一致性

| 校验项 | 实际 | 状态 |
|---|---|---|
| 路由证据可追溯 | {actual} | {通过/不通过} |
| P0/P1 追踪覆盖 | {actual} | {通过/不通过/不适用} |
| 组件版本证据边界 | {actual} | {通过/不通过} |
| 专项漏洞验证材料 | {actual} | {通过/不通过/不适用} |

## 4. 发现汇总索引

| 类型 | 报告路径 | 数量 | 备注 |
|---|---|---:|---|
| 鉴权发现 | {path} | {number} | {说明} |
| 组件版本证据 | {path} | {number} | 非漏洞确认 |
| SQL | {path} | {number} | {说明} |
| XXE | {path} | {number} | {说明} |
| 文件上传 | {path} | {number} | {说明} |
| 文件读取 | {path} | {number} | {说明} |
| 反序列化 | {path} | {number} | {说明} |

## 5. 阻塞与限制

- {限制或阻塞项；没有则写“无”}

## 6. 下一步

- {需要返工、复测或人工确认的动作；没有则写“无”}
```

## 阻塞报告模板

当完整流水线无法继续推进时，必须写入 `{output_path}/pipeline_blocked.md`。阻塞报告不是成功报告，不能把未运行阶段写成通过。
阻塞报告只允许以下 4 个编号章节；不要增加第 5 节。已生成产物清单应放入第 1 节或第 2 节证据。
若阻塞发生在业务 worker 启动前，第 1 节只记录“初始化”，阶段1到阶段5均写入第 3 节“未运行阶段”。

```markdown
# 审计流水线阻塞报告

## 1. 已完成阶段

| 阶段 | 产物 | 状态 | 说明 |
|---|---|---|---|
| 阶段1 路由/鉴权/组件 | {paths} | {通过/不通过/部分完成} | {说明} |

## 2. 阻塞点

| 项目 | 说明 |
|---|---|
| 阻塞阶段 | {阶段2/阶段3/阶段4/最终汇总} |
| 阻塞原因 | {工具能力不足/上下文不足/上游门禁不通过/输出质量不合格/其他可证原因} |
| 证据 | {已生成文件路径、校验失败信息或缺失产物} |

## 3. 未运行阶段

| 阶段 | 原因 | 下一步 |
|---|---|---|
| {stage} | {reason} | {action} |

## 4. 继续条件

- {需要补充的工具能力、人工确认、源码范围或重新运行方式；没有则写“无”}
```

## 通用不合格信号

- 输出中出现未替换占位符、模型测试说明、内部验收说明、内部检查字样、估算统计或“已修复后通过”。
- 完整流水线声称通过，但缺少 `team_execution.md`、缺少 `agent-7-x` 质检员记录，或 QA 文件只按 `stage` 命名。
- 无 Claude team/agent 能力时继续顺序执行多个子 skill，并把结果写成完整流水线通过。
- 生成 `cross_analysis/`、`trace_batch_plan.md` 或 `route_tracer/`，但缺少 route merge QA、route worker QA、auth QA 或 vuln QA。
- 任一 QA 报告判定为“不通过”，但没有后续返工记录、复检通过报告或 `pipeline_blocked.md`。
- 阻塞报告新增第 5 节，或把“继续条件”放到第 5 节。
- 阻塞报告暴露低层 team 协议帧、清理命令、隐藏状态目录、内部关闭错误原文，或把 worker 自述写成 QA 证据。
- 任一 Markdown 报告使用估算词、波浪线、尾随加号或范围数量描述数量、大小、行号、覆盖率或方法数。
- 组件版本证据被写成确认性漏洞结论。
- 组件版本报告出现 `scan_dependencies.py` JSON 结果之外的 CVE、规则名或组件命中。
- 组件版本证据、`vuln_report/` 或 `component_version_evidence.md` 出现具体版本建议、具体升级目标或具体迁移目标。
- 缺少上游文件路径或代码位置，却给出确定结论。
- 子 skill 报告结构与当前子 skill 模板不一致。
- 阶段失败后仍继续生成下游“通过”结论。
- 只生成阶段1目录却没有 `pipeline_blocked.md`、`pipeline_plan.md` 或 `quality_report.md`。
- 缺少 `scripts/pipeline_config.json`、`tmp/` 或 `decompiled/cache/`，却继续启动 worker 或声称流水线已启动成功。
