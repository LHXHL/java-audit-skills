# Claude Team 编排说明

本文件在 `PIPELINE_INITIALIZATION.md` 完成后读取。它定义真实 Claude team 的 agent 拓扑、质检员池、任务依赖、产物证据和降级规则。

读取本文件前必须已经完成：

- 基础输出目录创建。
- `{output_path}/scripts/pipeline_config.json` 写入。
- `{output_path}/tmp/` 创建。
- `{output_path}/decompiled/cache/` 创建。

缺少以上任一项时，先回到初始化步骤；仍无法完成则写 `pipeline_blocked.md`，不得创建 worker。

## 能力确认

启动任何审计 worker 前，负责人必须确认当前调用是否处于真实 Claude team/agent 调度环境。由 Claude 直接调用本 skill、或平台明确提供 team/agent 调度能力时，默认具备 Claude team 能力；用户不需要额外提供证明材料。

能力确认不是要求用户提交证明，而是要求本次运行必须真实完成以下生命周期，不能顺序模拟：

- 能创建独立 worker 和独立 `agent-7-x` 质检员。
- 能等待 worker 产物落盘。
- 能在 worker 完成后启动 QA。
- 能处理 QA 不通过后的返工或阻塞。
- 能关闭或释放 team。
- 能让当前调用自然返回。

初始化 `team_execution.md` 时，能力确认可以写：

- `agent 创建能力`：`可用`，证据写“Claude 直接调用/当前平台 team 调度环境默认具备；以实际 agent 产物校验”。
- `完整生命周期能力`：`可用`，证据写“按 Claude team 调度运行；以 worker 输出、QA 报告、返工记录和关闭记录复核”。

如果本次运行实际无法创建 agent、无法启动独立质检员、无法等待 worker、无法处理返工、无法关闭或无法自然返回，必须立刻转为阻塞。阻塞时不要把模型自称、计划文字、单进程顺序执行或 worker 自述当作 team 生命周期证据。

若实际无法使用完整 team 生命周期能力：

1. 创建 `{output_path}` 和基础目录。
2. 写入 `{output_path}/team_execution.md`，在能力确认表中记录实际失败环节；如果 agent 尚未创建成功，agent 创建能力写“不可用”；如果创建成功但等待、QA、返工或关闭失败，完整生命周期能力写“不可用”或“关闭未确认”。
3. 写入 `{output_path}/pipeline_blocked.md`。
4. 阻塞原因写实际失败点，例如“无法创建独立质检员”“无法等待 worker 产物落盘”“team 生命周期未能确认关闭/继续调度”。
5. 不得顺序调用多个 skill 冒充完整流水线。
6. 不得为了补齐报告而继续启动无关业务 worker。
7. `pipeline_blocked.md` 写入后立即结束 CLI 响应，不再生成 recon、vuln、cross、trace 或专项产物。

若已经创建 team，但在 agent 调度、质检员启动、worker 回收或 team 生命周期管理中出现不可恢复异常：

1. 立即停止启动新的 worker 和下游阶段。
2. 等待已经返回的 agent 产物落盘；不要为了“补齐阶段”继续派发任务。
3. 写入 `team_execution.md` 当前状态，未被工具确认关闭的 agent 写“关闭未确认”。
4. 写入 `pipeline_blocked.md`，只使用 `quality_check_templates.md` 的阻塞报告 4 个章节。
5. 已落盘产物清单并入“已完成阶段”或“阻塞点/证据”，不得新增第 5 节。
6. 不在用户可见报告中写入低层协议帧、隐藏 team 状态目录、清理命令或原始内部错误；统一归纳为“team 生命周期未能确认关闭/继续调度”。
7. 阻塞报告写入后立即结束 CLI 响应；不要继续等待未运行 QA，不要持续轮询后台 agent。

## 输出证据

真实 team 运行必须写入 `{output_path}/team_execution.md`，包含以下 6 个章节：

