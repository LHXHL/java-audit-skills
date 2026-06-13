# 组件命中触发面分流指南

只在组件版本命中后，需要判断后续交给哪个专项 skill 时读取本文件。这里不生成可复制验证材料。

## 分流原则

- 版本命中只证明“存在需要治理的组件版本证据”。
- 触发面核查只写需要哪些入口、配置、sink 或运行条件，不写攻击步骤。
- 如果当前项目没有相关入口或配置证据，状态保持 `触发面待核查` 或 `环境条件待确认`。

## 常见组件分流

| 组件/规则类型 | 需要核查的触发面 | 建议交接 |
|---------------|------------------|----------|
| Log4j2 / Log4j 1.x | 用户可控输入是否进入日志、JNDI/JMS/JDBC appender 配置、运行时 JDK/配置 | `java-route-tracer` 或日志专项；不要输出 JNDI 验证字符串 |
| Fastjson / Jackson / XStream | 是否解析用户可控 JSON/XML，对象类型控制、autoType/default typing、反序列化 sink | `java-deserialization-audit`；XML 场景可交给 `java-xxe-audit` |
| Shiro | `rememberMe`、密钥、filter chain、认证绕过路径、Cookie 处理 | `java-auth-audit` + `java-deserialization-audit` |
| Struts2 Core / REST / Multipart | Struts action 可达性、动态方法调用、REST/XStream、multipart 上传入口 | `java-route-mapper`、`java-route-tracer`、`java-file-upload-audit`、`java-deserialization-audit` |
| Spring Framework / Spring Boot | JDK、容器、数据绑定入口、Actuator 暴露、配置条件 | `java-route-tracer`、`java-auth-audit` 或对应专项 |
| Commons FileUpload | 可达上传接口、multipart parser、大小限制、临时目录 | `java-file-upload-audit` |
| Commons Collections / BeanUtils | 是否存在反序列化入口和利用链依赖条件 | `java-deserialization-audit` |
| dom4j / JDOM / Xerces / XML 解析库 | 用户可控 XML 是否进入解析器、安全特性是否关闭外部实体 | `java-xxe-audit` |
| JDBC 驱动 / H2 / Derby | 控制 JDBC URL、初始化脚本、控制台暴露、SQL 执行条件 | `java-sql-audit` 或配置专项 |
| Commons IO / 文件路径工具 | 用户可控文件名、下载/预览/导出路径、`FilenameUtils` / `FileUtils` 调用点 | `java-route-tracer`、`java-file-read-audit` |
| Tomcat / Jetty / 容器组件 | 容器版本、协议暴露、AJP/管理端口、部署配置 | pipeline/运维配置审计；必要时交给 `java-auth-audit` |

## 证据写法

报告第 4 节只写：

- 已观察到的入口、配置、类名或依赖组合。
- 仍缺失的运行条件。
- 下一步应该交给哪个 skill。

不要写：

- 可复制攻击请求。
- 可复制验证请求、攻击字符串、JNDI URL、恶意 XML、反序列化链对象。
- “业务风险已成立”“已确认 RCE”“可直接取得服务器权限”等结论。
