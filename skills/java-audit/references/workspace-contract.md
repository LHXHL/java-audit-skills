# 审计工作目录规范

## 默认目录

默认创建 `java-audit-workspace/`。如果目标目录已存在，脚本应自动追加序号，例如 `java-audit-workspace-1/`。

## 目录职责

| 目录 | 内容 |
|---|---|
| `tools/` | CFR 等审计工具，只放本次审计需要的工具 |
| `decompiled/` | CFR 反编译输出，按目标文件名分子目录 |
| `reports/` | 最终 Markdown 报告和报告校验结果 |
| `tmp/` | 临时清单、候选列表、中间结果 |
| `logs/` | 工具下载、反编译、校验脚本运行日志 |
| `evidence/` | 证据摘录、关键调用链片段、HTTP 样本 |

## 硬约束

- 不要把反编译结果写回源码目录。
- 不要把下载的 CFR 放到全局路径或项目根目录。
- 不要把临时脚本、日志或草稿报告混在目标项目业务代码中。
- 工作目录中的中间文件不能自动等同于漏洞证据；报告仍需写明文件、方法、行号或方法级证据。

## 建议命令

```bash
python3 skills/java-audit/scripts/init_audit_workspace.py --base <目标项目目录>
```

输出 JSON 中的 `workspace` 字段是后续脚本的输入。
