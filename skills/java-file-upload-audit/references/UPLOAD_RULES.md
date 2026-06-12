# 文件上传审计规则

本文件用于 `java-file-upload-audit` 已触发后加载。结论必须回到真实项目证据：入口或输入来源、上传内容来源、文件名来源、保存路径、写入 sink、校验逻辑、执行条件和限制说明。

## 证据模型

| 证据 | 必须回答的问题 | 不足时结论 |
|------|----------------|------------|
| 上传输入 | 文件内容、文件名或目录是否来自 HTTP/SOAP/RPC/MQ/后台表单/第三方回调 | 待验证或不可确认 |
| 写入 sink | 具体哪个 API 把内容写入磁盘或对象存储 | 不得下上传漏洞结论 |
| 文件名来源 | 最终文件名是否来自客户端、请求参数、数据库字段或服务端生成 | 待验证或不可确认 |
| 保存路径 | 基础目录和子目录是否固定，最终路径是否受请求影响 | 待验证或不可确认 |
| 校验逻辑 | 类型、内容、大小、路径和重命名校验是否在写入前生效 | 不得下确认漏洞；缺 sink 或后续校验证据时不得写条件成立 |
| 执行条件 | 路由、权限、分支、配置、文件大小、Content-Type 是否满足 | 待验证或不可确认 |
| 写入后影响 | 是否 Web 可访问、可被解释执行、覆盖已有文件、被后续解析或解压 | 影响风险说明，不替代前六项 |

状态必须使用中文：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 统计和映射口径

- “上传点映射”只列真实入口或可由外部触发的上传执行点。
- 工具类、拦截器、配置文件、静态目录、第三方 jar 和只被其它入口调用的 helper，不是上传点；这些证据放入“候选风险与非漏洞依据”，不计入结论统计。
- 结论统计数量必须与上传点映射中的状态数量一致；如果多个上传入口聚合为一个风险详情，必须说明映射行和风险编号的关系。

## 上传实现识别

### Servlet 3 Part

识别：

```java
request.getPart("file")
request.getParts()
part.getSubmittedFileName()
part.write(path)
part.getInputStream()
```

重点：

- `Part.write` 的相对路径可能受容器 `MultipartConfig` 位置影响，要确认实际落盘目录。
- `getSubmittedFileName` 来自客户端，必须看是否只保留 basename、是否过滤路径分隔符和控制字符。
- `@MultipartConfig` 的大小限制只控制容量，不等于类型或路径安全。

### Spring MultipartFile

识别：

```java
@RequestParam MultipartFile file
file.getOriginalFilename()
file.transferTo(dest)
file.getInputStream()
```

重点：

- `getOriginalFilename` 是高风险文件名来源，除非后续完全替换为服务端生成名。
- `transferTo`、`Files.copy(file.getInputStream(), path)`、`FileOutputStream` 都是写入 sink。
- `MultipartFile.isEmpty`、大小限制或异常捕获不能证明安全。

### Commons FileUpload

识别：

```java
ServletFileUpload.isMultipartContent(request)
new ServletFileUpload(factory).parseRequest(request)
FileItem.getName()
FileItem.write(file)
FileItem.getInputStream()
```

重点：

- `FileItem.getName` 来自客户端，可能包含路径片段。
- `setSizeMax`、`setFileSizeMax` 只限制大小，不限制类型或路径。
- 要区分普通表单字段和文件字段，确认 `isFormField()` 分支。

### Base64 / JSON / 自定义上传

识别：

```java
Base64.decode(value)
Files.write(path, bytes)
new FileOutputStream(path).write(bytes)
IOUtils.copy(input, output)
```

重点：

- 请求体、JSON 字段、SOAP 字段或 MQ 消息中携带文件内容时，也属于上传候选。
- 若文件名或目录来自另一个字段，需要追踪两个数据流：内容流和路径流。
- 只把内容写到临时文件后继续解压、导入或转码时，还要检查二次写入。

## 写入 sink

高优先级 sink：

- `MultipartFile.transferTo(File|Path)`
- `Part.write(String)`
- `FileItem.write(File)`
- `Files.copy(InputStream, Path)`
- `Files.write(Path, byte[])`
- `FileOutputStream`、`BufferedOutputStream`、`RandomAccessFile`
- `FileUtils.copyInputStreamToFile`
- `IOUtils.copy`
- `ZipInputStream` / `ZipFile` 解压后写入文件

非上传或需要额外证据：

- 服务端生成报表、导出 CSV/Excel/PDF。
- 日志、缓存、缩略图、二维码、验证码写入。
- 下载、预览或文件读取路径。
- 仅创建目录或检查文件存在。

## 文件名风险

高风险来源：

- `getOriginalFilename`
- `Part.getSubmittedFileName`
- `FileItem.getName`
- 请求参数中的 `fileName`、`name`、`path`、`dir`、`folder`
- JSON、XML、数据库字段中可被外部写入的文件名

安全倾向：

- 完全服务端生成随机名或哈希名。
- 只从白名单扩展名映射中生成后缀。
- 使用 `Paths.get(name).getFileName()` 或等价 basename 后，再做字符白名单。
- 写入前检查 canonical path 或 normalized path 位于允许目录下。

不足或不能单独证明安全：

- 只替换 `../`。
- 只检查不包含 `/`，但未处理反斜杠、编码、Unicode 分隔符或控制字符。
- 只用黑名单过滤少量扩展名。
- 只截取最后一个点后的扩展名，未处理多后缀或空后缀策略。

