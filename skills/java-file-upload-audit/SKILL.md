---
name: java-file-upload-audit
description: 当用户要求审计 Java 源码、反编译源码、部署产物或 pipeline 结构化证据中的文件上传、导入、写入、覆盖、落盘路径、FILE_WRITE sink 或外部输入控制保存目标时使用；只做路由、调用链、文件读取、SQL、XML、反序列化、鉴权或组件风险扫描时不要使用。
---

# Java File Upload Audit

## 当前定位

`java-file-upload-audit` 是文件写入/上传类 sink 的专项判定层。它回答：

- `REQUEST_PARAM` 或上传内容是否到达真实 `FILE_WRITE_API`。
- 文件名、路径、后缀、内容类型、大小和落盘目录是否可控。
- 是否存在重命名、白名单、隔离目录、不可执行存储和访问控制。
- 结论应为：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 触发条件

- 用户要求判断文件上传、导入、写入、覆盖或落盘风险。
- 上游结构化证据包含 `sink_types: ["FILE_WRITE"]`、`UPLOAD` 或 `FILE` 并派发到本 skill。
- route tracer 已证明输入到达文件写入 category sink。

不触发：

- 只判断文件读取或下载。
- 只有上传路由命名，没有写入实现证据。
- 只追踪调用链但不做漏洞判定。

## 工作流

1. 读取 route、trace、sink 和 coverage 证据。
2. 缺少端到端数据流时先要求或执行 route tracer。
3. 读取 `references/UPLOAD_RULES.md`。
4. 源码缺失时读取 `references/DECOMPILE_STRATEGY.md`。
5. 判断写入目标、文件名来源、类型校验、存储隔离、覆盖风险和访问路径。
6. 使用 `references/OUTPUT_TEMPLATE.md` 输出报告。

## 成功标准

- 每个结论都有入口、参数、trace、写入 sink、路径构造、防护和访问条件。
- 不把上传命名、响应输出或缺实现候选写成确认漏洞。
- 对文件名、后缀、内容类型、大小、重命名、目录隔离、访问路径给出证据。
- 报告不写内部规则、validator 结果或未授权利用步骤。

## Hard Rules

1. 没有真实 `FILE_WRITE_API`，不得下上传/写入结论。
2. 没有用户可控内容、文件名或路径，不得下确认漏洞。
3. 没有可访问、可覆盖、可解析或敏感后续处理条件时，最多写条件成立或待验证。
4. 结论状态只能使用：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 按需读取

- 上传规则：`references/UPLOAD_RULES.md`
- 反编译策略：`references/DECOMPILE_STRATEGY.md`
- 授权复核边界：`references/VALIDATION_GUIDE.md`
- 输出模板：`references/OUTPUT_TEMPLATE.md`
