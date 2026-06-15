---
name: java-audit
description: 当用户要求审计 Java 源码、JAR/WAR/class、反编译产物、Java Web 路由或安全发现，并需要默认脚本输出目录、报告输出目录、组件 YAML 正则匹配扫描、CFR 反编译工具下载/使用、确认漏洞判定标准、安全 Payload 和 BurpSuite 原始 HTTP 请求包证据时使用。仅用于授权 Java 代码审计和防御性安全验证。
---

# Java 审计

## 1. 默认输出目录

未指定目录时，先创建 `<目标目录>/java-audit-workspace/` 作为审计工作目录。

- 默认临时脚本输出目录：`<审计工作目录>/script-output/`
- 报告输出目录：`<审计工作目录>/reports/`
- 工具目录：`<审计工作目录>/tools/`
- 反编译目录：`<审计工作目录>/decompiled/`

所有脚本执行结果、临时扫描结果、命令输出、日志和中间证据都写入 `script-output/`；最终可交付报告只写入 `reports/`，默认文件名为 `java-audit-report.md`。

## 2. 组件 YAML 正则匹配扫描

需要从依赖、源码、JAR/WAR、`WEB-INF/lib` 或部署目录中发现组件版本风险时，使用内置组件扫描资源。

- 脚本：`skills/java-audit/scripts/run_component_vulnerability_scan.py`
- 规则：`skills/java-audit/references/java-vulnerability.yaml`
- 规则机制：YAML 中按严重等级维护组件名和版本正则；脚本解析 Maven/Gradle、JAR/WAR、部署目录和依赖文件后，用这些正则匹配组件版本命中。
- 命中输出：`<审计工作目录>/evidence/component-hits/`
- 日志输出：需要保留命令日志时，写入 `<审计工作目录>/script-output/`

先校验 YAML 正则：

```bash
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <审计工作目录> --validate-rules
```

扫描默认候选源：

```bash
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <审计工作目录>
```

指定一个或多个扫描源：

```bash
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <审计工作目录> --source <源码目录|依赖目录|目标.jar|目标.war|WEB-INF/lib>
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <审计工作目录> --source <源1> --source <源2>
```

使用自定义规则文件：

```bash
python3 skills/java-audit/scripts/run_component_vulnerability_scan.py --workspace <审计工作目录> --rules <自定义java-vulnerability.yaml>
```

组件命中只能作为线索；不能仅凭组件名、版本或 CVE 命中确认漏洞，必须继续证明入口、可控参数、传播链、可利用性、Payload 和 BurpSuite 请求包。

## 3. CFR 反编译工具下载及使用

默认使用 CFR 0.152。

- 下载地址：`https://xget.xi-xu.me/gh/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar`
- 保存位置：`<审计工作目录>/tools/cfr-0.152.jar`
- 反编译输出：统一放到 `<审计工作目录>/decompiled/`，不要覆盖源码目录。
- 使用策略：有源码时优先审源码；只有 JAR/WAR/class 或缺失关键代码时再反编译。

下载命令：

```bash
mkdir -p <审计工作目录>/tools
curl -L -o <审计工作目录>/tools/cfr-0.152.jar https://xget.xi-xu.me/gh/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar
```

基础用法：

```bash
java -jar <审计工作目录>/tools/cfr-0.152.jar <目标.jar|目标.class> --outputdir <审计工作目录>/decompiled/<目标名>
```

WAR 包用法：

```bash
java -jar <审计工作目录>/tools/cfr-0.152.jar <目标.war> --analyseas WAR --outputdir <审计工作目录>/decompiled/<目标名>
```

聚焦包名或类名：

```bash
java -jar <审计工作目录>/tools/cfr-0.152.jar <目标.jar> --jarfilter '<包名或类名正则>' --outputdir <审计工作目录>/decompiled/<目标名>
```

## 4. 如何判定漏洞有效

只有同时满足以下标准，才能把发现写成“确认漏洞”：

- 可达：存在真实外部入口，例如 HTTP 路由、Servlet、Filter、Controller、RPC、WebService、上传处理入口等。
- 可控：能指出用户可控参数、参数来源、绑定方式，以及参数进入代码的准确位置。
- 可传播：存在清晰的 source-to-sink 文件/方法级调用链，且中途没有有效鉴权、校验、编码、白名单或类型约束阻断。
- 可利用：sink 的语义在当前项目上下文中能造成真实安全影响。
- 可复现：必须有构造的安全 Payload，并提供可直接放入 BurpSuite Repeater 的原始 HTTP 请求包。
- 影响成立：能说明触发后产生的越权、泄露、绕过、写入或其他安全影响。

任一标准缺失时，只能写为“高风险线索 / 待人工验证”，不得写入“确认漏洞”。

每个确认漏洞必须包含：

```text
标题:
严重等级:
受影响入口:
鉴权要求:
用户可控输入:
Source-to-sink 调用链:
Sink:
防护判断:
安全 Payload:
BurpSuite 原始请求包:
影响:
证据文件和行号:
限制说明:
```

BurpSuite 原始请求包必须完整到可直接粘贴进 Repeater：

```http
POST /<授权测试路径> HTTP/1.1
Host: <授权测试主机>
Content-Type: application/x-www-form-urlencoded
Connection: close

<参数名>=<安全证明Payload>
```

## 安全边界

- 不准输出破坏性 Payload。
- 不准包含删除文件、修改配置、删除/清空/截断数据库、擦除表数据、写入持久化后门、反弹 shell、窃取敏感数据或横向移动的 Payload。
- 只使用无害证明 Payload，例如只读验证、布尔差异、受控回显标记，或针对非敏感测试记录的越权证明。
- Host、Cookie、凭据、ID、敏感值默认使用占位符；除非用户明确提供授权测试值。
- 如果漏洞必须依赖破坏性操作才能证明，只能写为高风险线索，并说明缺失的非破坏性验证路径。
