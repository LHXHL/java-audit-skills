---
name: java-file-upload-audit
description: 当用户要求审计 Java 源码、字节码或 pipeline 证据中的文件上传、MultipartFile、Part、Commons FileUpload、FileItem、上传保存路径、文件名处理、上传目录访问性、任意文件写入或上传路径穿越风险时使用；只做路由枚举、调用链追踪、文件读取、XXE、SQL、反序列化、鉴权或组件漏洞编号扫描时不要使用。
---

# Java File Upload Audit

## 当前定位

`java-file-upload-audit` 是 Java 审计体系中的文件上传专项判定层。它读取源码、字节码、反编译结果、配置、`java-route-mapper` 路由清单或 `java-route-tracer` 调用链证据，判断用户提供的文件内容、文件名或上传路径是否进入危险文件写入点，并区分：

- 确认漏洞
- 条件成立
- 待验证
- 不可确认
- 非漏洞

本 skill 不负责全量路由枚举，不替代调用链追踪，不做鉴权结论，不生成可执行后门样本、风险评分或组件漏洞编号结论。对已达到“确认漏洞”或“条件成立”的风险，报告必须给出可交付给开发单位的授权验证材料：真实入口绑定的 Burp Suite 请求和低破坏 Payload。

## 上下游边界

上游输入可以是：

- 用户指定的 Java 项目路径、Controller、Servlet、上传接口、上传工具类或 class/jar/war。
- `java-route-mapper` 产出的上传路由、HTTP 方法、参数类型、Content-Type 和表单字段。
- `java-route-tracer` 产出的上传参数到文件写入 sink 的调用链、分支条件和可控性。
- Spring MVC、Servlet、Struts、Commons FileUpload、JAX-RS、WebService、定时导入或后台管理代码中的文件接收证据。

下游通常读取：

- 文件上传审计报告。
- 上传点映射、保存路径、文件名来源、校验状态、Web 可访问性、执行条件和限制说明。
- 已确认或条件成立风险的授权验证 Burp Suite 请求、Payload、前置条件和预期现象。
- 需要交给 `java-route-tracer` 或 `java-auth-audit` 的证据缺口。

相邻 skill 边界：

- `java-route-mapper`：枚举上传路由和参数；本 skill 只消费路由证据。
- `java-route-tracer`：追踪上传参数、文件名、目录和写入 sink；本 skill 在证据不足时请求追踪，不凭方法名推断可控。
- `java-auth-audit`：判断上传入口鉴权、越权或未授权；本 skill 只记录鉴权上下文。
- `java-file-read-audit`：判断读取或下载任意文件；本 skill 只判断上传写入路径。
- `java-vuln-scanner`：扫描依赖组件漏洞编号；本 skill 不编造组件漏洞编号、风险评分或修复版本。

## 触发条件

满足任一条件时触发：

- 用户明确要求审计文件上传、任意文件上传、上传路径穿越、上传覆盖、上传目录可执行或上传校验绕过。
- 代码中出现 `MultipartFile`、`Part`、`ServletFileUpload`、`DiskFileItemFactory`、`FileItem`、`transferTo`、`item.write`、`Files.copy`、`FileOutputStream`、`IOUtils.copy` 等上传接收或写入模式。
- route-tracer 已报告请求文件、文件名或目录参数到达文件写入 sink，需要判断是否构成上传漏洞。
- 项目只有字节码，需要定位上传入口、保存路径和校验逻辑。
- 用户给出候选上传代码，要求判断类型校验、文件名处理、目录限制或 Web 可访问性是否安全。

## 不触发条件

以下情况不要触发本 skill：

- 只要求列出 Controller、Servlet、WebService 路由。
- 只要求追踪参数调用链，不要求判断上传风险。
- 只看到 `File`、`Path`、`InputStream` 或文件写入工具类，但没有外部上传内容、文件名或目录输入。
- 只审计文件下载、任意文件读取、日志写入、导出报表、SQL、XXE、反序列化、鉴权或组件版本。
- 文件内容由服务端生成，文件名和目录均由服务端固定且不可被请求影响。
- 用户要求生成可执行后门样本、持久化内容、横向移动、批量验证脚本，或要求在缺少真实入口/授权语境时生成攻击请求。

