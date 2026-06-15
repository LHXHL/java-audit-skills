# Java Audit Skill

本仓库提供一个中文 `java-audit` Skill，用于标准化 Java 快速漏洞审计、路由信息梳理、鉴权信息梳理、Java Web 组件暴露面识别、组件漏洞命中扫描的流程、工程目录、反编译工具调用、证据门槛和 Markdown 报告格式。

新版不再维护旧的多 Skill 体系，也不把路由枚举、鉴权梳理、组件暴露面或专项漏洞知识拆成多个入口。`java-audit` 的核心职责是让 AI 在处理具体 Java 目标时保持稳定流程：先建立工作目录，必要时用 CFR 反编译，再按用户意图输出漏洞、路由或鉴权报告。漏洞审计会先梳理鉴权，再识别 Java Web 组件暴露面，运行组件漏洞命中扫描和 Query Pack 硬检索，随后进入漏洞族初筛和候选深审。

## 适用场景

- 审计 Java 源码目录、单模块、JAR/WAR/class、反编译产物、diff 或混合材料。
- 快速寻找真实可利用漏洞，只输出满足证据门槛的确认漏洞。
- 梳理当前源码的路由信息、接口入口、Handler、参数和证据位置。
- 梳理当前源码的鉴权信息、认证授权机制、权限配置和路由鉴权映射。
- 识别 Java Web 组件暴露面，并将组件映射到漏洞族候选继续审计。
- 使用内置 `java-vulnerability.yaml` 扫描依赖、JAR/WAR、`WEB-INF/lib` 的组件漏洞命中，并把命中归类到候选闭环。
- 使用 Query Pack 对源码和反编译产物做基础检索，并把命中归类到候选闭环。
- 需要 payload 和 BurpSuite Repeater 可用的原始 HTTP 请求包。
- 需要把工具、临时脚本、反编译结果、证据、日志和报告统一放入审计工作目录。

## 前言

随着 AI 尤其是大模型的快速发展，模型能力几乎每隔一段时间就会发生明显变化，这也要求 Skill 必须持续更新。如果 Skill 仍然沿用旧模型时代的写法，堆叠大量细节、固定流程和过度说明，反而会限制新模型的理解、推理和发挥。

因此，现在的 Skill 更应该偏向“架构化设计”，而不是“说明书式堆内容”。它只需要明确目标、边界、原则、工具和关键流程，把具体判断和执行交给模型根据上下文完成。模型越强，Skill 越应该轻量、清晰、可扩展，而不是用过时内容束缚模型。

## 安装

将本仓库中的 `skills/java-audit/` 整个目录放置到 Cloud 或 Codex 可识别的 `.skills/` 目录下，目录名保持为 `java-audit`：

```text
.skills/
└── java-audit/
    ├── SKILL.md
    ├── config.json
    ├── references/
    └── scripts/
```

## 如何使用

安装后，在支持 Skills 的 Cloud 或 Codex 环境中，可以用 `$java-audit` 显式触发；也可以用“审计这个 Java 项目”“梳理当前源码路由”“梳理鉴权信息”等自然语言触发。显式使用 `$java-audit` 更稳定。

```text
使用 /java-audit 审计 /path/to/project，只输出确认漏洞，并给出 payload 和 BurpSuite 原始 HTTP 请求包。
```

```text
使用 /java-audit 对 /path/to/app.war 先反编译再快速审计，所有工具、临时文件和报告都放到审计工作目录。
```

```text
使用 /java-audit 分析这个 Java diff 是否引入真实可利用漏洞；不能确认的内容放入高风险线索。
```

```text
使用 /java-audit 帮我梳理当前源码的路由信息，输出 Markdown 路由报告。
```

```text
使用 /java-audit 帮我梳理当前源码下的鉴权信息，包括认证机制、权限配置和路由鉴权映射。
```

```text
使用 /java-audit 帮我梳理当前源码下的是否存在SQL注入漏洞。
```

