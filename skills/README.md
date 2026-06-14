# Skills 说明

本目录保存 Java Audit Skills 的正式 skill 集合。新版结构强调：AI 自主发现项目机制，skill 只规定工作闭环、结构化证据和验收标准。

## 总体原则

- `java-route-mapper` 产出入口面；`java-route-tracer` 产出调用链证据；专项漏洞 skill 才能做漏洞判定。
- 批量入口、动态分发、高风险候选和重复调用链模式必须脚本辅助。
- 漏洞类 skill 必须区分 `确认漏洞`、`条件成立`、`待验证`、`不可确认`、`非漏洞`。
- 所有数量、文件数、路由数、命中数都必须可复核；无法精确统计时写 `不可确认` 或 blocked。
- 正式报告不得包含输出自检、技能源校验、测试提示词、模型运行状态、内部规则编号、validator 过程或工具审批信息。

## 技能地图

| Skill | 分层 | 主要输入 | 主要输出 |
|---|---|---|---|
| `java-route-mapper` | 入口面数据底座 | Java 源码、部署产物、反编译目录、入口配置 | `route_mechanisms.json`、`routes.jsonl`、`dispatchers.jsonl`、`coverage_report.json` |
| `java-route-tracer` | 调用链证据层 | 已知 route、operation、trace task、候选批次 | 调用边、参数流、sink category、`trace_sinks.jsonl` |
| `java-auth-audit` | 认证授权专项 | 路由清单、鉴权门禁、策略代码、资源归属证据 | 鉴权映射、授权风险结论、blocked |
| `java-sql-audit` | SQL 专项 | SQL category sink、trace 证据、查询构造代码 | SQL 映射、注入结论、授权复核材料 |
| `java-file-upload-audit` | 文件写入专项 | 上传/写入 sink、文件名和路径流向 | 写入映射、上传风险结论 |
| `java-file-read-audit` | 文件读取专项 | 读取 sink、路径参数、输出条件 | 文件读取映射、路径遍历结论 |
| `java-xxe-audit` | XML 专项 | XML parser category、XML 输入、parser 配置 | XML parser 映射、XXE 结论 |
| `java-deserialization-audit` | 对象解码专项 | DESERIALIZE sink、对象类型控制、链条条件 | decoder 映射、链条条件结论 |
| `java-vuln-scanner` | 组件版本证据层 | 构建文件、依赖清单、部署包、规则数据 | 版本命中、触发面待核查、专项交接 |
| `java-audit-pipeline` | 编排与质检层 | source_path、output_path、真实 team 能力 | 阶段产物、QA 报告、quality_report 或 pipeline_blocked |

## 推荐流转

1. 入口不清楚时，先运行 `java-route-mapper`。
2. 需要证明请求参数是否到达 sink 时，运行 `java-route-tracer`。
3. 根据 `SINK_CATEGORY` 进入 SQL、XML、文件写入、文件读取、对象解码或鉴权专项。
4. 依赖版本问题交给 `java-vuln-scanner`；版本命中后只按触发面交给专项 skill。
5. 完整审计由 `java-audit-pipeline` 编排，缺真实 team/多 agent 调度能力时必须 blocked，不能用单进程顺序报告冒充。

## 通用边界

- route mapper 只做入口机制建模、extractor 和结构化入口证据，不下漏洞结论。
- route tracer 只做调用链、sink category、可控性和分支证据，不下专项漏洞结论。
- 专项 skill 必须消费真实 route/trace/sink 证据；缺证据时写待验证、不可确认或 blocked。
- 组件扫描只输出版本证据和触发面待核查，不证明业务风险成立。

## 输出闭环

每个大型任务至少满足：

- 机制已发现。
- 项目专用脚本或 helper 已运行。
- 结构化输出存在且 schema 一致。
- 未展开、未追踪、源码不可读、实现缺失都有 blocked 记录。
- QA 和 validator 只检查结构、类别、coverage 和 blocked 质量，不依赖某个固定框架或真实函数名。
