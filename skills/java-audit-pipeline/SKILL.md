---
name: java-audit-pipeline
description: 当用户要求用 Claude team/多 agent 编排 Java Web 全链路安全审计、调度 route-mapper/auth/vuln-scanner/route-tracer/SQL/XXE/上传/文件读取/反序列化 worker，并由独立质检员 agent 做阶段门禁和最终 quality_report 时使用；只要求单一 skill、单条调用链、依赖扫描或普通报告润色时不要使用。
---

# Java 审计流水线

## 当前定位

`java-audit-pipeline` 是 Claude team 编排 skill，不是漏洞检测 skill，也不是单进程全量扫描提示词。它负责创建和调度多个审计 worker，并使用独立 `agent-7-x` 质检员池对每个 worker 产物做门禁。

流水线只编排、传递输入、聚合产物和执行质量门禁；漏洞规则、输出模板、Burp 请求、payload 和结论均由对应子 skill 负责。

## 上游输入

- `source_path`：Java Web 源码、反编译产物或部署目录。
- `output_path`：流水线输出目录；未指定时使用 `{project_name}_audit`。
- 可选输入：并发上限、审计模块范围、已有阶段产物、用户排除模块。

## 下游产物

- `team_execution.md`：Claude team 调度记录，必须记录 worker 池、质检员池、任务依赖、返工和关闭状态。
- `pipeline_plan.md`：初始化后立即写入的阶段计划和当前状态，长任务运行中也必须存在。
- `scripts/pipeline_config.json`：流水线初始化配置，必须在创建任何 agent 前写入。
- `tmp/`、`decompiled/cache/`：流水线临时状态和共享反编译缓存；不得作为正式漏洞证据。
- `route_mapper/_recon/`、`route_mapper/`、`auth_audit/`、`vuln_report/`：阶段1产物。
- `cross_analysis/`：阶段2交叉分级和追踪分批。
- `route_tracer/`：阶段3调用链追踪 worker 产物。
- `sql_audit/`、`xxe_audit/`、`file_upload_audit/`、`file_read_audit/`、`deserialization_audit/`：阶段4专项 worker 产物；无 sink 时也要保留目录和跳过说明。
- `qa_reports/`：独立质检员 agent 为每个 worker 写的校验报告。
- `quality_report.md`：最终由质检员 agent 汇总的质量报告。
- `pipeline_blocked.md`：无法使用真实 Claude team 时的阻塞报告。

## 触发条件

- 用户要求“一键审计”“完整安全审计流水线”“Java 全链路审计”。
- 用户明确要求 Claude team、多个 agent、质检员、阶段门禁或并行编排。
- 用户要求基于路由、鉴权、组件版本、调用链和专项漏洞 skill 做统一编排。
- 用户已有多个阶段产物，要求继续 team 流水线或生成质量门禁报告。

## 不触发条件

- 只要路由清单：切换 `java-route-mapper`。
- 只要鉴权判断：切换 `java-auth-audit`。
- 只要组件版本或 CVE/组件风险命中：切换 `java-vuln-scanner`。
- 只追踪单条入口调用链：切换 `java-route-tracer`。
- 只审计 SQL、XXE、文件上传、文件读取或反序列化中的一种：切换对应漏洞 skill。
- 当前运行环境实际无法创建或调度 Claude team agent，且用户要求完整流水线：不要退化成单进程全跑；写 `pipeline_blocked.md`。

## 成功标准

- 开始前确认当前调用是否处于真实 Claude team/agent 调度环境；由 Claude 直接调用本 skill 时默认具备 team 调度能力，不要求用户额外提供证明材料。
- 能力确认是运行时门禁：能创建 agent、等待 worker 完成、启动独立 QA、处理返工或阻塞、关闭或释放 team，并让当前调用自然返回；任一环节实际失败时再阻塞。
- 工具名、模型自称、计划表或推断不能替代真实 agent 产物、QA 报告和关闭记录；但也不得因用户没有额外证明材料而提前阻塞。
- 普通用户请求“启动流水线/完整审计/使用本 skill 审计源码”只要触发 pipeline，就按默认具备 team 能力推进；不要启动虚假 worker 或顺序模拟来补证据。
- 创建任何 agent 前必须完成初始化目录、`scripts/pipeline_config.json`、`tmp/` 和 `decompiled/cache/`。
- `team_execution.md` 能证明 agent-1/2/3/4/5/6 worker 和 `agent-7-x` 质检员池的调度、依赖、校验、返工和关闭状态。
- 每个 worker 完成后由独立质检员 agent 校验；阶段进入下游前必须满足：本阶段 worker 完成、质检员队列清空、返工列表为空。
- `qa_reports/` 文件按 agent 命名，例如 `qa_report_agent-3-vuln-scanner.md`、`qa_report_agent-7-final.md`；不能只写泛化的 stage 级检查。
- `vuln_report/` 必须使用 `java-vuln-scanner` 六段模板，并通过 `java-vuln-scanner/scripts/validate_vuln_output.py`。
- 组件版本证据不写确认性漏洞结论、验证包、评分、具体版本建议、利用链或脚本外 CVE。
- 漏洞类子 skill 的确认漏洞或条件成立项必须保留 Burp Suite 请求和 payload；不可确认项不得补写验证材料。
- `java-route-tracer` 只输出调用链和 sink 证据；漏洞确认由阶段4专项 worker 完成。
- 所有 Markdown 产物不含估算数量、旧内部检查措辞、模型测试提示、未替换占位符、禁用评分字段、具体整改版本或安全版本。
- 无法完整推进时生成 `pipeline_blocked.md`，不能用半成品目录或顺序模拟报告冒充完整流水线。
- 一旦决定写 `pipeline_blocked.md`，必须停止启动新 worker；只允许记录已经落盘的产物、未运行阶段和继续条件。
- 阻塞报告必须严格使用 `quality_check_templates.md` 的 4 个章节，不得另加“已生成产物清单”等编号章节；产物清单并入第 1 节或第 2 节证据。
- `pipeline_blocked.md` 写入并刷新到磁盘后，立即结束本次 CLI 响应；不要等待未启动的 QA、不要保持后台 team 运行、不要继续追加产物。

