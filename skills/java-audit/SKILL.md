---
name: java-audit
description: 当用户要求对具体 Java 源码、JAR/WAR、class、反编译产物、模块或 diff 做快速漏洞审计，并需要标准审计工作目录、CFR 反编译、确认漏洞报告、payload 与 BurpSuite 原始 HTTP 请求包时使用；只做路由清单、Java 解释、安全培训、规则编写、报告润色或非 Java 目标时不要使用。
---

# Java 快速漏洞审计

## 定位

本 Skill 用于标准化 Java 快速漏洞审计的工程流程、证据门槛和报告格式。它不替代漏洞推理，不提供固定漏洞优先级，也不把路由枚举当主产物；审计方向必须由目标项目的依赖、入口、输入面、危险调用、配置和业务代码证据动态决定。

## 首次动作

1. 识别输入类型：源码目录、单模块、JAR/WAR/class、反编译产物、diff 或混合材料。
2. 在目标项目或用户指定位置创建审计工作目录；所有工具、反编译结果、临时脚本、日志、证据和报告都必须放入该目录。
3. 若输入包含 JAR/WAR/class 且没有等价可读源码，调用 `scripts/fetch_cfr.py` 下载 CFR，再调用 `scripts/decompile_with_cfr.py` 通过 CLI 反编译。
4. 读取 `references/workflow.md` 与 `references/evidence-standard.md` 后再开始漏洞判断。
5. 输出前使用 `references/report-template.md` 的 Markdown 结构；生成文件后运行 `scripts/validate_report.py` 做边界检查。

## 确认漏洞门槛

只有同时满足以下六项，才允许进入“确认漏洞”：

- 可达：存在明确外部入口，例如 HTTP 路由、Servlet、Filter、RPC/WebService 方法或可调用 Web 入口。
- 可控：能指出用户可控参数、来源、绑定方式和进入业务代码的位置。
- 可传播：能给出从 source 到 sink 的文件/方法级传播链，中途没有有效拦截、校验、编码或白名单。
- 可利用：sink 语义确实造成安全影响，并说明现有防护为何不能阻断。
- 可复现：能给出 payload 和 BurpSuite Repeater 可用的原始 HTTP 请求包。
- 影响成立：能说明漏洞成功触发后的具体影响。

缺少任一项时，不得写入“确认漏洞”；只能写入“高风险线索 / 下一步人工验证”。

## 工作流

1. 使用 `scripts/init_audit_workspace.py` 初始化目录。
2. 按输入类型归一化材料：源码优先读源码；字节码先反编译；diff 同时追改动点和受影响调用链。
3. 快速建立攻击面：入口、用户输入、鉴权/过滤、文件/网络/数据库/进程/XML/反序列化/模板/表达式等危险面。
4. 选择高价值候选做 source-to-sink 追踪；不要全量输出路由清单。
5. 对每个候选套用确认漏洞六门槛；无法证明时降级。
6. 为确认漏洞构造 payload 与原始 HTTP 请求包；不能凭空补路径、参数、Header、Cookie 或请求体。
7. 生成 Markdown 报告并运行校验脚本；校验失败必须返工报告。

## 禁止行为

- 不得把关键词、危险依赖、危险 import、sink 命中或组件版本命中直接写成漏洞。
- 不得为了“审计出漏洞”编造入口、参数、调用链、payload 或 HTTP 请求。
- 不得把高风险线索、待验证项、疑似漏洞放入“确认漏洞”章节。
- 不得把 CFR、临时脚本或反编译产物写到项目根目录、全局目录或原源码目录。
- 不得输出真实生产凭据、真实敏感数据、批量利用脚本、持久化 payload 或破坏性操作。

## References 读取时机

- `references/workflow.md`：开始审计前读取。
- `references/workspace-contract.md`：创建或检查工作目录前读取。
- `references/decompile-cfr.md`：遇到 JAR/WAR/class 或需要复用反编译结果时读取。
- `references/evidence-standard.md`：确认或降级任何漏洞前读取。
- `references/burpsuite-request.md`：编写原始 HTTP 请求包前读取。
- `references/report-template.md`：生成最终报告前读取。
- `references/evals.md`：修改本 Skill 或校准触发边界时读取。

## 停止、确认或切换

- 目标路径不存在、没有 Java 证据或用户没有提供具体审计对象时，停止并要求补充目标。
- 需要对真实线上目标发包、爆破、批量扫描或执行破坏性 payload 时，必须先确认授权与范围。
- 用户只要路由文档、Java 解释、安全文章、规则库或报告润色时，切换到对应普通任务，不使用本 Skill。
- 找不到确认漏洞时，明确写“未发现确认漏洞”，并给出高风险线索和下一步人工验证点；不要硬凑漏洞。
