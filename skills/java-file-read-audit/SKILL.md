---
name: java-file-read-audit
description: 当用户要求审计 Java 源码、字节码或 pipeline 证据中的任意文件读取、路径遍历、文件下载、FileInputStream/Files/Resource/InputStream 文件读取 sink，或需要判断外部参数是否能控制读取路径时使用；只做路由枚举、调用链追踪、文件上传、SQL、XXE、反序列化、鉴权或组件 CVE 扫描时不要使用。
---

# Java File Read Audit

## 当前定位

`java-file-read-audit` 是 Java 审计技能集中的任意文件读取和路径遍历专项判定层。它消费源码、反编译结果、`java-route-mapper` 路由清单或 `java-route-tracer` 调用链证据，判断：

- 是否存在真实文件读取、下载、模板/资源读取或流式返回 sink。
- 外部输入是否影响文件名、相对路径、绝对路径、资源 key、下载 ID 或 URL。
- 路径是否被白名单、canonical/normalize、ID 映射、扩展名和基础目录约束保护。
- 结论应标为确认漏洞、条件成立、待验证、不可确认还是非漏洞。
- 确认漏洞或条件成立项是否能提供 Burp Suite 请求和路径 payload 给开发单位复核。

本 skill 不负责全量路由枚举，不替代调用链追踪，不判断文件上传写入漏洞，不扫描依赖 CVE，不输出未验证的系统文件读取成功结论。

## 上下游边界

上游输入可以是：

- 用户指定的 Java 项目路径、路由、类、方法、下载接口或文件读取代码片段。
- `java-route-mapper` 产出的路由、参数和入口方法清单。
- `java-route-tracer` 产出的调用链、可控性、分支条件和 FILE sink 候选。
- 源码不可用时的 `.class`、`.jar`、`.war` 或已有反编译结果。

下游通常读取：

- 文件读取审计报告。
- 受影响入口、可控路径、文件读取 sink、防护缺口和限制说明。
- 确认漏洞或条件成立项的 Burp Suite 请求和路径 payload。
- 待验证或不可确认项的补证清单。

相邻 skill 边界：

- `java-route-mapper`：枚举路由和入口参数；本 skill 只消费其结果。
- `java-route-tracer`：追踪参数到 FILE sink；本 skill 只在需要数据流证据时读取或请求调用链追踪。
- `java-file-upload-audit`：处理上传、任意文件写入、上传路径穿越；本 skill 只处理读取。
- `java-xxe-audit`：处理 XML 解析读本地文件；本 skill 只在 XML 外部实体以外的普通文件读取 sink 中判定。
- `java-auth-audit`：判断鉴权和越权；本 skill 只引用鉴权上下文，不扩写成鉴权漏洞。
- `java-vuln-scanner`：扫描依赖组件 CVE；本 skill 不编造 CVE、CVSS 或修复版本。

## 触发条件

满足任一条件时触发：

- 用户明确要求审计任意文件读取、路径遍历、目录遍历、文件下载、读取本地文件、读取配置文件或资源文件泄露。
- 代码或上游证据出现 `FileInputStream`、`FileReader`、`Files.read*`、`ResourceUtils`、`ClassPathResource`、`ServletContext#getResourceAsStream`、`response.getOutputStream` 下载链路等 FILE sink。
- `java-route-tracer` 已报告 FILE sink 证据，需要做安全结论和可复核交付。
- 源码缺失但字节码中可能包含下载 Controller、文件 Service、资源读取工具类，需要反编译后审计。
- 用户给出候选代码片段，要求判断参数是否能穿越目录或读取敏感文件。

## 不触发条件

以下情况不要触发本 skill：

- 只要求列出 Java Web 路由、Controller、Servlet 或 WebService operation。
- 只要求追踪参数调用链，不要求判断文件读取漏洞。
- 只审计上传保存、任意文件写入、覆盖文件或 WebShell 上传。
- 只审计 SQL、XXE、反序列化、SSRF、命令执行、鉴权或组件 CVE。
- 文件路径完全由服务端常量、闭合 ID 映射或不可控配置决定，且用户不能影响目标文件。
- 用户要求批量读取线上目标文件、未授权攻击、敏感文件内容回显或破坏性验证。

## 成功标准

合格输出必须同时满足：