## 工作流

1. 解析 `source_path`、`output_path` 和并发上限；创建完整目录结构。
2. 读取 `references/PIPELINE_INITIALIZATION.md`，创建基础输出目录、`scripts/`、`tmp/`、`decompiled/cache/`，并写入 `scripts/pipeline_config.json` 和 `pipeline_plan.md`。
3. 读取 `references/TEAM_ORCHESTRATION.md`，确认 Claude team 拓扑、worker 池、质检员池、任务依赖和降级规则。
4. 读取 `references/quality_check_templates.md`，确认 QA 文件、最终质量报告和阻塞报告模板。
5. 做能力确认：
   - 由 Claude 直接调用或平台已提供 team/agent 调度能力时，能力确认默认通过，写入 `team_execution.md` 初始记录并启动 team 流水线。
   - 能力证据来自本次真实运行产物：agent 启动记录、worker 输出、`agent-7-x` QA 报告、返工记录和关闭记录；不要要求用户在请求中提供额外证明。
   - 若当前环境实际没有可用 team/agent 调度能力、无法创建独立质检员、无法等待 worker、无法启动 QA 或无法让调用自然返回：写 `team_execution.md` 与 `pipeline_blocked.md`，说明实际阻塞环节、已落盘产物、未运行阶段和继续条件；停止。
   - 若 team 创建、agent 调度、QA 启动、worker 等待或 team 生命周期管理出现不可恢复异常：立刻停止启动新 worker，按阻塞模板记录当前已落盘产物和未运行阶段，随后结束 CLI 响应。
6. 阶段1：
   - `agent-1-recon` 读取 `agent_1_recon_instructions.md` 做路由侦查和切分；通过 `agent-7-x` 校验后启动 `agent-1-N`。
   - `agent-1-N` 使用 `java-route-mapper` 并行提取模块路由；每个完成后由 `agent-7-x` 校验，失败则返工。
   - `agent-1-merge` 合并主索引和 README；通过质检后启动 `agent-2-auth-audit`。
   - `agent-3-vuln-scanner` 可与路由阶段并行；完成后必须通过独立组件 validator。
   - 没有 `qa_report_agent-1-merge.md` 和每个已启动 route worker 的 QA 报告时，不得进入阶段2。
7. 阶段2：
   - `agent-4a` 读取 `agent_4a_instructions.md` 生成高危路由分级。
   - `agent-4b` 读取 `agent_4b_instructions.md` 聚合组件版本证据和鉴权发现。
   - 两者都由 `agent-7-x` 校验通过后才能进入阶段3。
8. 阶段3：
   - `agent-5-route-tracer` 读取 `agent_5_instructions.md` 生成分批方案。
   - `agent-5-N` 使用 `java-route-tracer` 并行追踪；每个批次完成后由 `agent-7-x` 校验。
9. 阶段4：
   - 负责人根据 route-tracer sink 启动对应 `agent-6x` 专项 worker。
   - 无 sink 的专项目录写 `SKIPPED.md`，并由质检员确认跳过依据。
   - 每个实际启动的专项 worker 由 `agent-7-x` 校验，失败返工。
10. 阶段5：
   - `agent-7-final` 汇总所有 QA 报告、team 执行记录和阶段产物，生成 `quality_report.md`。
   - 负责人可运行本地 validator 作为最终兜底，但 validator 不能替代 `agent-7-x` 质检员。

## References 读取时机

- `references/TEAM_ORCHESTRATION.md`：启动流水线前必须读取。
- `references/PIPELINE_INITIALIZATION.md`：解析输入后、创建任何 agent 前必须读取。
- `references/quality_check_templates.md`：创建 QA、阻塞报告和最终质量报告前读取。
- `references/agent_1_recon_instructions.md`：阶段1路由侦查和 worker 拆分时读取。
- `references/agent_4a_instructions.md`：阶段2路由分级时读取。
- `references/agent_4b_instructions.md`：阶段2证据聚合时读取。
- `references/agent_5_instructions.md`：阶段3分批时读取。

