#!/usr/bin/env python3
"""Lightweight boundary checks for java-file-read-audit output."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP = r"\d{8}_\d{6}"
SECTIONS = [
    "## 1. 审计概述",
    "## 2. 结论统计",
    "## 3. 文件读取操作映射",
    "## 4. 候选风险与非漏洞依据",
    "## 5. 风险详情",
    "## 6. 审计结论",
]
FORBIDDEN = [
    "输出自检",
    "报告质量自检",
    "技能源",
    "CVSS",
    "CVE-",
    "修复版本",
    "Claude",
    "测试提示词",
    "模型验收",
    "hard rule",
    "PoC",
    "沙箱",
    "审批",
    "approval",
    "执行环境无法",
    "无法调用",
    "命令失败",
    "网络受限",
    "权限受限",
    "当前环境",
    "工具不可用",
    "反编译不可用",
    "无法启动目标服务",
    "javap",
    "cfr",
    "procyon",
    "jadx",
    "python",
]
SENSITIVE_PAYLOAD_TERMS = [
    "/etc/passwd",
    "/etc/shadow",
    "WEB-INF/web.xml",
    "System32",
    "drivers\\etc\\hosts",
    "drivers/etc/hosts",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_report(out_dir: Path) -> Path | None:
    pattern = re.compile(rf"^.+_file_read_audit_{TIMESTAMP}\.md$")
    matches = sorted(path for path in out_dir.glob("*_file_read_audit_*.md") if pattern.match(path.name))
    return matches[0] if len(matches) == 1 else None


def section_names(text: str) -> list[str]:
    return re.findall(r"^##\s+\d+\.\s+.+$", text, flags=re.MULTILINE)


def section_text(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    next_match = re.search(r"(?m)^##\s+\d+\.\s+", text[start + len(heading) :])
    if not next_match:
        return text[start:]
    return text[start : start + len(heading) + next_match.start()]


def validation_material_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    for heading in ["#### Burp Suite 请求", "#### Payload"]:
        start = 0
        while True:
            idx = text.find(heading, start)
            if idx < 0:
                break
            next_heading = re.search(r"(?m)^#{3,4}\s+", text[idx + len(heading) :])
            end = len(text) if not next_heading else idx + len(heading) + next_heading.start()
            blocks.append(text[idx:end])
            start = end
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    errors: list[str] = []

    report = find_report(args.output_dir)
    unexpected = sorted(
        path.name
        for path in args.output_dir.iterdir()
        if path.is_file() and (path.suffix in {".py", ".tmp", ".log"} or path.name.startswith("_"))
    )
    if unexpected:
        errors.append(f"unexpected generated helper files: {unexpected}")
    if report is None:
        errors.append("expected exactly one timestamped file-read audit report")
    else:
        if "_000000.md" in report.name or "_19700101_" in report.name:
            errors.append("filename uses placeholder timestamp")
        text = read(report)
        folded = text.casefold()
        if "生成时间:" not in text:
            errors.append("missing generation time")
        if "使用 skill: java-file-read-audit" not in text:
            errors.append("missing skill marker")
        if "生成时间:" in text and ("00:00:00" in text or "1970-01-01" in text):
            errors.append("report uses placeholder generation time")
        if section_names(text) != SECTIONS:
            errors.append(f"sections mismatch: {section_names(text)!r}")
        for term in FORBIDDEN:
            if term.casefold() in folded:
                errors.append(f"forbidden term found: {term}")
        if "【填写】" in text or "TODO" in text:
            errors.append("placeholder remains")
        risk_section = section_text(text, "## 5. 风险详情")
        mapping_section = section_text(text, "## 3. 文件读取操作映射")
        for line in mapping_section.splitlines():
            if line.startswith("|") and "ServletOutputStream" in line:
                if not re.search(
                    r"FileInputStream|FileReader|Files\.|InputStream|Resource|getResourceAsStream|getRealPath|BufferedReader",
                    line,
                ):
                    errors.append("mapping contains output stream without file/resource input source")
        if re.search(r"(候选状态|结论状态)\s*[:：|].*(待验证|不可确认|非漏洞)", risk_section):
            errors.append("section 5 contains non-final risk detail")
        for block in validation_material_blocks(text):
            if "【" in block or "】" in block:
                errors.append("validation material uses non-placeholder brackets")
            for term in SENSITIVE_PAYLOAD_TERMS:
                if term.casefold() in block.casefold():
                    errors.append(f"sensitive path appears in validation material: {term}")

        blocks = re.split(r"(?m)^###\s+", text)
        for block in blocks[1:]:
            title = block.splitlines()[0] if block.splitlines() else "<empty>"
            status_match = re.search(r"(候选状态|结论状态)\s*[:：|]\s*\*{0,2}(确认漏洞|条件成立|待验证|不可确认|非漏洞)", block)
            final_status = bool(status_match and status_match.group(2) in {"确认漏洞", "条件成立"})
            non_final_status = re.search(r"(\|\s*结论状态\s*\|\s*(待验证|不可确认|非漏洞)\s*\|)", block)
            has_request = "#### Burp Suite 请求" in block or "#### Payload" in block or "```http" in block
            if has_request and not final_status:
                errors.append(f"{title}: request/payload without final status")
            if has_request and non_final_status:
                errors.append(f"{title}: request/payload appears in non-final block")
            if final_status:
                for heading in [
                    "#### 受影响入口",
                    "#### 关键代码",
                    "#### 数据流",
                    "#### 防护与执行条件分析",
                    "#### Burp Suite 请求",
                    "#### Payload",
                    "#### 授权验证说明",
                ]:
                    if heading not in block:
                        errors.append(f"{title}: missing {heading}")
                if "```http" not in block:
                    errors.append(f"{title}: missing importable HTTP request")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print("[OK] java-file-read-audit output boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
