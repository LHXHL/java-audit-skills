# 服务端点入口兼容参考

本文件作为服务端点入口的机制参考。

## 泛化模型

```text
SERVICE_ROOT
  -> SERVICE_CONTRACT
  -> ENTRY_OPERATION
  -> MESSAGE_PARAM
  -> HANDLER_METHOD
```

## 必须区分

- `SERVICE_ROOT` 只是服务根，不是最终入口。
- `ENTRY_OPERATION` 才是下游可追踪的最小入口。
- 消息字段必须从契约、源码、反编译源码或解析逻辑中提取。
- 若服务契约缺失但源码可读，extractor 应从 handler 方法和消息对象收集候选。

## blocked 条件

- 只有服务根，没有 operation 来源。
- 契约文件缺失且 handler 实现不可读。
- operation 由运行时注册或外部表驱动，当前输入无法读取。

blocked 必须记录证据、缺失项和下一步，不得只写“待分析”。
