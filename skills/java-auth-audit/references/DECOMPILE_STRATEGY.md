# 鉴权反编译策略

只在 `AUTH_GATE`、`POLICY_RULE`、资源归属校验或动态策略实现不可读时使用。

## 优先补齐

- route 到 `AUTH_GATE` 的覆盖关系。
- 放行规则和匹配逻辑。
- `AUTH_CONTEXT` 构建和校验。
- `RESOURCE_ID`、`RESOURCE_OWNER`、`TENANT_SCOPE` 的验证逻辑。
- 动态策略加载和默认策略。

记录编译产物来源、反编译输出路径、缺失实现和 blocked 下一步。
