# 参数可控性与 sink 分类

本文件定义参数可控性、sink 分类和下游交接判断框架。

## sink category

| category | 说明 | 建议下游 |
|----------|------|----------|
| `SQL` | 参数进入查询、过滤、排序、聚合或动态数据访问构造 | `java-sql-audit` |
| `FILE_READ` | 参数影响本地、远程或资源读取目标 | `java-file-read-audit` |
| `FILE_WRITE` | 参数影响上传、导入、导出、覆盖或保存目标 | `java-file-upload-audit` |
| `XML` | 参数进入 XML 类解析、转换、校验或对象绑定 | `java-xxe-audit` |
| `DESERIALIZE` | 参数进入对象构造、对象还原、多态绑定或二进制对象读取 | `java-deserialization-audit` |
| `COMMAND` | 参数进入命令、脚本、模板执行或系统调用类能力 | 人工或后续专项 |
| `HTTP` | 参数影响外连地址、请求头、请求体或代理目标 | 人工或后续专项 |
| `EXPRESSION` | 参数进入表达式、模板、脚本或规则执行器 | 人工或后续专项 |
| `RESPONSE` | 参数进入响应体、响应头、跳转或下载名 | 人工或后续专项 |
| `PATH` | 参数只影响路径构造，尚未观察到读写动作 | 文件类专项候选 |
| `UNCONFIRMED` | 到达缺失实现、接口、代理、动态调用或不可读代码 | 补源码或反编译 |
| `NONE` | 已追踪到确定终点，未见敏感 sink | 无 |

## helper 输出字段

trace helper 应优先输出机器可读证据：

```json
{
  "trace_id": "TRACE-001",
  "route_id": "ROUTE-001",
  "param": "REQUEST_PARAM",
  "call_edges": [
    {
      "from": "CALL_NODE",
      "to": "CALL_NODE",
      "argument_map": {"REQUEST_PARAM": "LOCAL_VALUE"},
      "evidence": "file:line"
    }
  ],
  "sink_candidates": [
    {
      "category": "SINK_CATEGORY",
      "location": "file:line",
      "argument": "LOCAL_VALUE",
      "confidence": "high"
    }
  ]
}
```

## 可控性等级

| 等级 | 条件 |
|------|------|
| 完全可控 | 外部输入未经覆盖、固定映射或强校验到达 sink |
| 条件可控 | 需要满足分支、状态、格式、角色、配置或数据前置条件 |
| 受限可控 | 输入仍可影响目标，但被白名单、枚举、规范化或映射表限制 |
| 不可控 | sink 参数完全由服务端常量、固定配置或不可由请求影响的数据决定 |
| 未确认 | 缺源码、缺实现、缺配置或 helper 证据不足 |

## 必查问题

- 参数是否在中间层改名、拆分、拼接、转换或覆盖。
- 是否存在默认值覆盖、白名单、枚举、规范化、类型转换、提前返回或异常分支。
- sink 参数来自请求、配置、数据库、缓存、会话还是服务端常量。
- 接口、抽象方法、代理、配置映射、动态调用是否已追到真实实现。
- helper 是否给出可复核文件位置。

## 禁止

- 不得只凭业务方法名推断具体 sink。
- 不得把 `UNCONFIRMED` 写成具体漏洞。
- 不得把参数到达 sink 等同于漏洞成立。
- 不得在通用模板中写真实 API 示例。