- 每个结论都有入口、可控参数、数据流、真实文件读取 sink、防护状态和代码位置。
- 不把候选风险、缺失实现、未反编译类、静态资源正常访问或单独的 `fileName` 命中写成已确认漏洞。
- 明确区分确认漏洞、条件成立、待验证、不可确认和非漏洞。
- 对 canonical/normalize、基础目录、ID 映射、白名单、扩展名、黑名单、URL 解码和执行条件给出证据。
- 同根因多入口按相同 sink、相同防护缺口、相同修复点聚合；不同鉴权、不同基础目录、不同参数来源或不同证据等级拆分。
- 报告严格使用 `references/OUTPUT_TEMPLATE.md` 的 6 个编号章节，不添加输出自检、技能源校验、测试提示词或模型验收信息。
- 确认漏洞或条件成立项必须包含 Burp Suite 请求和 payload；待验证、不可确认和非漏洞项不得输出可复制请求。
- 第 5 节只允许写确认漏洞或条件成立的风险详情；待验证、不可确认和非漏洞只能放在第 4 节和第 6 节。
- 面向用户的最终对话回复只给报告路径和一句简短结论，不列发现详情、不引用 hard rule 编号、不输出后续工具建议。
- 不编造 CVE、CVSS、修复版本、文件读取成功、系统类型、真实敏感文件内容或不存在的代码路径。

## 工作流

1. 确定审计范围：读取用户路径、候选入口、上游 route/tracer 报告和已有反编译结果。
2. 选择 references：sink 识别读 `FILE_READ_METHODS.md`；路径遍历读 `PATH_TRAVERSAL.md`；源码缺失读 `DECOMPILE_STRATEGY.md`；验证材料读 `VALIDATION_MATERIALS.md`；生成报告读 `OUTPUT_TEMPLATE.md`。
3. 定位 FILE sink：优先找真实读取 API、下载输出流和资源读取方法，而不是只看类名或参数名。
4. 追踪可控性：从 HTTP/RPC/SOAP/MQ 参数、JSON 字段、Header、Cookie、路径变量、数据库字段或上游对象追踪到读取路径。
5. 判断防护：检查基础目录、规范化、白名单、ID 映射、扩展名校验、黑名单替换、URL 解码和路径分隔符处理。
6. 需要深度调用链时切换到 `java-route-tracer`；没有入口或调用链证据时只能输出待验证/不可确认。
7. 生成报告：确认/条件成立项按 `VALIDATION_MATERIALS.md` 输出 Burp Suite 请求和 payload；其他状态只写补证路径。
8. 输出后可运行 `scripts/validate_file_read_output.py <输出目录>` 做硬边界检查，再人工检查证据链。

## Hard Rules

1. 没有真实文件读取、下载或资源读取 sink，不得下任意文件读取结论。
2. 没有用户可控路径、文件名、资源 key、下载 ID 或可影响路径的数据库字段，不得下漏洞结论。
3. 没有证据证明防护缺失或不足，不得下漏洞结论。
4. `java-route-tracer` 的 `UNCONFIRMED`、Service/Util 方法名、`download` 命名只表示待查，不是 FILE sink。
5. `new File(base, fileName)` 不天然危险；必须看 `fileName` 可控性和 canonical/normalize 后是否限制在 base 内。
6. 扩展名白名单不是完整路径防护；若缺 canonical/normalize 和目录约束，仍可能条件成立。
7. 黑名单替换、去掉 `../`、只判断 `contains("..")` 不是充分防护；需要检查编码、双重编码、反斜杠和绝对路径。
8. ID 到服务端路径的闭合映射通常不是文件读取漏洞；除非用户能控制映射结果或绕过授权访问他人文件。
9. classpath 资源读取、模板读取、静态文件访问、下载固定帮助文档通常不是漏洞；除非外部输入影响资源路径并可越界。
10. 确认漏洞和条件成立项必须给 Burp Suite 请求和 payload；待验证、不可确认、非漏洞项不得给可复制请求。
11. Burp 请求必须匹配真实入口、HTTP 方法、参数名和 Content-Type；无法确认入口时不得编造请求。
12. payload 只用于授权测试环境低风险复核，必须使用占位符，不得包含批量读取、真实敏感文件内容、生产路径、系统敏感路径或破坏性动作。
13. 不编造 CVE、CVSS、修复版本、操作系统、容器路径、读取成功结果或未读取过的文件内容。
14. 反编译证据必须指向真实存在的源码文件、反编译输出文件或 class/JAR 来源；只有“应当存在”的推断不得作为确认漏洞证据。
15. 正式报告不得出现 `## 输出自检`、技能源校验、测试提示词、Claude 运行状态、验收清单、内部工具错误、具体工具不可用信息或固定占位时间。
16. 结论状态必须使用中文枚举：确认漏洞、条件成立、待验证、不可确认、非漏洞。
17. 只有 class 名、方法名、字段名、常量池字符串或“未发现 canonical/normalize 字符串”时，不得写确认漏洞或条件成立；必须取得方法体、调用链或上游可验证证据后才能升格。
18. 面向用户的最终回复只说明报告路径和简短结论，不输出报告质量自检、审批/权限提示、内部校验脚本、工具不可用过程、hard rule 编号、额外漏洞摘要或后续工具建议。
19. 只有 `ServletOutputStream`、`addHeader`、`setContentType` 或下载命名，不得作为 FILE sink 映射行；必须同时能指向文件/资源 `InputStream` 来源，否则放在第 4 节非 sink 候选或不写入主报告。

