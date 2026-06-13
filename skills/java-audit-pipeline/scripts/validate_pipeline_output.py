#!/usr/bin/env python3
"""Validate java-audit-pipeline generated outputs for boundary regressions."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


EXPECTED_DIRS = [
    "route_mapper",
    "auth_audit",
    "vuln_report",
    "cross_analysis",
    "route_tracer",
    "sql_audit",
    "xxe_audit",
    "file_upload_audit",
    "file_read_audit",
    "deserialization_audit",
    "qa_reports",
    "scripts",
    "tmp",
    "decompiled",
]

GLOBAL_FORBIDDEN = [
    "输出自检",
    "自检",
    "自检通过",
    "验收标记",
    "模型验收",
    "测试提示词",
    "hard rule",
    "自报",
    "shutdown",
    "通过（修复后）",
    "CVSS",
    "修复版本",
    "整改版本",
    "安全版本",
]

BLOCKED_FORBIDDEN = [
    "shutdown_request",
    "teammate protocol frame",
    "TeamCreate",
    "TeamDelete",
    "TaskCreate",
    "TaskUpdate",
    "Agent/",
    "/Task",
    ".claude/teams",
    "active member",
    "cleanup",
]

COMPONENT_FORBIDDEN = [
    "Burp",
    "payload",
    "Payload",
    "PoC",
    "CVSS",
    "修复版本",
    "整改版本",
    "安全版本",
    "建议升级",
    "建议迁移",
    "建议版本",
    "建议升级版本",
    "内置规则建议",
    "已确认漏洞",
    "漏洞已确认",
    "攻击成功",
    "验证成功",
    "可直接利用",
]

PLACEHOLDER_PATTERNS = [
    re.compile(r"\{(?:source_path|output_path|batch_id|project_name|paths|number|stage_or_agent|expected|actual|skill|stage|reason|module|batch|agent_id)(?:[:：][^}]*)?\}"),
    re.compile(r"\$\{(?:source_path|output_path|batch_id|project_name|paths|number|component|version|route|method|status|finding_id)[^}]*\}"),
    re.compile(r"【填写】"),
    re.compile(r"[({（]\s*待(?:生成|填写|补充|确认)[^)}）]*[)}）]"),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def add_error(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path}: {message}")


def check_global(output_dir: Path, errors: list[str]) -> None:
    for md in output_dir.rglob("*.md"):
        text = read_text(md)
        for marker in GLOBAL_FORBIDDEN:
            if marker in text:
                add_error(errors, md, f"contains forbidden marker {marker!r}")
        if re.search(r"(升级|迁移)\s*[A-Za-z0-9_.:-]*\s*(到|至)\s*[A-Za-z0-9_.+-]*\d", text):
            add_error(errors, md, "contains concrete upgrade or migration target version")
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(text):
                add_error(errors, md, f"contains unresolved placeholder matching {pattern.pattern!r}")


def check_component_boundary(output_dir: Path, errors: list[str]) -> None:
    candidates: list[Path] = []
    for rel in [
        "cross_analysis/component_version_evidence.md",
        "cross_analysis/component_vulnerabilities.md",
    ]:
        p = output_dir / rel
        if p.exists():
            candidates.append(p)
    vuln_dir = output_dir / "vuln_report"
    if vuln_dir.exists():
        candidates.extend(vuln_dir.rglob("*.md"))

    for path in candidates:
        text = read_text(path)
        for marker in COMPONENT_FORBIDDEN:
            if marker in text:
                add_error(errors, path, f"component evidence contains forbidden term {marker!r}")
        if re.search(r"(升级到|迁移到)\s*[A-Za-z0-9_.+-]+", text):
            add_error(errors, path, "component evidence contains upgrade or migration target version")
        if (
            "不构成漏洞确认" not in text
            and "非漏洞确认" not in text
            and "版本命中不等于业务风险真实成立" not in text
        ):
            add_error(errors, path, "component evidence lacks an explicit non-confirmation limitation")


def check_approximate_pipeline_counts(output_dir: Path, errors: list[str]) -> None:
    candidates = list(output_dir.rglob("*.md"))
    approx = re.compile(
        r"(?<![A-Za-z0-9_-])~\s*\d+"
        r"|(?<![A-Za-z0-9_-])\d+(?:\.\d+)?(?:KB|MB|GB|TB|个|条|项|处|类|次)?\+(?!\d)"
        r"|(?:大约|约)\s*\d+"
    )
    for path in candidates:
        text = read_text(path)
        if approx.search(text):
            add_error(errors, path, "approximate count found in pipeline gate output")


def check_team_execution(output_dir: Path, errors: list[str]) -> None:
    quality = output_dir / "quality_report.md"
    blocked = output_dir / "pipeline_blocked.md"
    team = output_dir / "team_execution.md"
    if not quality.exists() and not blocked.exists() and team.exists():
        add_error(errors, team, "team_execution.md exists without quality_report.md or pipeline_blocked.md")

    if blocked.exists() and not team.exists():
        add_error(errors, team, "blocked pipeline must preserve team_execution.md capability record")

    if team.exists():
        text = read_text(team)
        agent_creation_available = re.search(r"\|\s*agent 创建能力\s*\|\s*可用\s*\|", text) is not None
        lifecycle_available = re.search(r"\|\s*完整生命周期能力\s*\|\s*可用\s*\|", text) is not None
        if blocked.exists() and agent_creation_available:
            add_error(errors, team, "blocked capability record must not mark agent creation as available without external evidence")
        if lifecycle_available and (blocked.exists() or not quality.exists()):
            add_error(errors, team, "claims full team lifecycle is available without a completed quality report")
        if blocked.exists() and re.search(r"TeamCreate|TeamDelete|TaskCreate|TaskUpdate|Agent\s*工具|创建类工具", text):
            add_error(errors, team, "blocked capability record must not cite tool names as lifecycle evidence")

    if not quality.exists() or blocked.exists():
        return

    if not team.exists():
        add_error(errors, output_dir, "missing team_execution.md for completed team pipeline")
    else:
        text = read_text(team)
        required = [
            "Claude Team 执行记录",
            "## 1. 能力确认",
            "## 2. Agent 拓扑",
            "## 4. 质检员记录",
            "agent-7",
            "完整生命周期能力",
        ]
        for marker in required:
            if marker not in text:
                add_error(errors, team, f"missing team execution marker {marker!r}")

    qa_dir = output_dir / "qa_reports"
    if qa_dir.exists():
        qa_files = [p.name for p in qa_dir.glob("*.md")]
        agent_named = [name for name in qa_files if name.startswith("qa_report_agent-")]
        stage_named = [name for name in qa_files if name.startswith("qa_report_stage")]
        if not agent_named:
            add_error(errors, qa_dir, "missing agent-named QA reports")
        if stage_named:
            add_error(errors, qa_dir, f"stage-named QA reports are not valid team QA evidence: {stage_named}")


def check_initialization(output_dir: Path, errors: list[str]) -> None:
    if not output_dir.exists():
        return

    required_dirs = [
        "route_mapper/_recon",
        "route_mapper/.status",
        "auth_audit",
        "vuln_report",
        "cross_analysis",
        "route_tracer",
        "sql_audit",
        "xxe_audit",
        "file_upload_audit",
        "file_read_audit",
        "deserialization_audit",
        "qa_reports",
        "scripts",
        "tmp",
        "decompiled/cache",
    ]
    for rel in required_dirs:
        path = output_dir / rel
        if not path.is_dir():
            add_error(errors, path, "missing required initialization directory")

    config = output_dir / "scripts" / "pipeline_config.json"
    if not config.exists():
        add_error(errors, config, "missing pipeline initialization config")
        return

    try:
        data = json.loads(read_text(config))
    except json.JSONDecodeError as exc:
        add_error(errors, config, f"invalid JSON: {exc}")
        return

    required_keys = ["schema_version", "source_path", "output_path", "max_concurrent_agents", "audit_scope", "created_at"]
    for key in required_keys:
        if key not in data:
            add_error(errors, config, f"missing config key {key!r}")
    max_agents = data.get("max_concurrent_agents")
    if not isinstance(max_agents, int) or not 2 <= max_agents <= 10:
        add_error(errors, config, "max_concurrent_agents must be an integer between 2 and 10")

    plan = output_dir / "pipeline_plan.md"
    if not plan.exists():
        add_error(errors, plan, "missing pipeline execution plan")
    else:
        text = read_text(plan)
        for marker in ["# 审计流水线执行计划", "## 1. 初始化", "## 2. 阶段计划", "## 3. 门禁状态"]:
            if marker not in text:
                add_error(errors, plan, f"missing plan marker {marker!r}")


def check_recon_output_shape(output_dir: Path, errors: list[str]) -> None:
    recon_dir = output_dir / "route_mapper" / "_recon"
    if not recon_dir.exists():
        return

    if (recon_dir / "recon_report.md").exists():
        add_error(errors, recon_dir / "recon_report.md", "agent-1-recon must not replace the three recon files with recon_report.md")

    expected = [
        "project_overview.md",
        "module_inventory.md",
        "route_worker_tasks.md",
    ]
    existing_md = list(recon_dir.glob("*.md"))
    if existing_md:
        missing = [name for name in expected if not (recon_dir / name).exists()]
        if missing:
            add_error(errors, recon_dir, f"missing expected recon files: {', '.join(missing)}")


def check_stage_gate_consistency(output_dir: Path, errors: list[str]) -> None:
    qa_dir = output_dir / "qa_reports"
    blocked = output_dir / "pipeline_blocked.md"
    team = output_dir / "team_execution.md"
    team_text = read_text(team) if team.exists() else ""
    plan = output_dir / "pipeline_plan.md"
    plan_text = read_text(plan) if plan.exists() else ""
    cross_files = list((output_dir / "cross_analysis").glob("*.md")) if (output_dir / "cross_analysis").exists() else []
    trace_files = list((output_dir / "route_tracer").rglob("*.md")) if (output_dir / "route_tracer").exists() else []

    failing_qa: list[Path] = []
    if qa_dir.exists():
        for qa in qa_dir.glob("qa_report_agent-*.md"):
            text = read_text(qa)
            if "状态：不通过" in text or "状态: 不通过" in text or re.search(r"\|\s*不通过\s*\|", text):
                failing_qa.append(qa)

    if failing_qa and not blocked.exists():
        empty_rework = re.search(r"\|\s*无\s*\|\s*0\s*\|\s*无\s*\|\s*无\s*\|\s*无\s*\|", team_text) is not None
        handled = "返工记录" in team_text and not empty_rework and any(
            qa.stem.replace("qa_report_", "") in team_text for qa in failing_qa
        )
        if not handled:
            for qa in failing_qa:
                add_error(errors, qa, "failing QA is not followed by rework evidence or pipeline_blocked.md")

    if qa_dir.exists() and plan.exists():
        qa_files = [p.name for p in qa_dir.glob("qa_report_agent-*.md")]
        if qa_files and "待生成" in plan_text:
            add_error(errors, plan, "pipeline_plan.md still contains pending QA evidence after QA reports were generated")

    if cross_files or trace_files:
        required_qa = [
            "qa_report_agent-1-merge.md",
            "qa_report_agent-2-auth-audit.md",
            "qa_report_agent-3-vuln-scanner.md",
        ]
        for name in required_qa:
            if not (qa_dir / name).exists():
                add_error(errors, qa_dir / name, "missing required QA before downstream stage")

        route_worker_qas = [
            p
            for p in qa_dir.glob("qa_report_agent-1-*.md")
            if p.name not in {"qa_report_agent-1-recon.md", "qa_report_agent-1-merge.md"}
        ]
        if not route_worker_qas:
            add_error(errors, qa_dir, "missing route worker QA before cross_analysis or route_tracer")

    if trace_files:
        for name in ["qa_report_agent-4a-risk-classifier.md", "qa_report_agent-4b-evidence-aggregator.md"]:
            if not (qa_dir / name).exists():
                add_error(errors, qa_dir / name, "missing stage2 QA before route_tracer")


def check_vuln_report_with_skill_validator(output_dir: Path, errors: list[str]) -> None:
    vuln_dir = output_dir / "vuln_report"
    if not vuln_dir.exists():
        return
    blocked = output_dir / "pipeline_blocked.md"
    if blocked.exists() and not any(vuln_dir.rglob("*.md")):
        return
    skills_dir = Path(__file__).resolve().parent.parent.parent
    validator = skills_dir / "java-vuln-scanner" / "scripts" / "validate_vuln_output.py"
    if not validator.exists():
        add_error(errors, vuln_dir, "java-vuln-scanner validator is missing")
        return
    proc = subprocess.run(
        [sys.executable, str(validator), str(vuln_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = "\n".join(line for line in (proc.stderr + proc.stdout).splitlines() if line.strip())
        add_error(errors, vuln_dir, f"java-vuln-scanner validator failed: {detail}")


def check_pipeline_shape(output_dir: Path, errors: list[str]) -> None:
    if not output_dir.exists():
        add_error(errors, output_dir, "output directory does not exist")
        return

    has_plan = (output_dir / "pipeline_plan.md").exists()
    has_quality = (output_dir / "quality_report.md").exists()
    has_blocked = (output_dir / "pipeline_blocked.md").exists()

    existing_dirs = {p.name for p in output_dir.iterdir() if p.is_dir()}
    if existing_dirs and not has_blocked:
        missing = [name for name in EXPECTED_DIRS if name not in existing_dirs]
        if missing:
            add_error(errors, output_dir, f"missing expected pipeline directories: {', '.join(missing)}")

    if not (has_plan or has_quality or has_blocked):
        add_error(errors, output_dir, "expected pipeline_plan.md, pipeline_blocked.md, or quality_report.md")

    quality = output_dir / "quality_report.md"
    if quality.exists():
        text = read_text(quality)
        required = [
            "# 审计流水线质量报告",
            "## 1. 执行概览",
            "## 2. 阶段状态",
            "## 3. 数据一致性",
            "## 4. 发现汇总索引",
        ]
        for section in required:
            if section not in text:
                add_error(errors, quality, f"missing required section {section!r}")
        if not re.search(r"^##\s+\d+\.\s+阻塞与限制", text, flags=re.MULTILINE):
            add_error(errors, quality, "missing 阻塞与限制 section")

    blocked = output_dir / "pipeline_blocked.md"
    if blocked.exists():
        text = read_text(blocked)
        required = [
            "# 审计流水线阻塞报告",
            "## 1. 已完成阶段",
            "## 2. 阻塞点",
            "## 3. 未运行阶段",
            "## 4. 继续条件",
        ]
        for section in required:
            if section not in text:
                add_error(errors, blocked, f"missing required section {section!r}")
        if re.search(r"^##\s+5\.", text, flags=re.MULTILINE):
            add_error(errors, blocked, "blocked report must keep exactly four numbered sections")
        for marker in BLOCKED_FORBIDDEN:
            if marker in text:
                add_error(errors, blocked, f"blocked report exposes internal team lifecycle detail {marker!r}")
        if re.search(r"阶段[234].*\|\s*通过\s*\|", text):
            add_error(errors, blocked, "blocked report marks an unrun downstream stage as passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    check_pipeline_shape(args.output_dir, errors)
    if args.output_dir.exists():
        check_initialization(args.output_dir, errors)
        check_global(args.output_dir, errors)
        check_component_boundary(args.output_dir, errors)
        check_approximate_pipeline_counts(args.output_dir, errors)
        check_team_execution(args.output_dir, errors)
        check_recon_output_shape(args.output_dir, errors)
        check_stage_gate_consistency(args.output_dir, errors)
        check_vuln_report_with_skill_validator(args.output_dir, errors)

    if errors:
        print("pipeline output validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("pipeline output validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
