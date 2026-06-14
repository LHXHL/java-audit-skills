#!/usr/bin/env python3
"""Boundary checks for java-file-read-audit output.

The validator checks structure and status consistency only. It intentionally
does not look for concrete framework names or file-reading API names.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP = r"\d{8}_\d{6}"
SECTIONS = [
    "## 1. 审计范围",
    "## 2. 结论统计",
    "## 3. 文件读取映射",
    "## 4. 证据与限制",
    "## 5. 授权复核材料",
    "## 6. 修复与交接",
]
STATUSES = ["确认漏洞", "条件成立", "待验证", "不可确认", "非漏洞"]
FORBIDDEN = [
    "输出自检",
    "技能源",
    "CVSS",
    "CVE-",
    "修复版本",
    "Claude",
    "测试提示词",
    "模型验收",
    "hard rule",
    "PoC",
    "validator",
    "自检通过",
]
SENSITIVE_MATERIAL_TERMS = [
    "系统敏感路径",
    "批量枚举",
    "批量读取",
    "生产环境执行",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_report(out_dir: Path) -> Path | None:
    pattern = re.compile(rf"^.+_file_read_audit_{TIMESTAMP}\.md$")
    matches = sorted(path for path in out_dir.glob("*_file_read_audit_*.md") if pattern.match(path.name))
    return matches[0] if len(matches) == 1 else None


def section_names(text: str) -> list[str]:
    return re.findall(r"^##\s+\d+\.\s+.+$", text, flags=re.MULTILINE)


def section_body(text: str, heading: str) -> str:
    start = text.find(heading)
    if start == -1:
        return ""
    next_match = re.search(r"^##\s+\d+\.\s+", text[start + len(heading):], flags=re.MULTILINE)
    if not next_match:
        return text[start:]
    return text[start:start + len(heading) + next_match.start()]


def mapping_status_counts(text: str) -> dict[str, int]:
    body = section_body(text, "## 3. 文件读取映射")
    counts = {status: 0 for status in STATUSES}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 8 or not cells[0].isdigit():
            continue
        status = cells[-1]
        if status in counts:
            counts[status] += 1
        else:
            counts["__invalid__"] = counts.get("__invalid__", 0) + 1
    return counts


def stat_count(text: str, status: str) -> int | None:
    body = section_body(text, "## 2. 结论统计")
    match = re.search(rf"^\|\s*{re.escape(status)}\s*\|\s*(\d+)\s*\|", body, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    errors: list[str] = []

    report = find_report(args.output_dir)
    if report is None:
        errors.append("expected exactly one timestamped file-read audit report")
    else:
        text = read_text(report)
        folded = text.casefold()
        if section_names(text) != SECTIONS:
            errors.append(f"sections mismatch: {section_names(text)!r}")
        if "【填写】" in text or "TODO" in text:
            errors.append("placeholder remains")
        for term in FORBIDDEN:
            if term.casefold() in folded:
                errors.append(f"forbidden term found: {term}")
        for term in SENSITIVE_MATERIAL_TERMS:
            if term in section_body(text, "## 5. 授权复核材料"):
                errors.append(f"unsafe validation material term found: {term}")

        counts = mapping_status_counts(text)
        if counts.get("__invalid__"):
            errors.append("mapping contains invalid status")
        for status in STATUSES:
            expected = stat_count(text, status)
            actual = counts.get(status, 0)
            if expected is not None and expected != actual:
                errors.append(f"stat mismatch for {status}: section 2 has {expected}, mapping has {actual}")

        material = section_body(text, "## 5. 授权复核材料")
        if "```http" in material:
            final_count = counts.get("确认漏洞", 0) + counts.get("条件成立", 0)
            if final_count == 0:
                errors.append("validation request exists without confirmed or conditional item")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print("[OK] java-file-read-audit output boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
