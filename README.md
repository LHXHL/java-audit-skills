# Java Audit Skill

## 前言
随着 AI 尤其是大模型的快速发展，模型能力几乎每隔一段时间就会发生明显变化，这也要求 Skill 必须持续更新。如果 Skill 仍然沿用旧模型时代的写法，堆叠大量细节、固定流程和过度说明，反而会限制新模型的理解、推理和发挥。


## 安装

将本仓库中的 `skills/java-audit/` 整个目录放置到 Cloud 或 Codex 可识别的 `.skills/` 目录下，目录名保持为 `java-audit`：

```text
.skills/
└── java-audit/
    ├── SKILL.md
    ├── config.json
    ├── references/
    └── scripts/
```

## 使用
在使用Java Skill的时候，你必须要有强指向性，如：`是否存在SQL注入漏洞?`。

```text
使用 /java-audit 帮我梳理当前源码的路由信息，输出 Markdown 路由报告。
```

```text
使用 /java-audit 帮我梳理当前源码下的鉴权信息，包括认证机制、权限配置和路由鉴权映射。
```

```text
使用 /java-audit 帮我梳理当前源码下的是否存在SQL注入漏洞。
```

```text
使用 /java-audit 帮我梳理当前源码下的是否存在反序列化漏洞。
```

```text
使用 /java-audit 帮我梳理当前源码下的是否存在反序列化漏洞，可以使用多Agent形式分配任务进行审计。
```

```text
使用 /java-audit 帮我梳理当前源码下，分析中间件以及组件是否存在路径穿越漏洞。
```