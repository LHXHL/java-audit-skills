# Agent-1-recon：路由侦查与 worker 拆分

本文件只给 `java-audit-pipeline` 的 `agent-1-recon` 使用。它负责识别物理模块、入口配置文件和 route worker 拆分边界，不负责提取完整路由，也不估算漏洞风险。

## 职责

- 识别 Java Web 物理模块，例如 `webapps/{module}`、`WEB-INF/web.xml`、`WEB-INF/classes`、`WEB-INF/lib`。
- 统计可精确复核的入口配置数量，例如 JSP 文件数、`web.xml` 数、servlet/filter/listener 配置数、已存在的反编译 `.java` 文件数。
- 生成 route worker 任务拆分，交给 `java-route-mapper` 继续提取完整路由。
- 标注需要下游 route worker 精确解析的文件，不提前写完整路由结论。

## 确定性计数

每个模块的数量必须使用确定性命令或等价文件枚举结果，不能凭框架经验手算：

```text
JSP 文件数：在模块目录下枚举后缀为 .jsp 的文件数量。
已存在反编译 .java 文件数：在模块目录下枚举后缀为 .java 的文件数量。
WEB-INF/lib 依赖文件数：只统计该模块 WEB-INF/lib 目录下一层的 .jar 文件数量。
web.xml：只统计该模块 WEB-INF/web.xml 是否存在。
```

写入报告前必须做总数对账：

```text
各模块 JSP 数求和 = 项目 JSP 文件数
各模块 .java 数求和 = 项目 .java 文件数
各模块 lib 数求和 = 项目 WEB-INF/lib 依赖文件数
```

任一等式不成立时，不得输出“完成”；必须把冲突项写为“不可确认”并说明需要重新枚举。

## 输出文件

写入 `{output_path}/route_mapper/_recon/`：

- `project_overview.md`
- `module_inventory.md`
- `route_worker_tasks.md`

不得只写一个合并的 `recon_report.md` 代替以上 3 个文件。

## project_overview.md 模板

```markdown
# 项目侦查概览

## 1. 输入来源

| 项目 | 值 |
|---|---|
| source_path | {实际路径} |
| 统计时间 | {timestamp} |

## 2. 精确统计

| 指标 | 数量 | 计算依据 |
|---|---:|---|
| 物理模块数 | {number} | {find/文件枚举依据} |
| web.xml 文件数 | {number} | {实际路径列表} |
| JSP 文件数 | {number} | {文件枚举依据} |
| 已存在反编译 .java 文件数 | {number} | {文件枚举依据} |
| WEB-INF/lib 依赖文件数 | {number} | {文件枚举依据} |

## 3. 模块概览

| 模块 | 物理路径 | 类型 | web.xml | JSP 数 | 反编译 .java 数 | lib 数 |
|---|---|---|---|---:|---:|---:|
| {module} | {path} | {Java Web/静态目录/空目录/不可确认} | {有/无} | {number} | {number} | {number} |

## 4. 限制说明

- {无法精确统计的内容；没有则写“无”}
```

## module_inventory.md 模板

```markdown
# 模块入口清单

## {module}

| 类型 | 数量 | 证据路径 | 说明 |
|---|---:|---|---|
| JSP | {number} | {路径或文件清单位置} | {说明} |
| Servlet 定义 | {number 或 未精确统计} | {web.xml 路径} | {说明} |
| Servlet URL 映射 | {number 或 未精确统计} | {web.xml 路径} | {说明} |
| Filter | {number 或 未精确统计} | {web.xml 路径} | {说明} |
| Listener | {number 或 未精确统计} | {web.xml 路径} | {说明} |
| Struts 配置 | {number 或 未精确统计} | {struts.xml 路径列表} | 交给 route worker 精确解析 |
| Spring MVC 配置 | {number 或 未精确统计} | {配置/反编译文件路径} | 交给 route worker 精确解析 |
| WebService 配置 | {number 或 未精确统计} | {web.xml/类文件路径} | 交给 route worker 精确解析 |

### 下游注意事项

- {只写文件范围、框架线索和解析注意事项；不写预估路由数}
```

## route_worker_tasks.md 模板

```markdown
# Route Worker 任务拆分

## 1. 拆分依据

| 项目 | 说明 |
|---|---|
| 拆分粒度 | {按物理模块/按模块+入口类型} |
| worker 数 | {number} |
| 未精确统计项 | {无/列表} |

## 2. 任务清单

### agent-1-{N}: {module}

| 字段 | 值 |
|---|---|
| 模块 | {module} |
| 输入文件 | {web.xml/struts/spring/已反编译 java 路径列表} |
| 输出目录 | 写本轮实际模块输出目录，使用绝对路径或相对 `output_path` 的真实路径，不保留模板占位符 |
| 下游 skill | `java-route-mapper` |
| 必须提取 | {Servlet/Filter/Struts/Spring MVC/WebService/JSP 等} |
| 不确定项 | {未精确统计项或 无} |

#### 交给 route worker 的要求

- 精确提取实际路由、方法、参数和证据路径。
- 不沿用 recon 阶段的框架线索作为路由结论。
- 无法精确枚举时写“未精确统计”，不得写估算。
```

## 强制要求

- recon 阶段不写“预估路由数”。
- 不写 估算词、波浪线、尾随加号、范围数量或模糊数量词。
- 输出文件不得保留 `{...}`、`${...}` 或其他模板占位符；所有路径必须替换为本轮真实路径。
- 数量必须来自文件枚举、XML 节点计数、表格行数或其他可复核证据。
- 未统计或无法确认的数量写“未精确统计”，并说明缺失证据。
- 不生成漏洞结论、鉴权结论、组件风险结论、payload 或 Burp 请求。
- 不把 class 文件名猜测成路由；只能写“交给 route worker 精确解析”。
