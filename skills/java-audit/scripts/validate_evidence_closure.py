#!/usr/bin/env python3
"""校验 java-audit 组件暴露面、漏洞族初筛到候选深审的 evidence 闭环。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CANDIDATE_RE = re.compile(r"VULN-CAND-\d{3}")
FINAL_STATES = {"确认", "降级", "放弃"}
DEEP_AUDIT_STATUSES = {"[x]", "[?]"}
REASON_REQUIRED_STATUSES = {"[-]", "[!]"}


def split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_screening_rows(screening_path: Path) -> list[dict[str, str]]:
    return parse_markdown_table(screening_path, ["漏洞族", "状态"])


def parse_markdown_table(markdown_path: Path, required_headers: list[str]) -> list[dict[str, str]]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    headers: list[str] = []
    rows: list[dict[str, str]] = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue

        cells = split_markdown_row(stripped)
        if all(header in cells for header in required_headers):
            headers = cells
            in_table = True
            continue

        if in_table and is_separator_row(cells):
            continue

        if in_table and headers and len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))

    return rows


def read_current_status(matrix_text: str) -> str:
    match = re.search(r"^当前状态:\s*(.+)$", matrix_text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def read_decision(matrix_text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.*)$", matrix_text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def is_blank_or_placeholder(value: str) -> bool:
    stripped = value.strip()
    return not stripped or "【" in stripped or "】" in stripped


def is_missing_reason(value: str) -> bool:
    stripped = value.strip()
    return is_blank_or_placeholder(stripped) or stripped in {"无", "无。", "N/A", "n/a", "不适用"}


def extract_candidate_ids(value: str) -> list[str]:
    return sorted(set(CANDIDATE_RE.findall(value)))


def has_any_basis(*values: str) -> bool:
    return any(not is_blank_or_placeholder(value) for value in values)


def validate_component_surface(evidence_dir: Path, screening_rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    component_path = evidence_dir / "component-surface.md"
    if not component_path.exists():
        return [f"缺少 Java Web 组件暴露面表: {component_path}"]

    rows = parse_markdown_table(component_path, ["组件", "状态"])
    if not rows:
        return [f"未能解析 Java Web 组件暴露面表: {component_path}"]

    screening_candidate_ids = {
        candidate_id
        for row in screening_rows
        for candidate_id in extract_candidate_ids(row.get("候选 ID", ""))
    }

    for index, row in enumerate(rows, start=1):
        component = row.get("组件", f"第 {index} 行")
        status = row.get("状态", "")
        version_source = row.get("版本/来源", "")
        evidence_location = row.get("证据位置", "")
        usage_point = row.get("配置/使用点", "")
        related_family = row.get("关联漏洞族", "")
        candidate_ids = extract_candidate_ids(row.get("候选 ID", ""))
        handling = row.get("处理说明", "")

        if status == "[ ]":
            errors.append(f"{component} 仍为 [ ] 未检查状态，最终报告前必须闭环")
            continue

        if status in REASON_REQUIRED_STATUSES:
            if not has_any_basis(version_source, evidence_location, usage_point):
                errors.append(f"{component} 标记 {status}，但缺少版本/来源、证据位置或使用点依据")
            if is_blank_or_placeholder(handling):
                errors.append(f"{component} 标记 {status}，但缺少处理说明")
            continue

        if status not in DEEP_AUDIT_STATUSES:
            errors.append(f"{component} 状态非法或不受支持: {status}")
            continue

        if is_blank_or_placeholder(evidence_location):
            errors.append(f"{component} 标记 {status}，但缺少证据位置")
        if is_blank_or_placeholder(related_family):
            errors.append(f"{component} 标记 {status}，但缺少关联漏洞族")
        if not candidate_ids:
            errors.append(f"{component} 标记 {status}，但没有记录 VULN-CAND 候选 ID")
            continue

        for candidate_id in candidate_ids:
            if candidate_id not in screening_candidate_ids:
                errors.append(f"{component} 的 {candidate_id} 未映射到漏洞族初筛表")
            matrix_path = evidence_dir / f"{candidate_id}-evidence-matrix.md"
            if not matrix_path.exists():
                errors.append(f"{component} 的 {candidate_id} 缺少证据矩阵: {matrix_path.name}")

    return errors


def validate_closure(workspace: Path) -> list[str]:
    evidence_dir = workspace if workspace.name == "evidence" else workspace / "evidence"
    errors: list[str] = []

    if not evidence_dir.exists():
        return [f"缺少 evidence 目录: {evidence_dir}"]

    screening_path = evidence_dir / "vulnerability-type-screening.md"
    if not screening_path.exists():
        return [f"缺少漏洞族初筛表: {screening_path}"]

    rows = parse_screening_rows(screening_path)
    if not rows:
        return [f"未能解析漏洞族初筛表: {screening_path}"]

    errors.extend(validate_component_surface(evidence_dir, rows))

    for index, row in enumerate(rows, start=1):
        vuln_family = row.get("漏洞族", f"第 {index} 行")
        status = row.get("状态", "")
        basis = row.get("初筛依据", "")
        next_step = row.get("下一步", "")
        candidate_summary = row.get("发现的具体候选", "")
        candidate_id_cell = row.get("候选 ID", "")
        candidate_ids = extract_candidate_ids(candidate_id_cell)

        if status == "[ ]":
            errors.append(f"{vuln_family} 仍为 [ ] 未检查状态，最终报告前必须闭环")
            continue

        if status in REASON_REQUIRED_STATUSES:
            if is_blank_or_placeholder(basis):
                errors.append(f"{vuln_family} 标记 {status}，但缺少初筛依据")
            if is_blank_or_placeholder(next_step):
                errors.append(f"{vuln_family} 标记 {status}，但缺少下一步/处理说明")
            continue

        if status not in DEEP_AUDIT_STATUSES:
            errors.append(f"{vuln_family} 状态非法或不受支持: {status}")
            continue

        if is_blank_or_placeholder(candidate_summary):
            errors.append(f"{vuln_family} 标记 {status}，但没有填写发现的具体候选")
        if not candidate_ids:
            errors.append(f"{vuln_family} 标记 {status}，但没有记录 VULN-CAND 候选 ID")
            continue

        for candidate_id in candidate_ids:
            matrix_path = evidence_dir / f"{candidate_id}-evidence-matrix.md"
            if not matrix_path.exists():
                errors.append(f"{vuln_family} 的 {candidate_id} 缺少证据矩阵: {matrix_path.name}")
                continue

            matrix_text = matrix_path.read_text(encoding="utf-8")
            current_status = read_current_status(matrix_text)
            if is_blank_or_placeholder(current_status):
                errors.append(f"{candidate_id} 证据矩阵缺少 当前状态")
            elif current_status == "候选":
                errors.append(f"{candidate_id} 仍处于候选状态，不能生成最终报告")
            elif current_status not in FINAL_STATES:
                errors.append(f"{candidate_id} 当前状态必须是 确认/降级/放弃，实际为: {current_status}")

            confirmed = read_decision(matrix_text, "满足确认漏洞门槛")
            if is_blank_or_placeholder(confirmed):
                errors.append(f"{candidate_id} 缺少决策项: 满足确认漏洞门槛")
            elif confirmed not in {"是", "否"}:
                errors.append(f"{candidate_id} 满足确认漏洞门槛必须是 是/否，实际为: {confirmed}")
            elif current_status == "确认" and confirmed != "是":
                errors.append(f"{candidate_id} 状态为确认，但满足确认漏洞门槛不是 是")
            elif current_status in {"降级", "放弃"} and confirmed != "否":
                errors.append(f"{candidate_id} 状态为{current_status}，但满足确认漏洞门槛不是 否")

            reason = read_decision(matrix_text, "降级或放弃原因")
            if current_status in {"降级", "放弃"} and is_missing_reason(reason):
                errors.append(f"{candidate_id} 已{current_status}，但缺少降级或放弃原因")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 java-audit evidence 闭环")
    parser.add_argument("workspace", type=Path, help="审计工作目录，或其 evidence 子目录")
    args = parser.parse_args()

    errors = validate_closure(args.workspace)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print("[OK] java-audit evidence 闭环校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