## Gotchas

- 参数名叫 `file`、`path`、`url` 不等于可控文件读取；必须追到读取 sink。
- 只有响应输出流不等于文件读取；必须确认输出流的数据来源是文件、资源或可控本地路径。
- 下载接口返回数据库 BLOB、对象存储 key 或文件 ID，不等于本地文件读取。
- 只读 `classpath:` 固定资源通常不是任意文件读取。
- `getCanonicalPath()` 后必须和规范化后的 base 比较；只对原始字符串比较容易绕过。
- `startsWith(basePath)` 如果 basePath 未加路径边界，`/var/upload2` 可能绕过 `/var/upload`。
- `URLDecoder.decode` 的次数会影响 payload；不要在未确认解码链时写确认漏洞。
- Windows 与 Linux 分隔符不同；无法确认部署系统时写条件成立或待验证，不要编造目标系统。
- 反编译失败只能说明待验证或不可确认，不是漏洞。
- 常量池、字符串提取或方法签名只能证明“可能存在入口或 sink”，不能证明防护缺失。
- 待验证项输出 Burp 请求会把候选包装成漏洞，属于不合格。
- 确认漏洞没有 Burp 请求和 payload，会缺少开发单位复核材料，属于不合格。
- 条件成立不是“缺证但看起来危险”；它必须有真实入口、可控输入、文件读取 sink、方法体级防护缺口和明确环境条件。

## 停止、确认或切换条件

- 找不到实现源码、读取 sink 或可用反编译结果时：停止确认漏洞，输出不可确认和缺失证据。
- 只有 `.class` 常量、字段、方法签名、JSP 拼接或配置映射，未取得关键方法体时：停止在待验证/不可确认，不生成 Burp 请求和 payload。
- 缺入口参数或调用链时：切换到 `java-route-tracer`，完成证据后再回来判定。
- 需要判断接口是否只有管理员可访问、是否 IDOR 或越权时：交给 `java-auth-audit`，本 skill 只引用其结果。
- 用户要求上传写入或 WebShell 风险时：交给 `java-file-upload-audit`。
- 用户要求组件 CVE、版本漏洞或修复版本时：交给 `java-vuln-scanner`。
- 用户要求实际读取线上敏感文件、批量扫描或未授权利用时：拒绝该部分，只保留静态审计和授权环境低风险复核建议。

## Eval

| 类型 | 用户请求或场景 | 预期行为 |
|------|----------------|----------|
| 正例 | “审计这个项目有没有任意文件读取。” | 触发，定位入口到 FILE sink 并判定 |
| 正例 | “这个 download 接口的 fileName 会不会路径遍历？” | 触发，分析参数、路径拼接和校验 |
| 正例 | “route-tracer 说参数到达 FileInputStream，判断是否成立。” | 触发，读取 tracer 证据和文件读取规则 |
| 反例 | “提取所有 Controller 路由。” | 不触发，使用 `java-route-mapper` |
| 反例 | “上传接口能不能写 JSP？” | 不触发，使用 `java-file-upload-audit` |
| 反例 | “XXE 能不能读 /etc/passwd？” | 不触发，使用 `java-xxe-audit` |
| 边界例 | 下载参数是 fileId，服务端从数据库查固定路径 | 通常非漏洞或待验证，不能直接按路径遍历处理 |
| 边界例 | `new File(base, fileName)` 后有 canonical 校验 | 若校验完整，判非漏洞 |
| 边界例 | 只有 `.class` 类名疑似下载接口，未反编译 | 不确认，写不可确认/待验证 |
| 失败案例 | 把所有 `fileName` 参数都写成确认漏洞 | 不合格，缺 sink 和数据流 |
| 失败案例 | 待验证项输出 Burp 请求 | 不合格，候选被包装成漏洞 |
| 失败案例 | 输出 CVSS、CVE、修复版本、输出自检、工具不可用过程或 `000000` 占位时间 | 不合格，违反边界 |
