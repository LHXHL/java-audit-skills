#!/usr/bin/env python3
"""校验 java-audit Markdown 报告的边界。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


VULN_SECTIONS = [
    "## 1. 审计概述",
    "## 2. 确认漏洞",
    "## 3. 高风险线索 / 下一步人工验证",
    "## 4. 覆盖范围与限制",
]

ROUTE_SECTIONS = [
    "## 1. 梳理概述",
    "## 2. 路由汇总",
    "## 3. 路由详情",
    "## 4. 覆盖范围与限制",
]

AUTH_SECTIONS = [
    "## 1. 梳理概述",
    "## 2. 鉴权机制",
    "## 3. 路由/入口鉴权映射",
    "## 4. 风险观察与待确认项",
    "## 5. 覆盖范围与限制",
]

VULN_FIELDS = [
    "- 严重等级:",
    "- 受影响入口:",
    "- 是否需要鉴权:",
    "- 鉴权方式:",
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


def detect_report_type(text: str) -> str:
    names = section_names(text)
    if names == VULN_SECTIONS:
        return "vuln"
    if names == ROUTE_SECTIONS:
        return "route"
    if names == AUTH_SECTIONS:
        return "auth"
    return "unknown"


def validate_vuln(text: str) -> list[str]:
    errors: list[str] = []

    if section_names(text) != VULN_SECTIONS:
        errors.append(f"章节不匹配: {section_names(text)!r}")
    if "| 鉴权起手结论 |" not in section_body(text, "## 1. 审计概述"):
        errors.append("审计概述缺少鉴权起手结论")

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
        for field in VULN_FIELDS:
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


def validate_route(text: str) -> list[str]:
    errors: list[str] = []
    if section_names(text) != ROUTE_SECTIONS:
        errors.append(f"章节不匹配: {section_names(text)!r}")
    summary = section_body(text, "## 2. 路由汇总")
    details = section_body(text, "## 3. 路由详情")
    for header in ["| 类型 | 数量 | 说明 |", "| 编号 | HTTP 方法 | 路径/入口 | Handler | 参数 | 鉴权线索 | 证据位置 | 备注 |"]:
        if header not in text:
            errors.append(f"缺少表格: {header}")
    if "ROUTE-" not in details and "未发现路由" not in details:
        errors.append("路由详情既没有 ROUTE 编号，也没有写明未发现路由")
    if re.search(r"(大约|约|若干|~\s*\d+)", summary):
        errors.append("路由统计包含不精确数量")
    return errors


def validate_auth(text: str) -> list[str]:
    errors: list[str] = []
    if section_names(text) != AUTH_SECTIONS:
        errors.append(f"章节不匹配: {section_names(text)!r}")
    for header in [
        "| 编号 | 类型 | 实现位置 | 关键规则 | 证据位置 | 备注 |",
        "| 编号 | 路由/入口 | HTTP 方法 | Handler | 鉴权状态 | 权限要求 | 证据位置 | 备注 |",
        "| 编号 | 观察 | 当前证据 | 缺失证据 | 下一步 |",
    ]:
        if header not in text:
            errors.append(f"缺少表格: {header}")
    mapping = section_body(text, "## 3. 路由/入口鉴权映射")
    if "MAP-" not in mapping and "未发现" not in mapping:
        errors.append("鉴权映射既没有 MAP 编号，也没有写明未发现映射")
    if "未授权漏洞" in text or "确认漏洞" in text:
        errors.append("鉴权梳理报告不得直接写确认漏洞结论")
    return errors


def validate(path: Path, report_type: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if "【" in text or "】" in text:
        errors.append("报告仍包含模板占位符")

    resolved_type = detect_report_type(text) if report_type == "auto" else report_type
    if resolved_type == "vuln":
        errors.extend(validate_vuln(text))
    elif resolved_type == "route":
        errors.extend(validate_route(text))
    elif resolved_type == "auth":
        errors.extend(validate_auth(text))
    else:
        errors.append(f"无法识别报告类型，章节为: {section_names(text)!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 java-audit Markdown 报告")
    parser.add_argument("report", type=Path)
    parser.add_argument("--type", choices=["auto", "vuln", "route", "auth"], default="auto", help="报告类型")
    args = parser.parse_args()

    errors = validate(args.report, args.type)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print("[OK] java-audit 报告校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
