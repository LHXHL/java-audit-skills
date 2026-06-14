# 组件命中触发面分流指南

只在组件版本命中后判断后续交给哪个专项 skill。这里不生成验证材料。

## 分流原则

- 版本命中只证明组件证据。
- 触发面核查只写需要哪些入口、配置、sink 或运行条件。
- 没有相关入口、配置或使用证据时，状态保持 `触发面待核查` 或 `环境条件待确认`。

## 抽象分流

| 规则类型 | 需要核查的触发面 | 建议交接 |
|----------|------------------|----------|
| `LOGGING_INPUT` | 用户可控输入是否进入日志或外部解析配置 | route tracer 或对应专项 |
| `OBJECT_DECODER` | 用户可控对象数据、类型元数据和链条条件 | `java-deserialization-audit` |
| `XML_PARSER` | 用户可控 XML 是否进入 parser，外部资源防护是否缺失 | `java-xxe-audit` |
| `UPLOAD_PARSER` | 可达上传入口、解析器、大小限制和临时目录 | `java-file-upload-audit` |
| `AUTH_GATE` | 认证策略、token、cookie、过滤链或权限绕过条件 | `java-auth-audit` |
| `SQL_ENGINE` | 动态连接、初始化脚本、查询执行或控制台暴露 | `java-sql-audit` 或配置专项 |
| `FILE_HELPER` | 用户可控文件名、下载、预览、导出或路径工具 | `java-file-read-audit` |
| `RUNTIME_CONTAINER` | 运行容器、协议、管理端口或部署配置 | 运维配置审计或鉴权专项 |

## 证据写法

报告只写：

- 已观察到的入口、配置、类名、依赖组合或 structured 证据。
- 仍缺失的运行条件。
- 下一步交给哪个 skill。

不要写可复制请求、攻击字符串、恶意 XML、对象链或“业务风险已成立”。
