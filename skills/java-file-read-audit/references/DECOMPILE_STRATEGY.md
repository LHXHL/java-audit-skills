# 文件读取审计反编译策略

只在源码缺失、只有 `.class`/`.jar`/`.war`，或关键文件读取逻辑不可读时读取本文件。

## 何时反编译

必须优先反编译：

- 下载、预览、导出、附件、模板、资源读取相关 Controller/Action/Servlet。
- Service/Util/Helper 中的文件读取、路径拼接、资源加载方法。
- route-tracer 报告的 FILE sink 所在类。
- 配置指向的自定义下载 Servlet、文件处理 Filter、资源 Handler。

不需要反编译：

- 标准 JDK、Spring MVC、Servlet 容器默认类。
- 已有源码且可读的类。
- 与文件读取无关的海量业务类。

## 最小化定位

优先从以下信息定位 class：

- route mapper 的入口方法。
- `web.xml` servlet/filter class。
- Spring XML bean class。
- Struts action class。
- 类名和常量池中的 `download`、`readFile`、`fileName`、`FileInputStream`、`Files.read`、`getResourceAsStream`。

## 反编译结果要求

报告中引用反编译证据时必须标注：

- 原始 class/JAR 路径。
- 反编译输出路径或类名。
- 方法名和关键代码片段。
- 行号缺失时说明“反编译来源无稳定行号”。

## 证据等级

| 材料 | 能证明什么 | 不能证明什么 |
|------|------------|--------------|
| class/JAR 存在 | 类存在、包名、部署模块 | 方法内部安全逻辑 |
| 常量池字符串 | 可能存在字段、方法名、字符串字面量 | 调用顺序、分支条件、防护是否执行 |
| 方法签名 | 入口或工具方法可能存在 | 参数是否可控、sink 是否实际执行 |
| 字节码/反编译方法体 | 调用链、sink、防护和分支 | 运行时环境、鉴权策略是否生效 |
| route-tracer 证据 | 参数到 sink 的可达性 | 部署系统、文件存在性、实际响应内容 |

只有 class 名、方法名、字段名、常量池字符串，或“未发现 canonical/normalize 字符串”，不得作为确认漏洞或条件成立依据。它们只能支撑 `待验证` 或 `不可确认`。

## 失败处理

反编译失败或未取得方法体时：

- 不得写确认漏洞或条件成立。
- 映射表写 `待验证` 或 `不可确认`。
- 第 4 节写需要补充的 class、JAR、源码或方法体证据。
- 不生成 Burp Suite 请求和 payload。
- 正式报告不要写具体工具不可用、审批失败、权限限制、命令失败或运行环境问题；统一写“本轮未取得关键类可读实现/方法体”。
- 不要在第 5 节为此类项写风险详情。
