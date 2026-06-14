# 运行容器入口兼容参考

本文件作为运行容器入口的机制参考。

## 机制特点

运行容器入口通常先暴露 `ENTRY_ROOT`，再由代码根据路径片段、请求参数、请求体字段、配置键或注册表选择 `ENTRY_OPERATION`。

## 必须展开

- `ENTRY_ROOT` 是根入口，不是最终 route。
- `DISPATCH_RULE` 必须从源码、配置或运行产物中提取。
- 每个可枚举 `DISPATCH_KEY` 都应生成独立 route。
- 无法枚举的分支写 dispatcher 和 blocked 原因。

## 证据要求

每条记录至少包含：

- 根入口证据。
- 分发键来源。
- handler 定位证据。
- 参数读取证据。
- blocked 时的缺失证据和下一步。
