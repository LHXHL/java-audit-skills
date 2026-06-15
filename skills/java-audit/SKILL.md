---
name: java-audit
description: 当用户要求审计 Java 源码、JAR/WAR/class、反编译产物、Java Web 路由或安全发现，并需要 CFR 反编译工具下载/使用、确认漏洞判定标准、安全 Payload 和 BurpSuite 原始 HTTP 请求包证据时使用。仅用于授权 Java 代码审计和防御性安全验证。
---

# Java 审计

## 1. CFR 反编译工具下载及使用

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

## 2. 如何判定漏洞有效

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
