#!/usr/bin/env python3
"""校验 java-audit Markdown 报告的边界。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1. 审计概述",
    "## 2. 确认漏洞",
    "## 3. 高风险线索 / 下一步人工验证",
    "## 4. 覆盖范围与限制",
]

REQUIRED_FIELDS = [
    "- 严重等级:",
    "- 受影响入口:",
    "- 参数来源:",
    "- Source-to-Sink 传播链:",
    "- Sink:",
    "- 触发条件:",
    "- 防护判断:",
    "- Payload:",
    "- 影响:",
    "- 证据:",
    "- 修复建议:",
]

FORBIDDEN_IN_CONFIRMED = [
    "疑似",
    "待验证",
    "可能存在",
    "无法确认",
    "需要人工确认",
    "高风险线索",
    "下一步人工验证",
]


def section_names(text: str) -> list[str]:
    return re.findall(r"^##\s+\d+\.\s+.+$", text, flags=re.MULTILINE)


def section_body(text: str, section: str) -> str:
    start = text.find(section)
    if start < 0:
        return ""
    match = re.search(r"^##\s+\d+\.\s+", text[start + len(section):], flags=re.MULTILINE)
    if not match:
        return text[start:]
    return text[start:start + len(section) + match.start()]


def vulnerability_blocks(confirmed_body: str) -> list[str]:
    matches = list(re.finditer(r"^###\s+.+$", confirmed_body, flags=re.MULTILINE))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(confirmed_body)
        blocks.append(confirmed_body[match.start():end])
    return blocks


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    if "【" in text or "】" in text:
        errors.append("报告仍包含模板占位符")
    if section_names(text) != REQUIRED_SECTIONS:
        errors.append(f"章节不匹配: {section_names(text)!r}")

    confirmed = section_body(text, "## 2. 确认漏洞")
    if not confirmed:
        errors.append("缺少确认漏洞章节")
        return errors

    blocks = vulnerability_blocks(confirmed)
    if not blocks and "未发现确认漏洞" not in confirmed:
        errors.append("确认漏洞章节既没有漏洞块，也没有写明未发现确认漏洞")

    for block in blocks:
        title = block.splitlines()[0]
        if not re.search(r"^###\s+VULN-\d{3}\s+", title):
            errors.append(f"漏洞标题编号格式错误: {title}")
        for field in REQUIRED_FIELDS:
            if field not in block:
                errors.append(f"{title} 缺少字段: {field}")
        if "```http" not in block:
            errors.append(f"{title} 缺少 http fenced 原始请求包")
        for term in FORBIDDEN_IN_CONFIRMED:
            if term in block:
                errors.append(f"{title} 在确认漏洞中包含降级词: {term}")
        chain_match = re.search(r"- Source-to-Sink 传播链:\s*(.+)", block)
        if chain_match and "->" not in chain_match.group(1):
            errors.append(f"{title} 传播链未使用 source -> sink 形式")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 java-audit Markdown 报告")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    errors = validate(args.report)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print("[OK] java-audit 报告校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
