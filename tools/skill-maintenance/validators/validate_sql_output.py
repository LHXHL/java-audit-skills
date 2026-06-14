#!/usr/bin/env python3
"""Validate java-sql-audit report boundaries.

This validator checks report schema and status consistency. It intentionally
does not check concrete database/framework/library names.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXPECTED_SECTIONS = [
    "## 1. 审计范围",
    "## 2. 结论统计",
    "## 3. SQL 操作映射",
    "## 4. 证据与限制",
    "## 5. 授权复核材料",
    "## 6. 修复与交接",
]
STATUSES = ["确认漏洞", "条件成立", "待验证", "不可确认", "非漏洞"]
FORBIDDEN = [
    "输出自检",
    "技能源校验",
    "测试提示词",
    "模型自检",
    "Claude 运行状态",
    "hard rule",
    "CVSS",
    "CVE-",
    "修复版本",
    "漏洞利用成功",
    "验证成功",
    "网络受限",
    "命令受限",
    "边界校验",
    "校验通过",
    "validator",
    "自检通过",
]
APPROXIMATE = re.compile(
    r"(?<![A-Za-z0-9_-])~\s*\d+"
    r"|(?:大约|约)\s*\d+"
    r"|(?<![A-Za-z0-9_-])\d+(?:\.\d+)?(?:个|条|项|处|类|次|行|个方法|个接口)?\+(?!\d)"
)
DESTRUCTIVE_QUERY = re.compile(r"\b(DROP|ALTER|TRUNCATE|INSERT|UPDATE|DELETE)\b", flags=re.IGNORECASE)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


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


def stat_count(text: str, status: str) -> int | None:
    body = section_body(text, "## 2. 结论统计")
    match = re.search(rf"^\|\s*{re.escape(status)}\s*\|\s*(\d+)\s*\|", body, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def mapping_status_counts(text: str) -> dict[str, int]:
    body = section_body(text, "## 3. SQL 操作映射")
    counts = {status: 0 for status in STATUSES}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        status = cells[-1]
        if status in counts:
            counts[status] += 1
        else:
            counts["__invalid__"] = counts.get("__invalid__", 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    if not args.output_dir.exists():
        print(f"[FAIL] output directory does not exist: {args.output_dir}")
        return 1

    reports = [p for p in sorted(args.output_dir.glob("*_sql_audit_*.md")) if p.name != "ACCEPTANCE.md"]
    if len(reports) != 1:
        print("[FAIL] expected exactly one timestamped SQL audit report")
        return 1

    text = read_text(reports[0])
    errors: list[str] = []

    if section_names(text) != EXPECTED_SECTIONS:
        errors.append(f"sections mismatch: {section_names(text)!r}")
    if "【填写】" in text or "TODO" in text:
        errors.append("placeholder remains")
    if "..." in text:
        errors.append("three-dot ellipsis found")
    if APPROXIMATE.search(text):
        errors.append("approximate count found")
    for marker in FORBIDDEN:
        if marker.casefold() in text.casefold():
            errors.append(f"forbidden marker found: {marker}")

    counts = mapping_status_counts(text)
    if counts.get("__invalid__"):
        errors.append("SQL 操作映射 contains invalid conclusion status")
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
        if DESTRUCTIVE_QUERY.search(material) and not any(term in text for term in ["回滚", "备份", "最小样本"]):
            errors.append("destructive query material lacks rollback/backup/minimal-sample limitation")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[OK] java-sql-audit output boundary checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
