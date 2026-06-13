#!/usr/bin/env python3
"""Validate java-sql-audit report boundaries."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


EXPECTED_SECTIONS = [
    "## 1. 审计概述",
    "## 2. 结论统计",
    "## 3. SQL 操作映射",
    "## 4. 候选风险与非漏洞依据",
    "## 5. 风险详情",
    "## 6. 审计结论",
]

STATUSES = ["确认漏洞", "条件成立", "待验证", "不可确认", "非漏洞"]

FORBIDDEN = [
    "## 输出自检",
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
    "xp_cmdshell",
    "LOAD_FILE",
    "INTO OUTFILE",
    "DNSLOG",
    "OOB",
    "边界校验",
    "校验通过",
    "validator",
    "自检通过",
]

CLASS_HEAVY_GAPS = [
    "仅存在 .class 文件",
    "仅存 .class 文件",
    "大量 DAO 实现位于 class 文件中未解析",
    "项目无源码",
    "关键 Manager/DAO 实现",
    "未取得关键类可读实现/反编译方法体",
    "未取得可读反编译方法体",
    "未取得可读实现或反编译方法体",
]

DESTRUCTIVE_SQL = re.compile(
    r"\b(DROP|ALTER|TRUNCATE|INSERT|UPDATE|DELETE)\b",
    flags=re.IGNORECASE,
)

COMPONENT_VERSION = re.compile(
    r"\b(?:Hibernate|Spring|Struts2|Struts|Log4j|MyBatis)\s+\d+\.\d+(?:\.\d+)?\b"
)

APPROXIMATE = re.compile(
    r"(?<![A-Za-z0-9_-])~\s*\d+"
    r"|(?:大约|约)\s*\d+"
    r"|(?<![A-Za-z0-9_-])\d+(?:\.\d+)?(?:个|条|项|处|类|次|行|个方法|个接口)?\+(?!\d)"
)


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
        if len(cells) < 8 or not cells[0].isdigit():
            continue
        status = cells[-1]
        if status in counts:
            counts[status] += 1
        else:
            counts.setdefault("__invalid__", 0)
            counts["__invalid__"] += 1
    return counts


def risk_detail_statuses(text: str) -> list[str]:
    body = section_body(text, "## 5. 风险详情")
    return re.findall(r"^\|\s*结论状态\s*\|\s*([^|]+?)\s*\|", body, flags=re.MULTILINE)


def payload_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(r"^####\s+Payload\s*$", text, flags=re.MULTILINE):
        start = match.end()
        next_heading = re.search(r"^(?:###|---)", text[start:], flags=re.MULTILINE)
        end = start + next_heading.start() if next_heading else len(text)
        blocks.append(text[start:end])
    return blocks


def risk_blocks(text: str) -> list[str]:
    body = section_body(text, "## 5. 风险详情")
    matches = list(re.finditer(r"^###\s+", body, flags=re.MULTILINE))
    blocks: list[str] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        blocks.append(body[match.start():end])
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    if not args.output_dir.exists():
        print(f"[FAIL] output directory does not exist: {args.output_dir}")
        return 1

    reports = sorted(args.output_dir.glob("*_sql_audit_*.md"))
    reports = [p for p in reports if p.name != "ACCEPTANCE.md"]
    if len(reports) != 1:
        print("[FAIL] expected exactly one timestamped SQL audit report")
        return 1

    report = reports[0]
    text = read_text(report)
    errors: list[str] = []

    names = section_names(text)
    if names != EXPECTED_SECTIONS:
        errors.append(f"sections mismatch: {names!r}")

    if "【填写】" in text or "TODO" in text:
        errors.append("placeholder remains")

    if "..." in text:
        errors.append("three-dot ellipsis found")

    if APPROXIMATE.search(text):
        errors.append("approximate count found")

    if COMPONENT_VERSION.search(text):
        errors.append("component version leaks into SQL report")

    for marker in FORBIDDEN:
        if marker.casefold() in text.casefold():
            errors.append(f"forbidden marker found: {marker}")

    for block in payload_blocks(text):
        if DESTRUCTIVE_SQL.search(block):
            context = text.casefold()
            if "回滚" not in text and "备份" not in text and "最小样本" not in text:
                errors.append("DML/DDL payload lacks rollback/backup/minimal-sample limitation")

    counts = mapping_status_counts(text)
    if counts.get("__invalid__"):
        errors.append("SQL 操作映射 contains invalid conclusion status")
    for status in STATUSES:
        expected = stat_count(text, status)
        actual = counts.get(status, 0)
        if expected is not None and expected != actual:
            errors.append(f"stat mismatch for {status}: section 2 has {expected}, mapping has {actual}")

    for detail_status in risk_detail_statuses(text):
        status = detail_status.strip()
        if status not in {"确认漏洞", "条件成立"}:
            errors.append(f"risk detail contains non-confirmed status: {status}")

    unresolved_chain = re.compile(r"是否(?:全部|统一)经由|未逐[个一](?:核对|确认)")
    for block in risk_blocks(text):
        if re.search(r"^\|\s*结论状态\s*\|\s*(确认漏洞|条件成立)\s*\|", block, flags=re.MULTILINE):
            if unresolved_chain.search(block):
                errors.append("confirmed/conditional risk contains unresolved end-to-end chain wording")

    if re.search(r"####\s+Payload", text) and "仅限授权测试环境" not in text:
        errors.append("payload exists without authorization limitation")

    class_heavy_gap = any(marker in text for marker in CLASS_HEAVY_GAPS) or "候选 class 检查结果" in text
    if class_heavy_gap:
        required_markers = ["候选 class 检查结果", "选择原因", "字节码/反编译线索", "仍缺证据"]
        for marker in required_markers:
            if marker not in text:
                errors.append(f"class-heavy limitation lacks marker: {marker}")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1

    print("[OK] java-sql-audit output boundary checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
