# Java Audit Skill

本仓库提供一个中文 `java-audit` Skill，用于标准化 Java 快速漏洞审计的流程、工程目录、反编译工具调用、证据门槛和 Markdown 报告格式。

新版不再维护旧的多 Skill 体系，也不把路由枚举、组件扫描或专项漏洞知识拆成多个入口。`java-audit` 的核心职责是让 AI 在审计具体 Java 目标时保持稳定流程：先建立工作目录，必要时用 CFR 反编译，再基于代码证据确认漏洞，最后输出可复现的报告。

## 适用场景

- 审计 Java 源码目录、单模块、JAR/WAR/class、反编译产物、diff 或混合材料。
- 快速寻找真实可利用漏洞，只输出满足证据门槛的确认漏洞。
- 需要 payload 和 BurpSuite Repeater 可用的原始 HTTP 请求包。
- 需要把工具、临时脚本、反编译结果、证据、日志和报告统一放入审计工作目录。

## 不适用场景

- 只整理路由清单或接口文档。
- 只解释 Java 代码、修业务 bug 或写安全培训材料。
- 只生成 Semgrep/CodeQL/规则库。
- 对非授权线上目标发起扫描、爆破或破坏性验证。

## 目录结构

```text
java-audit-skills/
├── README.md
├── assets/
└── skills/
    └── java-audit/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
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
python3 skills/java-audit/scripts/fetch_cfr.py --workspace /path/to/project/java-audit-workspace
python3 skills/java-audit/scripts/decompile_with_cfr.py /path/to/app.war --workspace /path/to/project/java-audit-workspace --analyseas WAR
```

底层 CLI：

```bash
java -jar cfr-0.152.jar <target.jar|target.war|target.class> --outputdir <output-dir>
```

## 报告校验

生成报告后建议运行：

```bash
python3 skills/java-audit/scripts/validate_report.py /path/to/report.md
```

校验器会检查章节、占位符、确认漏洞必填字段、BurpSuite 原始 HTTP 请求包，以及“疑似/待验证”内容是否误入确认漏洞区。

## 安全边界

本项目仅用于授权代码审计、企业内部安全评估、学习和研究。报告中的请求包应使用授权测试环境和占位凭据，不应包含真实敏感数据、生产环境凭据、批量利用脚本、持久化 payload、横向移动步骤或破坏性操作。
