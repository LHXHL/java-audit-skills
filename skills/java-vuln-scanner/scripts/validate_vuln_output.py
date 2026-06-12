#!/usr/bin/env python3
"""Boundary checks for java-vuln-scanner final reports."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP = r"\d{8}_\d{6}"
SECTIONS = [
    "## 1. 扫描概述",
    "## 2. 依赖证据统计",
    "## 3. 组件版本命中映射",
    "## 4. 触发面待核查",
    "## 5. 未命中与限制说明",
    "## 6. 审计结论",
]

FORBIDDEN = [
    "## 输出自检",
    "技能源",
    "Claude",
    "测试提示词",
    "模型验收",
    "hard rule",
    "审批",
    "approval",
    "命令失败",
    "权限受限",
    "网络受限",
    "CVSS",
    "PoC",
    "Payload",
    "payload",
    "Burp",
    "```http",
    "JNDI:",
    "ldap://",
    "rmi://",
    "gadget",
    "确认漏洞",
    "条件成立",
    "已验证",
    "可利用",
    "漏洞利用成功",
    "最新修复版本",
    "安全版本",
    "升级到最新版本",
    "占位",
    "已合并到上表",
    "为避免章节结构歧义",
    "...",
    "…",
    "getshell",
    "webshell",
]

OLD_TEMPLATE_MARKERS = [
    "Java 组件漏洞扫描报告",
    "## 扫描概览",
    "## 漏洞详情（按模块分组）",
    "## 依赖列表（按模块分组）",
    "#### 漏洞描述",
    "#### 攻击向量",
    "#### 代码搜索命令",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_report(out_dir: Path) -> Path | None:
    pattern = re.compile(rf"^.+_vuln_scan_{TIMESTAMP}\.md$")
    matches = sorted(path for path in out_dir.glob("*_vuln_scan_*.md") if pattern.match(path.name))
    return matches[0] if len(matches) == 1 else None


def section_names(text: str) -> list[str]:
    return re.findall(r"^##\s+\d+\.\s+.+$", text, flags=re.MULTILINE)


def section_body(text: str, section: str) -> str:
    start = text.find(section)
    if start < 0:
        return ""
    next_section = re.search(r"^##\s+\d+\.\s+", text[start + len(section):], flags=re.MULTILINE)
    if not next_section:
        return text[start:]
    return text[start:start + len(section) + next_section.start()]


def table_count(text: str, label: str) -> int | None:
    match = re.search(rf"^\|\s*{re.escape(label)}\s*\|\s*(\d+)\s*\|", text, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    errors: list[str] = []

    report = find_report(args.output_dir)
    unexpected = sorted(
        path.name
        for path in args.output_dir.iterdir()
        if path.is_file()
        and (
            path.suffix in {".py", ".tmp", ".log", ".json"}
            or path.name.startswith("_")
            or path.name.endswith("_vuln_report.md")
        )
    )
    if unexpected:
        errors.append(f"unexpected generated helper files: {unexpected}")

    if report is None:
        errors.append("expected exactly one timestamped vuln scan report")
    else:
        if "_000000.md" in report.name or "_19700101_" in report.name:
            errors.append("filename uses placeholder timestamp")
        text = read(report)
        folded = text.casefold()
        if "生成时间:" not in text:
            errors.append("missing generation time")
        if "使用 skill: java-vuln-scanner" not in text:
            errors.append("missing skill marker")
        if "生成时间:" in text and ("00:00:00" in text or "1970-01-01" in text):
            errors.append("report uses placeholder generation time")
        if section_names(text) != SECTIONS:
            errors.append(f"sections mismatch: {section_names(text)!r}")
        if "【填写】" in text or "TODO" in text:
            errors.append("placeholder remains")
        if re.search(r"(~\s*\d+|约\s*\d+|大约\s*\d+|若干|多项)", text):
            errors.append("approximate statistics found")
        if re.search(r"(规则|rule)\s*#\s*\d+", text, flags=re.IGNORECASE):
            errors.append("internal rule number found")
        resolved = table_count(text, "已解析依赖")
        matched = table_count(text, "版本命中")
        unmatched = table_count(text, "未命中")
        if None not in (resolved, matched, unmatched) and resolved != matched + unmatched:
            errors.append(
                f"dependency statistic mismatch: 已解析依赖 {resolved} != 版本命中 {matched} + 未命中 {unmatched}"
            )
        stats_body = section_body(text, "## 2. 依赖证据统计")
        version_hit_line = re.search(r"^\|\s*版本命中\s*\|.*$", stats_body, flags=re.MULTILINE)
        if version_hit_line and re.search(r"(组件\+版本|独立治理项|去重后)", version_hit_line.group(0)):
            errors.append("version hit count uses unique component-version wording instead of dependency instances")
        limits_body = section_body(text, "## 5. 未命中与限制说明")
        module_unmatched_counts = [int(n) for n in re.findall(r"[（(]\s*(\d+)\s*个\s*[）)]", limits_body)]
        if unmatched is not None and module_unmatched_counts and sum(module_unmatched_counts) != unmatched:
            errors.append(
                f"unmatched module counts mismatch: {sum(module_unmatched_counts)} != 未命中 {unmatched}"
            )
        for term in FORBIDDEN:
            if term.casefold() in folded:
                errors.append(f"forbidden term found: {term}")
        for marker in OLD_TEMPLATE_MARKERS:
            if marker in text:
                errors.append(f"old template marker found: {marker}")
        statuses = re.findall(r"(版本命中|触发面待核查|环境条件待确认|不可确认|未命中)", text)
        if not statuses:
            errors.append("no allowed status found")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print("[OK] java-vuln-scanner output boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
