---
name: java-file-read-audit
description: 当用户要求审计 Java 源码、反编译源码、部署产物或 pipeline 结构化证据中的任意文件读取、资源读取、下载、路径遍历、FILE_READ sink 或外部参数控制读取路径时使用；只做路由、调用链、文件上传、SQL、XML、反序列化、鉴权或组件风险扫描时不要使用。
---

# Java File Read Audit

## 当前定位

`java-file-read-audit` 是文件读取类 sink 的专项判定层。它消费 route、trace、源码、反编译源码和结构化 sink，回答：

- `REQUEST_PARAM` 是否影响 `FILE_READ_API` 的读取目标。
- 路径是否经过 `PATH_JOIN`、规范化、根目录约束、白名单或 ID 映射。
- 文件内容是否通过 `OUTPUT_CHANNEL` 返回、写入或用于后续敏感操作。
- 结论应为：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 触发条件

- 用户要求判断文件读取、下载、路径遍历或资源读取风险。
- 上游结构化证据包含 `sink_types: ["FILE_READ"]` 或 `FILE` 并派发到本 skill。
- route tracer 已证明输入到达文件读取 category sink。

不触发：

- 只追踪调用链但不做漏洞判定。
- 只有响应输出或下载命名，没有文件/资源来源证据。
- 只审计上传、SQL、XML、反序列化或鉴权。

## 工作流

1. 读取 route、trace、sink 和 coverage 证据。
2. 缺少端到端数据流时先要求或执行 route tracer。
3. 读取 `references/FILE_READ_METHODS.md` 和 `references/PATH_TRAVERSAL.md`。
4. 源码缺失时读取 `references/DECOMPILE_STRATEGY.md`。
5. 判断路径来源、根目录、防护、输出条件和分支可达性。
6. 使用 `references/OUTPUT_TEMPLATE.md` 输出报告。

## 成功标准

- 每个结论都有入口、参数、trace、读取 sink、路径构造、防护和输出条件。
- 不把只有响应输出、业务命名或缺实现的候选写成文件读取 sink。
- 对路径规范化、根目录约束、白名单、ID 映射和服务端常量给出证据。
- 报告不写内部规则、validator 结果或未授权利用步骤。

## Hard Rules

1. 没有真实 `FILE_READ_API`，不得下文件读取/路径遍历结论。
2. 没有用户可控路径或间接文件标识，不得下确认漏洞。
3. 没有输出或敏感后续使用条件时，最多写条件成立或待验证。
4. 结论状态只能使用：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 按需读取

- 文件读取类别：`references/FILE_READ_METHODS.md`
- 路径遍历规则：`references/PATH_TRAVERSAL.md`
- 反编译策略：`references/DECOMPILE_STRATEGY.md`
- 输出模板：`references/OUTPUT_TEMPLATE.md`
