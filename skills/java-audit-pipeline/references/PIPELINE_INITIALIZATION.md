# Pipeline 初始化约束

本文件只在 `java-audit-pipeline` 启动后、创建任何 worker 或质检员前读取。它定义输出目录、脚本目录、临时目录和运行配置的初始化要求。

## 初始化顺序

1. 解析并确认 `source_path`、`output_path`、`max_concurrent_agents` 和审计范围。
2. 校验 `source_path` 存在且可读。
3. 创建完整输出目录结构。
4. 写入 `{output_path}/scripts/pipeline_config.json`。
5. 写入 `{output_path}/pipeline_plan.md`。
6. 再读取 `TEAM_ORCHESTRATION.md` 并创建 team/agent。

若第 1 到第 4 步失败，直接写 `pipeline_blocked.md`，不得启动任何 agent。

## 必须创建的目录

在任何 agent 启动前，一次性创建以下目录：

```text
{output_path}/route_mapper/_recon
{output_path}/route_mapper/.status
{output_path}/auth_audit
{output_path}/vuln_report
{output_path}/cross_analysis
{output_path}/route_tracer
{output_path}/sql_audit
{output_path}/xxe_audit
{output_path}/file_upload_audit
{output_path}/file_read_audit
{output_path}/deserialization_audit
{output_path}/qa_reports
{output_path}/scripts
{output_path}/tmp
{output_path}/decompiled/cache
```

目录创建是 pipeline lead 的职责，不交给 worker 自行补齐。worker 只能写入负责人指定的输出目录。

## scripts 目录

`{output_path}/scripts/` 用于保存本次流水线运行需要的确定性配置和临时 helper 脚本。

必须写入：

```json
{
  "schema_version": 1,
  "source_path": "{source_path}",
  "output_path": "{output_path}",
  "max_concurrent_agents": 5,
  "audit_scope": "all",
  "created_at": "{timestamp}"
}
```

要求：

- `pipeline_config.json` 必须是有效 JSON。
- `max_concurrent_agents` 必须是数字，合法范围为 2 到 10。
- 若用户限制审计范围，`audit_scope` 写入 include/exclude 模块清单和确认时间。
- 运行时生成的 helper 脚本只能写入 `scripts/`，不得写到源码目录或系统临时目录。
- 不得把脚本目录作为正式审计报告目录。

## pipeline_plan.md

`{output_path}/pipeline_plan.md` 必须在创建任何 agent 前写入，用于记录运行中状态。长时间运行、被中断或阻塞时，至少能通过该文件还原当前阶段。

```markdown
# 审计流水线执行计划

## 1. 初始化

| 项目 | 值 |
|---|---|
| source_path | {实际路径} |
| output_path | {实际路径} |
| pipeline_config | scripts/pipeline_config.json |
| 初始化目录 | 完成/阻塞 |

## 2. 阶段计划

| 阶段 | 进入条件 | 退出条件 | 当前状态 |
|---|---|---|---|
| 阶段1 路由/鉴权/组件 | 初始化完成 | route merge QA、auth QA、vuln QA 均通过 | 未启动 |
| 阶段2 交叉分析 | 阶段1 全部 QA 通过 | 4a/4b QA 通过 | 未启动 |
| 阶段3 调用链 | 阶段2 QA 通过 | 全部 batch QA 通过 | 未启动 |
| 阶段4 专项漏洞 | 阶段3 QA 通过 | 专项 QA 通过或写明跳过 | 未启动 |
| 阶段5 质量汇总 | QA 队列清空 | quality_report.md | 未启动 |

## 3. 门禁状态

| 门禁 | 状态 | 证据 |
|---|---|---|
| route merge QA | 未通过/通过/阻塞 | {实际 QA 文件或无} |
| auth QA | 未通过/通过/阻塞 | {实际 QA 文件或无} |
| vuln QA | 未通过/通过/阻塞 | {实际 QA 文件或无} |
```

要求：

- 运行中可以更新 `pipeline_plan.md`，但不能删除。
- 进入新阶段前，必须把上一阶段门禁状态更新为“通过”并填写 QA 文件路径。
- 若进程需要阻塞，`pipeline_plan.md` 与 `pipeline_blocked.md` 的阶段状态必须一致。
- 若因实际无法创建或调度 Claude team agent 而在业务 worker 启动前阻塞，`pipeline_plan.md` 中阶段1到阶段5都保持“未启动”，门禁状态写“阻塞”或“未通过”，证据写 `pipeline_blocked.md`；不得把阶段1写成“进行中”。

## tmp 与 decompiled/cache

- `{output_path}/tmp/` 保存流水线临时状态、排序中间结果、待返工队列快照等可删除文件。
- `{output_path}/decompiled/cache/` 保存共享反编译缓存；每个 worker 如需独占反编译目录，由负责人在派发前创建 `{output_path}/decompiled/{agent_id}/`。
- 临时目录内容不得作为漏洞证据或最终报告引用；正式报告必须引用子 skill 报告、源码路径、route mapper 产物或 QA 报告。
- 不得把源码、skill、references 或 scripts 复制到临时目录作为规避上下文限制的手段。

## 初始化记录

初始化完成后，在 `team_execution.md` 或 `pipeline_blocked.md` 中记录：

| 项目 | 值 |
|---|---|
| 初始化状态 | 完成/阻塞 |
| 创建目录数 | {number} |
| 配置文件 | `{output_path}/scripts/pipeline_config.json` |
| 执行计划 | `{output_path}/pipeline_plan.md` |
| 临时目录 | `{output_path}/tmp`, `{output_path}/decompiled/cache` |

数量必须来自实际目录清单；无法确认时写“未精确统计”。

## 禁止事项

- 禁止在创建基础目录前启动 worker。
- 禁止由 worker 自行创建全局目录结构。
- 禁止把 helper 脚本、临时状态或反编译缓存写入源码目录。
- 禁止把 `scripts/`、`tmp/`、`decompiled/cache/` 中的内容当作正式漏洞证据。
- 禁止缺少 `scripts/pipeline_config.json` 时声称完整流水线启动成功。
- 禁止缺少 `pipeline_plan.md` 时启动 worker。
