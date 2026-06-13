# 文件上传字节码审计策略

当项目只有 `.class`、`.jar`、`.war` 或源码缺失时读取本文件。目标是用最小反编译范围确认上传入口、写入 sink、文件名来源、保存路径和校验逻辑，不做全量无差别反编译。

## 何时需要反编译

需要反编译或读取字节码的情况：

- 只有 WAR/JAR/class，没有 Java 源码。
- 常量池命中 `MultipartFile`、`FileItem`、`Part`、`transferTo`、`write`、`upload`、`getOriginalFilename`、`getSubmittedFileName` 等上传候选，但无法确认调用顺序。
- route-tracer 报告 `UNCONFIRMED` 上传 sink。
- 需要确认写入前是否发生文件名净化、路径规范化、类型校验或重命名。

不需要扩大反编译的情况：

- 已有源码能证明完整数据流。
- 常量池只出现服务端导出、日志、缓存或固定配置写入，且没有外部上传输入。
- 只需要列出路由，应该交给 `java-route-mapper`。

## 定位优先级

按以下顺序定位：

1. 路由和入口类：`*Controller*`、`*Servlet*`、`*Action*`、`*Resource*`、`*WebService*`。
2. 上传 API 命中类：包含 `MultipartFile`、`FileItem`、`Part`、`ServletFileUpload`、`transferTo`、`getOriginalFilename` 的 class。
3. 存储封装：`*Upload*`、`*Storage*`、`*FileService*`、`*FileUtil*`、`*Attachment*`。
4. 配置和常量：上传目录、临时目录、静态资源映射、大小限制、白名单数组。
5. 二次处理：解压、导入、图片处理、Office/媒体解析、同步任务。

## 推荐定位命令

以下命令只用于定位候选，不替代最终证据：

```bash
rg -a -n "MultipartFile|FileItem|ServletFileUpload|javax/servlet/http/Part|transferTo|getOriginalFilename|getSubmittedFileName|item.write|Files.copy|FileOutputStream" <target>
rg -a -n "upload|Upload|attachment|Attachment|import|Import|getRealPath|static|resources|webapps" <target>
find <target> -name "*Upload*.class" -o -name "*File*.class" -o -name "*Attachment*.class"
```

注意：`rg -a`、`strings` 和常量池命中只能证明候选存在。确认漏洞必须有调用顺序和数据流证据；无法确认时写“待验证”或“不可确认”。

## 反编译目标

最小反编译集合：

- 入口类：接收上传请求或调用上传服务的方法。
- 存储类：构造文件名、目录和写入 sink 的方法。
- 校验类：扩展名、MIME、魔数、路径校验、重命名策略。
- 配置类：上传目录、Web 映射、MultipartConfig、Spring multipart 配置。

不建议反编译：

- 与候选类无调用关系的大型第三方库。
- 仅 DTO、常量枚举、异常类，除非它们保存上传目录或白名单。
- JDK、Servlet API、Spring 框架本身。

## 证据记录

报告中记录：

- 原始 class/jar/war 路径。
- 反编译输出路径或常量池读取来源。
- 关键方法名、字段名、字符串常量和调用关系。
- 反编译失败或工具不可用时的限制说明。
- 未运行 `javap`、CFR、Procyon、`strings` 或其它工具时，写“本次未使用该工具”。
- 没有可用反编译或反汇编输出时，写“本轮未取得反编译/反汇编结果”，并说明因此缺少哪些代码证据。
- 报告只记录证据缺口，不解释工具为什么没有输出；不要写环境、安装、权限、审批、申请、拒绝、拦截或工具许可类原因。

不得记录：

- 不存在的反编译路径。
- 没有读取过的源码片段。
- 由类名猜测出的上传路由或漏洞结论。
- 可执行后门样本、持久化内容、批量利用脚本、横向移动步骤，或缺少真实入口的可复制请求。

## 验证材料边界

- 反编译证据足以支持“确认漏洞/条件成立”时，报告仍必须按 `VALIDATION_GUIDE.md` 输出 Burp Suite 请求和 Payload。
- Burp Suite 请求中的入口、参数名、Content-Type 和鉴权状态必须来自源码、配置、route-mapper、route-tracer 或反编译证据。
- 如果只能从 class 常量池看到候选方法名，不能输出 Burp Suite 请求或 Payload；写清“入口未确认，不输出 Burp Suite 请求和 Payload”。

## 判定限制

- 只有常量池命中 `transferTo` 或 `write`，但无法确认输入来自请求时，标“不可确认”或“待验证”。
- 只有入口参数 `MultipartFile`，但无法确认保存路径和写入 sink 时，不能确认漏洞。
- 只有 `uploadDir` 字符串，无法确认 Web 映射时，不能声称可执行或可访问。
- 只有反编译伪代码时，必须说明来源和可能的控制流缺失。