```markdown
# Claude Team 执行记录

## 1. 能力确认

| 项目 | 结果 | 证据 |
|---|---|---|
| agent 创建能力 | 可用/不可用/不可确认 | Claude 直接调用或当前平台 team 调度环境；失败时写实际失败点 |
| 完整生命周期能力 | 可用/不可用/不可确认/关闭未确认 | worker 输出、QA 报告、返工记录、关闭记录；失败时写实际失败点 |
| worker 池上限 | 数字 | 用户输入或默认值 |
| 质检员池上限 | 数字 | 计算依据 |
| 初始化状态 | 完成/阻塞 | `scripts/pipeline_config.json` 和基础目录 |

## 2. Agent 拓扑

| agent | 角色 | 使用 skill/reference | 输出目录 | 状态 |
|---|---|---|---|---|
| agent-1-recon | 路由侦查 | agent_1_recon_instructions.md | route_mapper/_recon | 完成/阻塞/跳过 |
| agent-1-N | 路由 worker | java-route-mapper | route_mapper/真实模块名；未启动时写未启动 | 完成/返工/阻塞/未启动 |
| agent-2-auth-audit | 鉴权 worker | java-auth-audit | auth_audit | 完成/返工/阻塞 |
| agent-3-vuln-scanner | 组件 worker | java-vuln-scanner | vuln_report | 完成/返工/阻塞 |
| agent-4a-risk-classifier | 路由分级 | agent_4a_instructions.md | cross_analysis | 完成/返工/阻塞 |
| agent-4b-evidence-aggregator | 证据聚合 | agent_4b_instructions.md | cross_analysis | 完成/返工/阻塞 |
| agent-5-route-tracer | 分批员 | agent_5_instructions.md | cross_analysis | 完成/返工/阻塞 |
| agent-5-N | 调用链 worker | java-route-tracer | route_tracer/真实批次名；未启动时写未启动 | 完成/返工/阻塞/未启动 |
| agent-6a-sql-auditor | SQL worker | java-sql-audit | sql_audit | 完成/返工/跳过 |
| agent-6b-xxe-auditor | XXE worker | java-xxe-audit | xxe_audit | 完成/返工/跳过 |
| agent-6c-upload-auditor | 上传 worker | java-file-upload-audit | file_upload_audit | 完成/返工/跳过 |
| agent-6d-fileread-auditor | 文件读取 worker | java-file-read-audit | file_read_audit | 完成/返工/跳过 |
| agent-6e-deserialization-auditor | 反序列化 worker | java-deserialization-audit | deserialization_audit | 完成/返工/跳过 |
| agent-7-x | 质检员池 | quality_check_templates.md | qa_reports | 完成/返工/阻塞 |

## 3. 任务依赖

| 任务 | 依赖 | 进入条件 | 退出条件 |
|---|---|---|---|
| 阶段1 路由 | 无 | recon QA 通过 | merge QA 通过 |
| 阶段1 鉴权 | route merge QA | 路由索引稳定 | auth QA 通过 |
| 阶段1 组件 | 无 | 依赖路径可读 | vuln validator 通过 |
| 阶段2 交叉 | 阶段1 全部 QA | 输入齐全 | 4a/4b QA 通过 |
| 阶段3 追踪 | 阶段2 QA | 分批方案通过 | 全部 batch QA 通过 |
| 阶段4 专项 | 阶段3 QA | 有 sink 或跳过依据 | 全部专项 QA 通过 |
| 阶段5 汇总 | 前序 QA | QA 队列清空 | quality_report.md |

## 4. 质检员记录

| QA agent | 校验对象 | QA 报告 | 判定 | 返工要求 |
|---|---|---|---|---|
| agent-7-1 | agent-3-vuln-scanner | qa_reports/qa_report_agent-3-vuln-scanner.md | 通过/不通过 | 无/说明 |

## 5. 返工记录

| 被返工 agent | 轮次 | 失败原因 | 修复动作 | 复检结果 |
|---|---:|---|---|---|
| 无 | 0 | 无 | 无 | 无 |

## 6. 关闭记录

| agent | 关闭状态 | 说明 |
|---|---|---|
| agent-1-recon | 已关闭 | 输出已落盘 |
```

生成实际 `team_execution.md` 时，不得出现花括号占位符或任何“待生成/待填写”说明。初始化后阻塞时，未启动 worker 的输出目录统一写“未启动”，不要写模块名模板、批次模板或把质检员池写成待命；只记录“未启动/阻塞”和不可确认原因。

关闭状态只能使用实际工具已确认的状态：

