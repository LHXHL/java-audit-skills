## 审计 skills 系列

- [net-audit-skills](https://github.com/RuoJi6/net-audit-skills) - .NET / ASP.NET 代码审计 Claude Skills 集合

## 推荐阅读

- [Skill 约束悖论](https://ruoji6.github.io/posts/14856.html) - 理解 skill 在 AI 代码审计中的能力边界，以及全量自主审计与自主式深度推理的配合方式

# Java Audit Skills

Java Audit Skills 是一组面向 Java Web 代码审计的 Claude Skills。新版技能集按“入口面、证据层、专项判定、组件证据、流水线编排”重新拆分，目标不是让单个 skill 包办所有结论，而是让每个 skill 在清晰边界内产出可复核证据。

适合用于：

- 从源码、WAR、class、JAR 或反编译目录中梳理 Java Web 入口面。
- 建立路由、参数、鉴权、组件版本、调用链和 sink 之间的证据关系。
- 对 SQL 注入、XXE、文件上传、文件读取、反序列化、认证授权问题做专项审计。
- 在具备真实多 agent 调度能力时，编排完整 Java Web 安全审计流水线。

不适合用于：

- 未授权线上攻击、批量扫描真实目标或生成破坏性利用材料。
- 只凭组件版本、方法名、参数名或字符串命中直接确认业务漏洞。
- 把 route-tracer 的 sink 证据、vuln-scanner 的 CVE 命中或 validator 的检查结果包装成漏洞结论。

## 新版分层

| 层级 | Skill | 职责 |
|---|---|---|
| 入口面数据底座 | `java-route-mapper` | 提取真实可达路由、入口方法、参数结构和 WebService/SOAP 方法 |
| 调用链证据层 | `java-route-tracer` | 从已知入口追踪参数到 SQL/FILE/XML/COMMAND/HTTP/DESERIALIZE 等 sink |
| 认证授权专项 | `java-auth-audit` | 判断认证、授权、路由鉴权覆盖、绕过、权限提升和 IDOR |
| 漏洞专项判定 | `java-sql-audit`、`java-xxe-audit`、`java-file-upload-audit`、`java-file-read-audit`、`java-deserialization-audit` | 基于入口、调用链和代码证据做专项结论，并为确认项输出授权验证材料 |
| 组件版本证据层 | `java-vuln-scanner` | 提取依赖版本，匹配本地规则库，输出版本命中和触发面交接方向 |
| 编排与质检层 | `java-audit-pipeline` | 调度多 agent 流水线、阶段门禁、返工、QA 报告和最终质量报告 |
| 共享规则 | `java-shared` | 反编译策略、输出标准、漏洞聚合、严重性参考等共享资料 |

## 快速选择

| 你想做什么 | 使用 |
|---|---|
| 列出所有 Controller、Servlet、Struts、JAX-RS、WebService 入口和参数 | `java-route-mapper` |
| 追踪某条路由参数是否传到 SQL、文件、XML、反序列化或命令等 sink | `java-route-tracer` |
| 判断接口是否未授权、鉴权绕过、水平越权或垂直越权 | `java-auth-audit` |
| 判断 JDBC/MyBatis/Hibernate/JPA 动态 SQL 是否可注入 | `java-sql-audit` |
| 判断 MultipartFile、Part、Commons FileUpload 等上传链路是否危险 | `java-file-upload-audit` |
| 判断下载、预览、资源读取或 FileInputStream/Files 链路是否路径遍历 | `java-file-read-audit` |
| 判断 XML/SOAP/JAXP/dom4j/StAX/JAXB/XStream XML 解析是否有 XXE | `java-xxe-audit` |
| 判断 ObjectInputStream、XMLDecoder、Fastjson、XStream、Shiro RememberMe、Log4j/JNDI 或 gadget 链是否可利用 | `java-deserialization-audit` |
| 扫描 pom.xml、build.gradle、WEB-INF/lib 或 JAR 的组件版本命中 | `java-vuln-scanner` |
| 需要 route/auth/vuln/tracer/专项审计一起跑，并由独立 QA 做阶段门禁 | `java-audit-pipeline` |

## 目录结构

```text
java-audit-skills/
├── README.md
├── assets/
├── skills/
│   ├── README.md
│   ├── java-shared/
│   ├── java-route-mapper/
│   ├── java-route-tracer/
│   ├── java-auth-audit/
│   ├── java-sql-audit/
│   ├── java-file-upload-audit/
│   ├── java-file-read-audit/
│   ├── java-xxe-audit/
│   ├── java-deserialization-audit/
│   ├── java-vuln-scanner/
│   └── java-audit-pipeline/
└── tools/
    └── skill-maintenance/
        ├── README.md
        └── validators/
```

## 前置要求

- Java 运行环境：用于反编译或辅助分析时执行 Java 工具。
- CFR 反编译器：源码缺失、class-heavy 项目或部署包审计时按需使用。详细策略见 `skills/java-shared/DECOMPILE_STRATEGY.md`。
- 完整流水线：需要当前运行环境具备真实 Claude team / 多 agent 调度能力。若环境不能创建、等待或质检独立 agent，`java-audit-pipeline` 应写入阻塞报告，而不是顺序模拟完整流水线。

## 安装

将 `skills/` 下需要的 skill 目录复制或链接到 Claude Code 的 skills 配置目录中。每个 skill 都以自己的 `SKILL.md` 为加载入口，`references/` 中存放按需读取的规则、模板和细节。

运行期脚本保留在对应 skill 的 `scripts/` 下；维护和回归检查脚本位于 `tools/skill-maintenance/validators/`，不要把 validator 结果写入正式审计报告。

## 使用示例

单项技能：

```text
/java-route-mapper /path/to/project
/java-route-tracer --route /api/user/list --project /path/to/project
/java-auth-audit /path/to/project
/java-sql-audit /path/to/project
/java-file-upload-audit /path/to/project
/java-file-read-audit /path/to/project
/java-xxe-audit /path/to/project
/java-deserialization-audit /path/to/project
/java-vuln-scanner /path/to/project
```

完整流水线：

```text
/java-audit-pipeline /path/to/project --output /path/to/project_audit
```

流水线会按阶段产出路由、鉴权、组件版本、交叉分析、调用链、专项审计、QA 报告和最终质量报告。它只负责编排与门禁，漏洞判定仍由对应子 skill 完成。

![java-audit-pipeline 运行演示](assets/WechatIMG5173.jpg)

## 输出约定

默认输出目录为 `{project_name}_audit/`：

```text
{project_name}_audit/
├── route_mapper/
├── auth_audit/
├── vuln_report/
├── cross_analysis/
├── route_tracer/
├── sql_audit/
├── xxe_audit/
├── file_upload_audit/
├── file_read_audit/
├── deserialization_audit/
├── qa_reports/
├── decompiled/
├── quality_report.md
└── pipeline_blocked.md
```

专项漏洞 skill 统一区分：

- `确认漏洞`
- `条件成立`
- `待验证`
- `不可确认`
- `非漏洞`

组件扫描 skill 使用：

- `版本命中`
- `触发面待核查`
- `环境条件待确认`
- `不可确认`
- `未命中`

只有 `确认漏洞` 和 `条件成立` 项可以输出绑定真实入口的 Burp Suite 请求和低破坏 payload。`待验证`、`不可确认`、`非漏洞` 不输出可复制验证材料。

## 维护说明

维护规则见 `tools/skill-maintenance/README.md`。提交前建议至少执行：

```bash
python3 -m py_compile tools/skill-maintenance/validators/*.py
git diff --check
git status --short
```

如果修改了某个 skill 的运行期脚本，也应对对应脚本做语法检查或等价回归检查。

## 安全边界

本项目仅用于授权代码审计、企业内部安全评估、学习和研究。报告中的验证材料应绑定真实入口、占位凭据和授权测试环境，不应包含真实敏感数据、生产环境请求、批量利用脚本、持久化 payload、横向移动步骤或破坏性操作。

## 交流

需要进群可将微信号发送到 `asdnnj32nsd@foxmail.com`，由维护者邀请加入。

## 代码审计培训推荐

![代码审计培训推荐](assets/WechatIMG3380.jpg)

## 相关链接

- [CFR Decompiler](https://github.com/leibnitz27/cfr) - Java 反编译器
- [Claude Code](https://claude.ai/claude-code) - Claude CLI 工具