```text
使用 /java-audit 帮我梳理当前源码下的是否存在可以拿到shell权限的漏洞。
```

典型执行流程：

1. AI 识别输入类型：源码、JAR/WAR/class、反编译产物、模块、diff 或混合材料。
2. AI 创建审计工作目录，并把工具、反编译结果、日志、证据和报告都放进去；如果默认目录已存在，会使用随机前缀创建新目录。
3. 如果目标是 JAR/WAR/class，AI 下载 CFR 并通过 CLI 反编译。
4. AI 按用户意图选择报告类型：漏洞审计、路由信息梳理或鉴权信息梳理。
5. 如果是漏洞审计，AI 必须先梳理鉴权方式、放行规则、权限边界和路由鉴权状态，再从鉴权面选择审计切入点。
6. 漏洞审计必须识别 Java Web 组件暴露面，组件命中只用于驱动漏洞族初筛和候选生成，不能直接确认漏洞。
7. 漏洞审计必须运行组件漏洞命中扫描，命中进入 `workspace/evidence/component-hits/` 并完成归类处理。
8. 漏洞审计必须运行 Query Pack 检索源码和反编译产物，命中进入 `workspace/evidence/search-hits/` 并完成归类处理。
9. 漏洞审计必须将常见 Java 漏洞族列成内部初筛表逐项检查；每个 `[x]` 或 `[?]` 组件或漏洞族必须生成 `VULN-CAND-xxx` 候选、进入深度审计并形成闭环状态。
10. AI 生成最终报告前先运行 evidence 闭环校验；任一 `[x]`/`[?]` 没有候选、没有证据矩阵或状态仍为“候选”，或 component hits / search hits 仍有未处理命中时，必须返工；组件表和初筛表不得保留 `[ ]`。
11. AI 最终只把满足六项验收标准的内容写入“确认漏洞”；不得输出内部组件表、组件漏洞命中表、Query Pack 命中表、初筛表、证据矩阵或“漏洞不存在/已排除漏洞类型”清单。
12. AI 输出 Markdown 报告，并用报告校验脚本检查报告边界。

## 目录结构

```text
java-audit-skills/
├── README.md
├── assets/
└── skills/
    └── java-audit/
        ├── SKILL.md
        ├── config.json
        ├── references/
        └── scripts/
```

## 核心验收标准

一个漏洞只有同时满足以下六项，才能进入“确认漏洞”：

- 可达：存在明确外部入口。
- 可控：用户能控制关键参数。
- 可传播：存在 source-to-sink 传播链。
- 可利用：sink 语义能造成真实安全影响，且防护不足。
- 可复现：有 payload 和 BurpSuite 原始 HTTP 请求包。
- 影响成立：能说明具体安全影响。

缺少任一项时，只能写入“高风险线索 / 下一步人工验证”，不能硬报确认漏洞。

## CFR 反编译

默认 CFR 地址：

```text
https://xget.xi-xu.me/gh/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar
```

典型调用：

```bash
python3 skills/java-audit/scripts/init_audit_workspace.py --base /path/to/project
python3 skills/java-audit/scripts/fetch_cfr.py --workspace <init 输出的 workspace>
python3 skills/java-audit/scripts/decompile_with_cfr.py /path/to/app.war --workspace <init 输出的 workspace> --analyseas WAR
```

底层 CLI：

```bash
java -jar cfr-0.152.jar <target.jar|target.war|target.class> --outputdir <output-dir>
```

## 组件漏洞命中扫描

漏洞审计在组件暴露面识别后、Query Pack 前运行：

```bash
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <init 输出的 workspace>
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <init 输出的 workspace> --source /path/to/app.war
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <init 输出的 workspace> --source /path/to/WEB-INF/lib
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <init 输出的 workspace> --validate-rules
```

