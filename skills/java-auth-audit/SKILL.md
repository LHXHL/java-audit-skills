---
name: java-auth-audit
description: 当用户要求审计 Java 源码、反编译源码、部署产物或 pipeline 结构化证据中的认证、授权、越权、未授权访问、鉴权绕过、资源归属校验或入口到鉴权策略映射时使用；只做路由、调用链、SQL、XML、文件、反序列化或组件风险扫描时不要使用。
---

# Java Auth Audit

## 当前定位

`java-auth-audit` 是入口鉴权和资源授权专项判定层。它消费 route mapper 的入口闭环、route tracer 的调用链证据、源码、反编译源码和结构化 coverage，回答：

- 每个 `ENTRY_ROUTE` 是否经过真实 `AUTH_GATE`。
- `AUTH_GATE` 只认证身份，还是包含 `POLICY_RULE`、角色、权限、租户、资源归属或对象级授权。
- 是否存在未覆盖入口、条件绕过、路径解析差异或资源越权。
- 结论应为：确认漏洞、条件成立、待验证、不可确认、非漏洞。

本 skill 不负责全量路由枚举、不替代调用链追踪、不扫描组件 CVE。

## 触发条件

- 用户要求判断未授权、越权、认证绕过、权限绕过或资源归属校验。
- pipeline 需要把 route mapper 输出映射到鉴权策略。
- 上游结构化证据存在 auth 相关候选或 route coverage 缺口。

不触发：

- 只要求提取路由。
- 只追踪参数到 sink。
- 只判断 SQL、XML、文件、反序列化或组件版本。

## 工作流

1. 读取 `structured/routes.jsonl`、`dispatchers.jsonl`、`coverage_report.json`。
2. 若路由只有 root/dispatcher 未展开，先要求 route mapper 补全或记录 auth blocked。
3. 识别项目实际 `AUTH_GATE`：过滤、拦截、注解、会话、令牌、业务方法、网关或自定义策略均由代码证据决定。
4. 建立 `ENTRY_ROUTE -> AUTH_GATE -> POLICY_RULE -> RESOURCE_SCOPE` 映射。
5. 对高风险入口或资源对象不足时，可要求 route tracer 补调用链。
6. 使用输出模板生成映射报告和主报告。

## 成功标准

- 每个入口都有已覆盖、未覆盖、待验证或不可确认状态。
- 未展开 route 不得当作已审计入口。
- 身份认证、角色权限、资源归属、租户范围和业务状态分开判断。
- 缺源码、缺配置、缺实现或动态策略不可读时写 blocked。
- 报告不写组件版本、内部规则或 validator 结果。

## Hard Rules

1. 没有 route 闭环，不得宣称入口面鉴权全覆盖。
2. 没有真实 `AUTH_GATE` 证据，不得写已鉴权。
3. 只有登录态不等于对象级授权。
4. 资源归属、租户和业务状态必须有代码证据。
5. 结论状态只能使用：确认漏洞、条件成立、待验证、不可确认、非漏洞。

## 按需读取

- 鉴权门禁：`references/FILTER_INTERCEPTOR.md`
- 策略和资源授权：`references/ANNOTATION_AUTH.md`、`references/SESSION_AUTH.md`
- 绕过模式：`references/BYPASS_PATTERNS.md`、`references/URI_PARSING_BYPASS.md`
- 反编译策略：`references/DECOMPILE_STRATEGY.md`
- 输出模板：`references/OUTPUT_TEMPLATE_MAPPING.md`、`references/OUTPUT_TEMPLATE_MAIN.md`
