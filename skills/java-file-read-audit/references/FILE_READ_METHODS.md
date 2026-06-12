# 文件读取 Sink 识别

只在需要定位 Java 文件读取、下载或资源读取 sink 时读取本文件。

## 高价值 sink

| 类别 | API / 模式 | 审计重点 |
|------|------------|----------|
| 传统 IO | `new FileInputStream(path)`, `new FileReader(path)`, `RandomAccessFile` | `path` 是否可控，是否经过规范化和目录约束 |
| Reader/Scanner | `BufferedReader`, `InputStreamReader`, `Scanner(new File(...))` | 底层 `File` / `InputStream` 来源 |
| NIO | `Files.readAllBytes`, `Files.readAllLines`, `Files.lines`, `Files.newInputStream`, `Files.copy` | `Path` 构造和 `normalize`/`toRealPath` |
| Servlet 下载 | `response.getOutputStream`, `IOUtils.copy(input, response)` | `InputStream` 的文件来源和入口参数 |
| Spring Resource | `ResourceUtils.getFile`, `ClassPathResource`, `FileSystemResource`, `ServletContextResource` | 外部输入是否影响 resource path |
| ServletContext | `getResource`, `getResourceAsStream`, `getRealPath` | webroot 下路径是否可控或越界 |
| 压缩/归档读取 | `ZipFile#getInputStream`, `JarFile#getInputStream` | entry name 是否可控；通常交叉关注 zip slip 但本 skill 只判读取 |
| 配置/模板读取 | `Properties.load`, `Yaml.load`, template engine loader | 是否由外部输入选择本地文件 |

## 非 sink 或低价值信号

- `File.exists()`、`isFile()`、`length()` 只是元数据检查；只有与文件内容返回结合时才构成读取风险。
- `new File(path)` 只是路径对象构造，不是读取 sink。
- 只有 `ServletOutputStream`、`response.getOutputStream()`、`addHeader`、`setContentType`、`download` 方法名，只能证明响应可能返回数据；没有文件/资源 `InputStream` 来源时，不得作为 FILE sink 映射行。
- 固定 `classpath:` 资源、固定帮助文档、固定模板文件通常不是漏洞。
- 数据库 BLOB、对象存储 key、附件 ID 映射不是本地文件读取，除非最终落到本地路径并可被外部控制。

## 需要继续追踪的模式

- `download(fileId)` 从数据库查路径后读取文件：查 ID 是否可控、是否有对象归属校验、数据库路径是否闭合。
- `baseDir + fileName`、`new File(baseDir, fileName)`、`Paths.get(baseDir, fileName)`：查 `fileName` 是否可控和 canonical/normalize 约束。
- `request.getParameter("path")`、JSON 字段 `file.path`、Header 中的文件名：查是否进入 sink。
- `URLDecoder.decode`、自定义 `cleanPath`、黑名单替换：查解码顺序和绕过。

## 结论门槛

进入第 5 节风险详情并提供 Burp Suite 请求前必须同时具备：

- 真实入口或上游调用证据。
- 外部输入可影响读取路径或文件选择。
- 真实文件读取 sink。
- 防护缺失或不足证据。
- 可复核 Burp Suite 请求和 payload。

只具备 sink 命中、字段名、方法名、常量池字符串、配置映射或前端拼接时，可以进入第 3 节映射和第 4 节候选说明，但不得进入第 5 节风险详情，不得输出 Burp Suite 请求和 payload。

若只观察到输出流而未观察到文件、资源、`InputStream`、`FileInputStream`、`Files.*`、`getResourceAsStream`、`Resource` 或 `getRealPath` 等来源证据，应只在第 4 节作为“非 sink 或不可确认候选”说明，避免放入文件读取操作映射。