脚本复用 `skills/java-audit/references/java-vulnerability.yaml`，扫描 Maven/Gradle、JAR/WAR、`WEB-INF/lib` 和 Spring Boot fat jar 的 `BOOT-INF/lib`，生成 `workspace/evidence/component-hits/`。命中只是组件版本规则线索，必须被归类为生成候选、合并候选、低价值放弃、误报、不适用或防护阻断；未处理命中会导致 evidence 闭环校验失败。

## Query Pack 检索

漏洞审计在组件暴露面识别后、漏洞族初筛前运行：

```bash
python3 skills/java-audit/scripts/run_discovery_queries.py --validate-queries
python3 skills/java-audit/scripts/run_discovery_queries.py --workspace <init 输出的 workspace>
python3 skills/java-audit/scripts/run_discovery_queries.py --workspace <init 输出的 workspace> --source /path/to/source-or-decompiled
python3 skills/java-audit/scripts/run_discovery_queries.py --workspace <init 输出的 workspace> --queries skills/java-audit/references/discovery-query-pack.yaml
python3 skills/java-audit/scripts/run_discovery_queries.py --workspace <init 输出的 workspace> --engine python
python3 skills/java-audit/scripts/run_discovery_queries.py --workspace <init 输出的 workspace> --engine auto
python3 skills/java-audit/scripts/run_discovery_queries.py --list-groups
python3 skills/java-audit/scripts/run_discovery_queries.py --workspace <init 输出的 workspace> --group sql-mybatis --group ssrf-http-client
```

脚本默认加载 `skills/java-audit/references/discovery-query-pack.yaml` 并使用 Python 标准库递归扫描生成 `workspace/evidence/search-hits/`，不依赖 `rg`。维护检索规则时优先修改 YAML，并用 `--validate-queries` 校验字段和正则；不要把查询规则写回脚本。需要加速时，可用 `--engine auto` 自动优先使用 `rg`，或用 `--engine rg` 强制使用 `rg`。Query Pack v3 按入口、source、传播中间态、鉴权、SQL/JDBC/MyBatis/JPA、NoSQL、命令、表达式、模板、文件、SSRF、XML、LDAP、反序列化、XSS、凭据、密码学、TLS、CORS/CSRF、调试端点、日志、资源消耗和业务流程拆分查询组。命中只是候选线索，必须被归类为生成候选、合并候选、低价值放弃、误报、不适用或防护阻断；未处理命中会导致 evidence 闭环校验失败。

## 报告校验

生成报告后建议运行：

```bash
python3 skills/java-audit/scripts/validate_evidence_closure.py /path/to/java-audit-workspace
python3 skills/java-audit/scripts/validate_report.py /path/to/report.md --type vuln
python3 skills/java-audit/scripts/validate_report.py /path/to/route_report.md --type route
python3 skills/java-audit/scripts/validate_report.py /path/to/auth_report.md --type auth
```

`validate_evidence_closure.py` 会检查组件暴露面表、组件漏洞命中、Query Pack 命中和漏洞族初筛表中每个 `[x]`/`[?]` 是否生成候选、是否有证据矩阵、是否闭环为确认/降级/放弃，并禁止最终组件表或初筛表保留 `[ ]`、禁止 component hits / search hits 保留未处理命中。它只校验流程闭环，不判断漏洞真假。

报告校验器会检查章节、占位符和报告边界。漏洞报告会额外检查确认漏洞必填字段、BurpSuite 原始 HTTP 请求包，以及“疑似/待验证”内容是否误入确认漏洞区。
它还会拦截“漏洞不存在”“已排除漏洞类型”等枚举式否定结论，避免把内部假设证伪过程写进最终报告。

## 安全边界

本项目仅用于授权代码审计、企业内部安全评估、学习和研究。报告中的请求包应使用授权测试环境和占位凭据，不应包含真实敏感数据、生产环境凭据、批量利用脚本、持久化 payload、横向移动步骤或破坏性操作。