## 成功标准

合格输出必须同时满足：

- 每个结论都有入口或输入来源、文件内容来源、文件名来源、保存路径、写入 sink、校验逻辑和执行条件。
- 不把普通文件写入、服务端导出、模板生成、固定配置落盘或缓存写入误报为文件上传漏洞。
- 明确区分确认漏洞、条件成立、待验证、不可确认和非漏洞。
- “条件成立”必须有真实入口、上传内容、写入 sink、可观察弱防护点和实际影响路径；纯配置加固项、工具类缺陷、假设某个白名单失效、或单纯文件大小阈值过大，不得单独写成条件成立。
- 对文件名净化、路径规范化、目录限制、扩展名/Content-Type/魔数校验、大小限制、随机重命名、覆盖策略、Web 可访问性给出证据。
- 同根因多入口按 `../java-shared/VULNERABILITY_GROUPING.md` 聚合；不同保存目录、文件名来源、校验条件或权限条件拆分。
- 对“确认漏洞/条件成立”风险给出 Burp Suite 请求和 Payload，并明确鉴权、参数、文件名、文件内容、预期现象、清理要求和限制。
- 报告严格使用 `references/OUTPUT_TEMPLATE.md` 的 6 个编号章节，不新增额外章节。
- 不编造组件漏洞编号、风险评分、修复版本、可执行后门样本、验证成功结果、HTTP 响应或不存在的代码路径。

## 工作流

### 1. 确定审计范围

- 读取用户指定路径、候选入口、上游 route/tracer 报告和上传相关配置。
- 若没有入口证据，可做上传 sink 盘点，但结论只能是“待验证/不可确认/非漏洞”，不能写外部可利用。
- 若只有工具类名、`upload` 字样或 `UNCONFIRMED` sink，先定位实现源码、字节码或反编译结果。
- 上传点映射只列真实入口或可被外部触发的上传执行点；工具类、拦截器、第三方库、静态目录和配置文件只放第 4 节作为依据，不计入结论统计。

### 2. 选择 reference

- 上传识别和风险判定：读取 `references/UPLOAD_RULES.md`。
- 授权验证输出：读取 `references/VALIDATION_GUIDE.md`。
- 源码缺失或只给字节码：读取 `references/DECOMPILE_STRATEGY.md`。
- 生成报告前：读取 `references/OUTPUT_TEMPLATE.md`。

### 3. 定位上传入口和写入 sink

优先查找真实上传执行点：

- Servlet 3：`request.getParts()`、`request.getPart()`、`Part.write`、`Part.getInputStream`。
- Spring：`MultipartFile`、`getOriginalFilename`、`transferTo`、`getInputStream`。
- Commons FileUpload：`ServletFileUpload.parseRequest`、`FileItem.getName`、`FileItem.write`、`FileItem.getInputStream`。
- 通用写入：`Files.copy`、`Files.write`、`FileOutputStream`、`FileUtils.copyInputStreamToFile`、`IOUtils.copy`、`Channel.transferFrom`。
- Base64 或 JSON 上传：请求字符串解码后进入文件写入，也按上传候选处理。

### 4. 追踪文件名、目录和校验

- 文件名来源：`getOriginalFilename`、`Part.getSubmittedFileName`、`FileItem.getName`、请求参数、JSON 字段、服务端生成名。
- 目录来源：固定配置、`getRealPath`、请求参数、数据库字段、租户/用户目录、临时目录。
- 校验逻辑：扩展名白名单、Content-Type、魔数、MIME 探测、大小限制、重命名、路径规范化、目录前缀校验。
- 写入后状态：是否位于 Web 根目录、是否可被静态资源访问、是否可被应用解析执行、是否覆盖已有文件。
- 若跨层证据不足，切回 `java-route-tracer`；不要凭 `upload`、`saveFile`、`import` 等名称推断可控性。

### 5. 判定执行条件