- `已关闭`：工具明确确认 agent/team 已关闭。
- `关闭未确认`：agent 已返回结果但运行时仍未确认关闭。
- `阻塞`：agent 未完成或无法继续调度。
- `未启动`：未派发任务。

不得在同一份 `team_execution.md` 中同时写“已关闭”和“仍活跃/active/未离线”等矛盾描述。

## Worker 池

- 默认 worker 并发上限为 5，合法范围 2 到 10。
- 负责人不占 worker 槽位。
- `agent-1-recon` 和 `agent-5-route-tracer` 是协调员，不占普通 worker 槽位。
- `agent-3-vuln-scanner` 可以与路由 worker 并行，但仍计入 worker 池。
- worker 完成后关闭，输出交给质检员池异步校验。

## 质检员池

- 质检员命名为 `agent-7-1`、`agent-7-2`。
- 质检员池上限为 `ceil(worker_limit / 2)`，最小 1，最大 5。
- 质检员不占 worker 槽位。
- 每个 worker 完成后立即分配质检员校验。
- 同一 worker 不能自批自验；不得把 worker 自己的完成声明当作 QA。
- worker 自述、完成消息或口头声明不能替代 `agent-7-x` QA 报告，也不能替代本地 validator 的真实运行结果。
- 质检员报告必须写入 `qa_reports/qa_report_{被校验agent}.md`。
- 每个阶段进入下游前，必须满足 worker 完成、QA 队列清空、返工列表为空。

## 阶段角色

| 阶段 | agent | 职责 |
|---|---|---|
| 阶段1 | agent-1-recon | 按 `agent_1_recon_instructions.md` 切分物理模块和 route worker 任务 |
| 阶段1 | agent-1-N | 使用 `java-route-mapper` 提取模块路由 |
| 阶段1 | agent-1-merge | 合并 route mapper 主索引 |
| 阶段1 | agent-2-auth-audit | 使用 `java-auth-audit` 审计鉴权 |
| 阶段1 | agent-3-vuln-scanner | 使用 `java-vuln-scanner` 生成组件版本证据 |
| 阶段2 | agent-4a-risk-classifier | 生成高危路由分级 |
| 阶段2 | agent-4b-evidence-aggregator | 聚合组件版本证据和鉴权发现 |
| 阶段3 | agent-5-route-tracer | 生成调用链追踪批次 |
| 阶段3 | agent-5-N | 使用 `java-route-tracer` 追踪批次 |
| 阶段4 | agent-6a | 使用 `java-sql-audit` |
| 阶段4 | agent-6b | 使用 `java-xxe-audit` |
| 阶段4 | agent-6c | 使用 `java-file-upload-audit` |
| 阶段4 | agent-6d | 使用 `java-file-read-audit` |
| 阶段4 | agent-6e | 使用 `java-deserialization-audit` |
| 全程 | agent-7-x | 独立质检员 |

## 专项跳过

阶段4某个专项没有对应 sink 时：

- 仍保留对应目录。
- 写入 `SKIPPED.md`，包含输入文件、未触发原因、缺失证据和后续条件。
- 由 `agent-7-x` 校验跳过依据。
- 最终质量报告写“跳过”，不能写“通过”。

## 禁止事项

- 禁止单个进程顺序生成全部报告后自称 team 完成。
- 禁止没有 `team_execution.md` 时输出完整通过结论。
- 禁止 QA 文件只按阶段命名而不对应被校验 agent。
- 禁止把本地 validator 结果替代 `agent-7-x`。
- 禁止把 worker 自述的“已通过 validator”写成独立校验证据。
- 禁止在阻塞报告中暴露低层 team 协议帧、清理命令、隐藏状态目录或内部关闭错误原文。
- 禁止写出带估算的 recon 任务，例如 估算词、波浪线、尾随加号或模糊数量词；无法精确统计时写“未精确统计”。
- 禁止 `agent-1-recon` 用单个 `recon_report.md` 代替 `project_overview.md`、`module_inventory.md`、`route_worker_tasks.md`。
- 禁止写完 `pipeline_blocked.md` 后继续保持 CLI 会话不返回。
- 禁止把组件版本证据写成确认性漏洞。
- 禁止把调用链 sink 写成漏洞结论。
