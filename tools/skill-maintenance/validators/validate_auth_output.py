#!/usr/bin/env python3
"""Boundary checks for java-auth-audit output.

Checks report structure, status consistency, and validation-material bounds
without depending on concrete framework names.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP = r"\d{8}_\d{6}"
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
]
MAIN_SECTIONS = [
    "## 1. 审计范围",
    "## 2. 结论统计",
    "## 3. 鉴权风险映射",
    "## 4. 证据与限制",
    "## 5. 授权复核材料",
    "## 6. 修复与交接",
]
MAPPING_SECTIONS = [
    "## 1. 覆盖统计",
    "## 2. 映射表",
    "## 3. blocked",
]
README_SECTIONS = [
    "## 1. 入口来源",
    "## 2. 鉴权模型",
    "## 3. 交付文件",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_matching(out_dir: Path, suffix: str, errors: list[str]) -> Path | None:
    pattern = re.compile(rf"^.+_{suffix}_{TIMESTAMP}\.md$")
    matches = sorted(path for path in out_dir.glob(f"*_{suffix}_*.md") if pattern.match(path.name))
    if len(matches) > 1:
        errors.append(f"{suffix}: expected one timestamped file, got {len(matches)}")
    return matches[0] if matches else None


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


def check_common(label: str, text: str, expected: list[str], errors: list[str]) -> None:
    got = section_names(text)
    if got != expected:
        errors.append(f"{label}: sections mismatch, got {got!r}")
    if "【填写】" in text or "TODO" in text:
        errors.append(f"{label}: placeholder remains")
    folded = text.casefold()
    for term in FORBIDDEN:
        if term.casefold() in folded:
            errors.append(f"{label}: forbidden term found: {term}")


def mapping_status_counts(text: str) -> dict[str, int]:
    body = section_body(text, "## 3. 鉴权风险映射")
    counts = {status: 0 for status in STATUSES}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6 or not cells[0].isdigit():
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

    out_dir = args.output_dir
    if not out_dir.is_dir():
        print(f"not a directory: {out_dir}", file=sys.stderr)
        return 2

    main_file = find_matching(out_dir, "auth_audit", errors)
    mapping_file = find_matching(out_dir, "auth_mapping", errors)
    readme_file = find_matching(out_dir, "auth_README", errors)

    if main_file:
        text = read(main_file)
        check_common("main", text, MAIN_SECTIONS, errors)
        counts = mapping_status_counts(text)
        if counts.get("__invalid__"):
            errors.append("main: risk mapping contains invalid status")
        for status in STATUSES:
            expected = stat_count(text, status)
            actual = counts.get(status, 0)
            if expected is not None and expected != actual:
                errors.append(f"main: stat mismatch for {status}: section 2 has {expected}, mapping has {actual}")
        material = section_body(text, "## 5. 授权复核材料")
        if "```http" in material and counts.get("确认漏洞", 0) + counts.get("条件成立", 0) == 0:
            errors.append("main: validation request exists without confirmed or conditional item")
    else:
        errors.append("main: expected timestamped file is missing")

    if mapping_file:
        check_common("mapping", read(mapping_file), MAPPING_SECTIONS, errors)
    else:
        errors.append("mapping: expected timestamped file is missing")

    if readme_file:
        check_common("readme", read(readme_file), README_SECTIONS, errors)
    else:
        errors.append("readme: expected timestamped file is missing")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print("[OK] java-auth-audit output boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