- 确认安全检查必须发生在写入 sink 前，并作用于实际使用的文件名、目录和文件内容。
- 黑名单、仅 Content-Type、仅大小限制、仅非空检查、仅替换部分分隔符不能单独证明安全。
- 随机重命名降低文件名可控性，但不能替代类型/内容校验和目录隔离。
- 数据流缺入口、缺写入 sink、缺校验证据、缺目录证据或缺执行条件时，输出待验证或不可确认。

### 6. 输出报告

- 使用 `references/OUTPUT_TEMPLATE.md`。
- 对“确认漏洞/条件成立”项，按 `references/VALIDATION_GUIDE.md` 输出 Burp Suite 请求和 Payload。
- 对“待验证”项，只写证据缺口和补证方向，不输出 Burp Suite 请求或 Payload。
- 对“不可确认/非漏洞”项，不输出 Burp Suite 请求或 Payload。
- 对没有确认漏洞的审计，也要输出已检查上传点、候选风险、非漏洞依据、不可确认项和待补证据。

## Hard Rules

1. 没有外部文件内容、文件名或目录输入，不得下上传漏洞结论。
2. 没有真实文件写入 sink，不得下上传漏洞结论。
3. 没有证据证明校验缺失、不完整或顺序错误，不得下确认漏洞。
4. `UNCONFIRMED`、工具类名、拦截器名、上传目录字符串、`upload` 方法名、框架依赖或单个配置项只表示候选或加固点，不是漏洞。
5. 结论状态必须使用中文枚举：确认漏洞、条件成立、待验证、不可确认、非漏洞。
6. “确认漏洞/条件成立”必须输出绑定真实入口、参数和鉴权状态的 Burp Suite 请求与 Payload；不得只写泛化验证思路。
7. “待验证/不可确认/非漏洞”不得输出 Burp Suite 请求或 Payload，即使入口看起来可访问；只写需要补充的源码、反编译、route-tracer、鉴权或运行配置证据。
8. Burp Suite 请求和 Payload 只能用于授权验证，必须使用占位符表示主机、Cookie、CSRF、边界值和环境变量，不得声称测试结果已经达成。
9. 不输出可执行后门样本、持久化脚本、批量利用脚本、横向移动步骤或破坏性内容；文件内容 Payload 使用无害 marker。
10. 不编造组件漏洞编号、风险评分、修复版本、文件内容、HTTP 响应或验证结果。
11. 反编译证据必须指向真实存在且已读取的源码、反编译文件或 class/jar 来源；路径不存在时只能写不可确认。
12. 未取得反编译/反汇编结果时，报告只写“本轮未取得反编译/反汇编结果”以及因此缺少哪些代码证据；不得解释原因、环境、安装状态、权限、审批、申请、拒绝、拦截或工具许可。
13. 结论统计数量必须与上传点映射和风险详情一致；聚合时要写清映射行和风险详情的对应关系。
14. 报告文件名和生成时间必须使用真实运行时刻，不得使用 `000000`、`00:00:00` 或占位时间。
15. 报告全文禁止出现三个连续英文句点；无法完整确认时写中文“省略非关键字段”或限制说明。

## Gotchas

