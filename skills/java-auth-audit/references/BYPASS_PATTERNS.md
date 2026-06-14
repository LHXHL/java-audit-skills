# 鉴权绕过模式

## 模式

| 模式 | 说明 |
|------|------|
| `UNMAPPED_ROUTE` | route mapper 发现入口，但没有 `AUTH_GATE` 覆盖 |
| `ROOT_ONLY_AUTH` | 只验证根入口，operation/sub-function 未校验 |
| `ALLOWLIST_OVERMATCH` | 放行规则覆盖过宽 |
| `PATH_NORMALIZATION_GAP` | 路径解析和鉴权匹配不一致 |
| `CLIENT_SCOPE_TRUST` | 用户、租户、角色或资源归属信任客户端字段 |
| `MISSING_OWNER_CHECK` | 只认证身份，未校验资源所有者 |
| `DYNAMIC_POLICY_UNKNOWN` | 策略来自动态配置但不可读 |

每个绕过都必须绑定真实入口和证据。
