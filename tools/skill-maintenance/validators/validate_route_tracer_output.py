#!/usr/bin/env python3
"""Boundary checks for java-route-tracer reports.

The validator checks structure, sink categories, and evidence references only.
It does not depend on concrete framework or API names.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FULL_SECTIONS = [
    "## 0. 上游上下文",
    "## 1. 追踪对象",
    "## 2. 请求与参数",
    "## 3. 调用链证据",
    "## 4. Sink 识别",
    "## 5. 参数流向与可控性",
    "## 6. 分支条件与路径状态",
    "## 7. 下游交接结论",
]
SIMPLE_SECTIONS = [
    "## 1. 入口",
    "## 2. 参数",
    "## 3. 调用链",
    "## 4. sink 与可控性",
    "## 5. 交接",
]
INDEX_SECTIONS = [
    "## 1. 批次范围",
    "## 2. 追踪结果",
    "## 3. blocked 闭环",
    "## 4. 结构化产物",
]
FORBIDDEN = [
    "输出自检",
    "技能源",
    "模型验收",
    "测试提示词",
    "Claude",
    "hard rule",
    "CVSS",
    "PoC",
    "Payload",
    "payload",
    "漏洞已确认",
    "确认漏洞",
    "攻击成功",
    "验证成功",
    "可利用",
    "推断为",
    "安全风险",
    "关键发现",
    "修复版本",
    "【填写】",
    "${",
    "...",
    "…",
    "同上",
    "后续代码",
]
ALLOWED_SINKS = {
    "SQL",
    "FILE_READ",
    "FILE_WRITE",
    "XML",
    "DESERIALIZE",
    "COMMAND",
    "HTTP",
    "LDAP",
    "EXPRESSION",
    "RESPONSE",
    "PATH",
    "UNCONFIRMED",
    "NONE",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def section_names(text: str) -> list[str]:
    return re.findall(r"^##\s+\d+\.\s+.+$", text, flags=re.MULTILINE)


def classify(text: str) -> tuple[str, list[str]]:
    sections = section_names(text)
    if sections == FULL_SECTIONS:
        return "full", sections
    if sections == SIMPLE_SECTIONS:
        return "simple", sections
    if sections == INDEX_SECTIONS:
        return "index", sections
    return "unknown", sections


def has_allowed_sink(text: str) -> bool:
    return any(sink in text for sink in ALLOWED_SINKS)


def validate_report(path: Path) -> list[str]:
    errors: list[str] = []
    text = read(path)
    folded = text.casefold()
    kind, sections = classify(text)

    if kind == "unknown":
        errors.append(f"{path}: section mismatch: {sections!r}")
    for term in FORBIDDEN:
        if term.casefold() in folded:
            errors.append(f"{path}: forbidden term found: {term}")
    if not has_allowed_sink(text):
        errors.append(f"{path}: no allowed sink marker found")
    if re.search(r"(规则|rule)\s*#\s*\d+", text, flags=re.IGNORECASE):
        errors.append(f"{path}: internal rule number found")
    if re.search(r"(~\s*\d+|约\s*\d+|大约\s*\d+|若干|多项)", text):
        errors.append(f"{path}: approximate count wording found")
    if "trace helper" not in folded and "manual" not in folded:
        errors.append(f"{path}: missing helper or manual evidence marker")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    reports = sorted(path for path in args.output_dir.rglob("*.md") if path.name != "ACCEPTANCE.md")
    if not reports:
        print("[FAIL] no markdown reports found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for report in reports:
        errors.extend(validate_report(report))

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print("[OK] java-route-tracer output boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