- `MultipartFile` 参数不等于漏洞；如果服务端生成随机文件名、目录不可访问且内容白名单充分，通常不是漏洞。
- 仅校验 `Content-Type` 或文件后缀不可靠，尤其当文件内容未校验或上传目录可执行时。
- `getOriginalFilename` 和 `FileItem.getName` 可能包含客户端路径、路径分隔符或特殊字符，必须看净化与规范化。
- `Paths.get(base, name).normalize()` 之后仍需确认最终路径在允许目录下。
- `getRealPath` 写入 Web 根目录通常提高风险，但是否可执行取决于容器映射、扩展名处理和静态资源配置。
- 上传后立刻解析、导入、解压或转码时，要同时检查二次写入、临时文件、压缩包路径穿越和清理逻辑。
- 文件导出、报表生成、图片缩略图生成通常不是上传入口，除非文件内容或文件名来自请求上传。
- 只看到 Struts `fileUpload` 拦截器缺少 `allowedTypes/allowedExtensions`，但没有 Action sink、后续自定义拦截器或保存目录证据时，最多写“待验证”，不要写“条件成立”。
- 黑名单、白名单、魔数和随机重命名并存时，不能因为黑名单覆盖范围有限就写条件成立；必须证明某条可达分支只依赖黑名单，或白名单/魔数未在写入前生效。
- 单纯 `maximumSize` 过大属于容量配置加固点；除非用户明确审计 DoS，且有未鉴权可达入口和临时目录影响证据，否则不要作为文件上传漏洞单独编号，也不要输出 Burp/Payload。
- 白名单包含 `zip`、Office、文本、图片、视频等业务类型，不等于上传漏洞；只有存在后续自动解析、可访问目录、类型混淆或内容校验缺失导致的实际影响时，才可写“条件成立”。
- 只有前端 JavaScript 校验、JSP 表单或 Base64 字段，缺服务端处理实现时，不得写“非漏洞”；应写“待验证”或“不可确认”。
- `web.xml` 声明的 Servlet 找不到实现 class/jar 时，写“不可确认”，不要混写“待验证”。
- 报告可以最小引用代码中真实出现的扩展名常量。验证 Payload 需要文件名时，优先使用无害 marker 文件名；若必须证明类型校验缺陷，文件名或扩展名必须来自真实入口和授权验证上下文，且不得包含后门内容。

## 停止、确认或切换条件

- 找不到实现源码、反编译结果或字节码证据时：停止确认漏洞，输出不可确认。
- 需要先知道请求参数是否到达写入 sink 时：切换到 `java-route-tracer`。
- 需要判断上传入口是否未授权或越权时：交给 `java-auth-audit`。
- 需要判断上传后的文件读取、下载或目录遍历时：交给 `java-file-read-audit`。
- 用户要求组件版本漏洞或组件编号查询时：交给 `java-vuln-scanner`。
- 用户要求可执行后门样本、持久化内容、横向移动或批量验证脚本时：拒绝该部分，只保留绑定真实入口的低破坏授权验证材料。

## Eval

| 类型 | 用户请求或场景 | 预期行为 |
|------|----------------|----------|
| 正例 | “审计这个 MultipartFile 上传接口是否能任意文件上传。” | 触发，定位入口、文件名、保存路径、校验和 Web 可访问性 |
| 正例 | “WAR 里只有 class，帮我看上传保存路径有没有路径穿越。” | 触发，读取反编译策略，先定位上传相关类 |
| 正例 | “检查 Commons FileUpload 代码有没有限制扩展名和目录。” | 触发，读取上传规则并输出上传点映射 |
| 反例 | “列出所有 POST 路由。” | 不触发，使用 `java-route-mapper` |
| 反例 | “追踪 fileId 最后读了哪个文件。” | 不触发，使用 `java-file-read-audit` 或 `java-route-tracer` |
| 反例 | “检查 commons-fileupload 组件漏洞编号。” | 不触发，使用 `java-vuln-scanner` |
| 边界例 | 上传图片后服务端重命名并写入非 Web 目录 | 记录上传点，通常非漏洞或低风险加固 |
| 边界例 | Base64 字符串解码后写入请求参数指定文件名 | 触发，按上传候选追踪文件名和目录 |
| 边界例 | 上传 zip 后解压到服务端目录 | 触发，检查压缩包路径穿越和二次写入 |
| 失败案例 | 只看到 `/upload` 路由就写任意文件上传 | 不合格，缺写入 sink 和校验证据 |
| 失败案例 | 确认漏洞却没有 Burp Suite 请求和 Payload | 不合格，无法交付开发单位复现 |
| 失败案例 | 输出可执行后门样本文件名、持久化内容或批量利用脚本 | 不合格，违反安全边界 |
| 失败案例 | 把报表导出写文件误报为上传漏洞 | 不合格，缺外部上传输入 |
| 失败案例 | 把工具类、拦截器或 `maximumSize` 配置单独列为上传点 | 不合格，统计口径错误 |