## 强制规则

- 不得把单个 Claude 进程顺序执行多个 skill 的结果冒充 Claude team。
- 不得把模型自批自验、worker 口头声明或 validator 口头声明写成 `agent-7-x` 质检员产物。
- 没有 `team_execution.md` 和 agent 命名 QA 报告时，不得生成“完整流水线通过”结论。
- 质检员必须独立于被校验 worker；同一 worker 不能自批自验。
- 子 skill 产物不合格时必须回到对应 worker 返工，不得由 pipeline 字符串替换后标记通过。
- 组件版本证据不得升级为业务漏洞确认。
- `route-tracer` sink 不得升级为漏洞确认。
- 缺失目录、缺失专项跳过说明或缺少 QA 报告，都必须阻塞。
- 缺少 `scripts/`、`tmp/`、`decompiled/cache/` 或 `scripts/pipeline_config.json` 时，不能启动 worker，也不能声称流水线已成功启动。
- 数量、行数、文件数、接口数和覆盖率必须是精确可复核值；无法精确时写 `不可确认` 或 `未精确统计`。
- `agent` 自述、worker 完成消息或口头说明不能替代独立 QA、validator 或文件证据。
- 用户可见报告不得写入低层 team 协议帧、清理命令、隐藏状态目录或内部关闭错误原文；统一归纳为“team 生命周期未能确认关闭/继续调度”并给出可复核产物路径。

## Gotchas

- Claude CLI 普通单进程模式常会顺序模拟 worker 和 QA；这不是合格的 pipeline 运行。
- `claude -p` 测试环境和 Claude 直接调用环境不同；直接调用本 skill 时默认按具备 team 能力推进，只有实际无法完成等待、QA、关闭或自然返回时才阻塞。
- QA 报告中不要引用禁用词本身；确认评分字段边界时写“未发现禁用评分字段”。
- 跳过 XXE、文件读取或上传专项时，仍要保留对应目录和 `SKIPPED.md`，否则下游无法区分“未触发”和“漏跑”。
- 反编译中间文件不是正式报告；正式质量判断只看子 skill 报告、QA 报告、team 执行记录和限制说明。
- 大项目可能需要阻塞等待真正的 team/agent 工具；清楚阻塞优于伪造完整报告。
- team worker 已落盘部分产物但 QA 尚未运行时，只能写“已完成（未 QA）”或“部分完成”，不得写“通过”。
- `team_execution.md` 的关闭记录不得和拓扑状态矛盾；未被工具确认关闭的 agent 写“关闭未确认”。
- recon 阶段也不能写估算词、范围数量、波浪线或尾随加号；入口数量不精确时写“未精确统计”。

## 停止、确认或切换条件

- 缺少 `source_path`、路径不存在或没有 Java/Web 证据：停止并要求补充。
- 只出现单一审计目标：切换到对应子 skill。
- 当前环境实际无法创建或调度独立 worker/质检员：初始化后生成 `team_execution.md` 和 `pipeline_blocked.md`，不启动顺序模拟或长任务 worker。
- 只有模型自称、计划文字或顺序执行多个子 skill 的能力：不能冒充 Claude team；若没有真实 agent 调度能力则阻塞。
- team 执行记录缺失、QA 报告缺失、阶段门禁不通过：停在当前阶段返工。
- 若无法在当前 CLI 会话继续推进或等待会造成挂起：写 `pipeline_blocked.md` 后立即返回，不持续等待。
- 运行中无法继续等待、无法回收 agent 或无法确认关闭状态时：写 `pipeline_blocked.md`，记录已完成产物和未运行阶段后返回。
- 用户要求模块范围筛选：只允许物理模块级筛选，记录到 `team_execution.md`。

## Eval 样例

| 类型 | 用户请求 | 期望行为 |
|---|---|---|
| 正例 | “对这个 Java Web 项目跑完整安全审计流水线，输出到 audit/。” | 触发 pipeline，先确认 team 能力，再编排多 agent |
| 正例 | “用 Claude team 跑 route/auth/tracer/SQL/反序列化，并让质检员检查。” | 触发，默认按 Claude team 能力可用推进，必须生成 `team_execution.md` 和 agent 命名 QA |
| 反例 | “扫描 pom.xml 有多少 CVE 命中。” | 不触发，切换 `java-vuln-scanner` |
| 反例 | “追踪 /admin/login 到 DAO 的调用链。” | 不触发，切换 `java-route-tracer` |
| 边界例 | “完整流水线，但当前运行环境实际没有 agent/team 调度能力。” | 初始化后写 `team_execution.md` 和 `pipeline_blocked.md`，不顺序模拟 |
| 失败案例 | 单个进程顺序写完所有报告，并把 stage 级内部检查当质检员 | 不合格，必须返工或阻塞 |
