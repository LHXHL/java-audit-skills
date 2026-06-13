# Java Audit Skills 维护说明

本目录只放仓库维护、质检和回归检查资源，不放单个 skill 正常运行时必须加载的业务逻辑。

## 脚本分类

### 运行时脚本

运行时脚本保留在对应 skill 的 `scripts/` 下。

适合放在 skill-local `scripts/` 的内容：

- skill 执行过程中会直接调用的确定性逻辑。
- 会生成正式中间产物或报告基础数据的脚本。
- 与该 skill 的 `references/`、规则库或资产强绑定的脚本。

示例：

- `skills/java-vuln-scanner/scripts/scan_dependencies.py`

### 维护/质检脚本

维护/质检脚本统一放在 `tools/skill-maintenance/validators/`。

适合放在这里的内容：

- 检查报告章节、统计一致性、禁用字段、占位符、估算数字和模板边界。
- 检查 pipeline 目录结构、QA 产物、阶段门禁和跨 skill 输出边界。
- 只用于本地维护、回归检查或 Claude 测试后的人工验收辅助。

维护脚本不能替代人工审计判断，也不能把“validator 通过”写入正式审计报告。

当前维护脚本：

| 脚本 | 用途 |
|---|---|
| `validators/validate_auth_output.py` | 检查 `java-auth-audit` 三文件输出边界 |
| `validators/validate_sql_output.py` | 检查 `java-sql-audit` 报告章节、统计和 payload 边界 |
| `validators/validate_vuln_output.py` | 检查 `java-vuln-scanner` 组件版本证据报告 |
| `validators/validate_pipeline_output.py` | 检查 `java-audit-pipeline` 目录、QA 和阶段门禁 |
| `validators/validate_file_read_output.py` | 检查 `java-file-read-audit` 报告边界 |
| `validators/validate_route_tracer_output.py` | 检查 `java-route-tracer` 输出边界 |

## Skill 编写标准

### `SKILL.md`

- `description` 写“何时加载”，不是功能介绍。
- 主文档只保留当前定位、触发条件、不触发条件、成功标准、工作流、强制规则、gotchas、停止/切换条件和 eval 样例。
- 不堆长篇漏洞背景、工具教程、完整模板或大量规则细节。
- 新增或重写内容默认用中文；类名、方法名、配置键、CVE、命令和路径保持原文。
- 漏洞类 skill 的确认漏洞或条件成立项需要给出可交付给开发单位的验证材料，包括 Burp Suite 请求和 payload；待验证、不可确认或非漏洞项不得补写验证材料。
- 组件版本证据类 skill 不输出 Burp、payload、PoC、CVSS、具体修复版本或确认性漏洞结论。

### `references/`

- 大段检测规则、模板、框架细节、payload 注意事项、漏洞背景和输出格式放入 `references/`。
- `SKILL.md` 只说明何时读取哪个 reference。
- 模板不得诱导模型编造 CVE、CVSS、修复版本、PoC、利用链或不可验证结论。
- reference 职责混杂时应拆分或重命名。

### `scripts/`

- 只有运行期会被 skill 调用的脚本留在 skill-local `scripts/`。
- 只做维护检查、回归检查、输出验收的脚本放到本目录 `validators/`。

## Claude 真实运行测试

每个 skill 修改完成后，应使用普通用户视角的 prompt 调用 `claude -p`，不要在 prompt 中加入“自检”“测试边界”“请验证你是否遵守模板”等额外提示。

示例：

```bash
claude --add-dir /path/to/java-audit-skills \
  --add-dir /path/to/target-source \
  --disable-slash-commands \
  --permission-mode acceptEdits \
  -p '请使用 /path/to/java-audit-skills/skills/java-sql-audit 审计 /path/to/target-source 的 Java SQL 注入风险，并把报告输出到 /path/to/java-audit-skills/test_outputs/java-sql-audit。'
```

测试输出目录建议放在仓库根目录的 `test_outputs/<skill-name>/`。该目录已被 `.gitignore` 忽略，不应提交到公开仓库。

## 结果检查流程

1. 删除该 skill 上一次生成的明确测试报告或测试输出目录；不要删除源码、skill、references、运行期脚本或未知文件。
2. 运行 `claude -p`，等待进程完整结束；长时间无输出时继续等待或轮询，不提前终止。
3. 阅读 Claude 生成的报告，确认是否正确触发当前 skill、是否误用相邻 skill、是否遵守模板。
4. 对适用的 skill 运行维护脚本，例如：

```bash
python3 tools/skill-maintenance/validators/validate_sql_output.py test_outputs/java-sql-audit
python3 tools/skill-maintenance/validators/validate_pipeline_output.py test_outputs/java-audit-pipeline
```

5. 人工复核 validator 无法判断的内容：
   - 证据路径、文件位置、方法名和数据流是否可复核。
   - 候选风险是否被错误写成确认漏洞。
   - 确认漏洞或条件成立项是否包含必要 Burp Suite 请求和 payload。
   - 不可确认项是否说明缺失证据和补证路径。
   - 是否存在估算数量、旧模板痕迹、占位符、模型自检话术或不可公开信息。
6. 不合格时回到当前 skill 修改 `SKILL.md`、`references/` 或运行期 `scripts/`，删除旧测试输出后重新运行 `claude -p`。
7. 合格后记录验收结论，但不要把 `test_outputs/` 提交到公开仓库。

## 提交前检查

提交前至少运行：

```bash
python3 -m py_compile tools/skill-maintenance/validators/*.py
git diff --check
git status --short
```

如果修改了运行时脚本，也应对对应脚本做 `py_compile` 或等价的语法检查。