## 保存路径和目录限制

需要记录：

- 基础目录来源：配置、常量、系统属性、`getRealPath`、数据库、请求参数。
- 子目录来源：用户 ID、租户 ID、日期、业务类型、请求字段。
- 最终路径构造：`new File(base, name)`、字符串拼接、`Paths.get`、`resolve`。
- 是否在写入前执行 `normalize`、`getCanonicalPath`、`startsWith(base)` 或等价检查。

风险模式：

- 基础目录或子目录来自请求参数。
- 最终路径未限制在固定基础目录内。
- 写入 Web 根目录、应用部署目录、`WEB-INF` 外可访问目录或静态资源目录。
- 文件名不重命名，导致覆盖或可预测访问路径。
- 上传后自动解压，解压条目名未做路径限制。

仅目录可访问还不够：

- 如果文件名服务端随机、扩展名白名单和内容校验均有效，写入 Web 可访问目录通常是风险影响放大因素，不应单独下漏洞结论。
- 如果同时存在入口绕过鉴权、校验缺失、路径可控、内容可被后续解析等证据，才可把 Web 可访问目录纳入“条件成立/确认漏洞”的影响说明。

## 类型和内容校验

较强证据：

- 扩展名白名单和服务端生成文件名同时存在。
- MIME/Content-Type 只作为辅助，结合文件魔数或真实解析。
- 对图片、文档、压缩包等类型做解析级验证，并处理解析失败。
- 大小限制、数量限制和存储配额存在。

较弱证据：

- 只信任浏览器提供的 Content-Type。
- 只检查扩展名但保留原始文件名。
- 只做黑名单。
- 只判断文件非空。
- 上传后再扫描，但扫描失败仍保存或可访问。

不能单独作为漏洞的情况：

- 只看到黑名单常量，但同时存在白名单、魔数或解析级校验，且未证明白名单/魔数分支失效。
- 白名单包含 `zip`、Office、文本、图片、视频等业务类型，但没有后续自动解析、内容执行、静态暴露或类型混淆影响证据。
- 只看到 `maximumSize` 数值偏大；这是容量加固点，不是文件上传漏洞编号。

## 可访问性和影响

需要判断：

- 保存目录是否映射为静态资源。
- 是否位于应用部署目录、Web 根目录或可被反向代理暴露的目录。
- 容器是否会解释特定类型文件。
- 上传文件是否可被后续导入、解析、解压、转码或同步到其它系统。
- 覆盖已有文件是否可能影响配置、模板、任务脚本或业务数据。

验证输出：

- 对“确认漏洞/条件成立”项，必须按 `VALIDATION_GUIDE.md` 输出 Burp Suite 请求和 Payload。
- Burp Suite 请求必须绑定真实入口和参数，不能用泛化 `/upload` 或虚构字段。
- Payload 使用无害 marker 文件内容，证明写入路径、文件 ID、日志、后续解析或访问性条件，不包含可执行代码。
- 对“待验证/不可确认/非漏洞”项，不输出 Burp Suite 请求或 Payload。

不要输出：

- 可执行后门样本内容、持久化脚本、批量利用脚本或横向移动步骤。
- 缺少真实入口、参数或鉴权上下文的验证请求。
- 声称测试结果已经达成，除非用户提供授权验证日志且报告明确标注来源。

扩展名证据写法：

- 可以最小引用代码中真实出现的黑名单或白名单常量，用于证明项目采用了哪类校验。
- 不要补充列举“黑名单缺少哪些可执行后缀”。
- 不要给出大小写绕过、双后缀绕过或编码绕过写法。授权验证需要文件名时，使用占位符或无害 marker 文件名，并说明需由开发单位在测试环境替换。
- 若黑名单不充分，写“黑名单覆盖范围不足，需改为白名单和内容校验”，不要列具体绕过后缀。

## 常见误判

- 看到 `/upload` 路由但没有文件写入 sink 就写漏洞。
- 把服务端导出报表、模板生成或缓存文件写入误报为上传。
- 把 `MultipartFile` 参数写成漏洞，但忽略后续服务端随机命名、目录隔离和内容白名单。
- 把大小限制当成类型或路径防护。
- 把 Struts `fileUpload` 拦截器未配置 `allowedTypes/allowedExtensions` 直接写成条件成立，却没有 Action 写入 sink、后续自定义拦截器和保存目录证据。
- 把 `maximumSize` 或全局 multipart 配置当成独立上传漏洞并输出 Burp/Payload。
- 发现黑名单常量就列出一串未覆盖后缀；应写“黑名单覆盖范围不足”，不要给具体绕过后缀清单。
- 把白名单包含 `zip`、Office、文本、图片或视频业务类型直接写成漏洞；需要证明后续解析、静态可访问或内容校验缺失带来的实际影响。
- 把前端 JavaScript 白名单、JSP 表单或 Base64 字段当成服务端安全结论；缺服务端实现时只能待验证或不可确认。
- `web.xml` 里声明了 Servlet 但找不到 class/jar 实现时混用“不可确认”和“待验证”；只能选择一种状态，通常为不可确认。
- 看到 `getRealPath` 就直接确认可执行上传，未判断路径和容器映射。
- 对缺少实现源码或反编译证据的工具类直接写非漏洞。
