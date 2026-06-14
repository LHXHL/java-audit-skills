# Java Audit Skill

本仓库提供一个中文 `java-audit` Skill，用于标准化 Java 快速漏洞审计、路由信息梳理、鉴权信息梳理的流程、工程目录、反编译工具调用、证据门槛和 Markdown 报告格式。

新版不再维护旧的多 Skill 体系，也不把路由枚举、鉴权梳理、组件扫描或专项漏洞知识拆成多个入口。`java-audit` 的核心职责是让 AI 在处理具体 Java 目标时保持稳定流程：先建立工作目录，必要时用 CFR 反编译，再按用户意图输出漏洞、路由或鉴权报告。

## 适用场景

- 审计 Java 源码目录、单模块、JAR/WAR/class、反编译产物、diff 或混合材料。
- 快速寻找真实可利用漏洞，只输出满足证据门槛的确认漏洞。
- 梳理当前源码的路由信息、接口入口、Handler、参数和证据位置。
- 梳理当前源码的鉴权信息、认证授权机制、权限配置和路由鉴权映射。
- 需要 payload 和 BurpSuite Repeater 可用的原始 HTTP 请求包。
- 需要把工具、临时脚本、反编译结果、证据、日志和报告统一放入审计工作目录。

## 前言

随着 AI 尤其是大模型的快速发展，模型能力几乎每隔一段时间就会发生明显变化，这也要求 Skill 必须持续更新。如果 Skill 仍然沿用旧模型时代的写法，堆叠大量细节、固定流程和过度说明，反而会限制新模型的理解、推理和发挥。

因此，现在的 Skill 更应该偏向“架构化设计”，而不是“说明书式堆内容”。它只需要明确目标、边界、原则、工具和关键流程，把具体判断和执行交给模型根据上下文完成。模型越强，Skill 越应该轻量、清晰、可扩展，而不是用过时内容束缚模型。


## 如何使用

在支持 Skills 的环境中，直接用 `$java-audit` 指向具体 Java 目标，并说明你需要“快速审计”“确认漏洞”“路由信息”“鉴权信息”“payload”或“BurpSuite 原始请求包”。

```text
使用 $java-audit 审计 /path/to/project，只输出确认漏洞，并给出 payload 和 BurpSuite 原始 HTTP 请求包。
```

```text
使用 $java-audit 对 /path/to/app.war 先反编译再快速审计，所有工具、临时文件和报告都放到审计工作目录。
```

```text
使用 $java-audit 分析这个 Java diff 是否引入真实可利用漏洞；不能确认的内容放入高风险线索。
```

```text
使用 $java-audit 帮我梳理当前源码的路由信息，输出 Markdown 路由报告。
```

```text
使用 $java-audit 帮我梳理当前源码下的鉴权信息，包括认证机制、权限配置和路由鉴权映射。
```

典型执行流程：

1. AI 识别输入类型：源码、JAR/WAR/class、反编译产物、模块、diff 或混合材料。
2. AI 创建审计工作目录，并把工具、反编译结果、日志、证据和报告都放进去；如果默认目录已存在，会使用随机前缀创建新目录。
3. 如果目标是 JAR/WAR/class，AI 下载 CFR 并通过 CLI 反编译。
4. AI 按用户意图选择报告类型：漏洞审计、路由信息梳理或鉴权信息梳理。
5. 如果是漏洞审计，AI 必须先梳理鉴权方式、放行规则、权限边界和路由鉴权状态，再从鉴权面选择审计切入点。
6. 漏洞审计可使用漏洞假设库做内部推导，但最终只把满足六项验收标准的内容写入“确认漏洞”；不得输出“漏洞不存在/已排除漏洞类型”清单。
7. AI 输出 Markdown 报告，并用校验脚本检查报告边界。

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

## 报告校验

生成报告后建议运行：

```bash
python3 skills/java-audit/scripts/validate_report.py /path/to/report.md --type vuln
python3 skills/java-audit/scripts/validate_report.py /path/to/route_report.md --type route
python3 skills/java-audit/scripts/validate_report.py /path/to/auth_report.md --type auth
```

校验器会检查章节、占位符和报告边界。漏洞报告会额外检查确认漏洞必填字段、BurpSuite 原始 HTTP 请求包，以及“疑似/待验证”内容是否误入确认漏洞区。
它还会拦截“漏洞不存在”“已排除漏洞类型”等枚举式否定结论，避免把内部假设证伪过程写进最终报告。

## 安全边界

本项目仅用于授权代码审计、企业内部安全评估、学习和研究。报告中的请求包应使用授权测试环境和占位凭据，不应包含真实敏感数据、生产环境凭据、批量利用脚本、持久化 payload、横向移动步骤或破坏性操作。
