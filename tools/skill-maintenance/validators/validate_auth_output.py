#!/usr/bin/env python3
"""Lightweight boundary checks for java-auth-audit output."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TIMESTAMP = r"\d{8}_\d{6}"
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
]
UNCERTAINTY_PATTERNS = [
    r"(鉴权|认证|授权|拦截|Interceptor|Filter|HandlerInterceptor|Servlet|Controller|父类|基类|AOP|网关|运行时路由)[^。；\n]{0,60}(需反编译|未反编译|待补证|内部实现未知|后续拦截未知|行为未知|无法确认|待验证|候选|未知|未确认|待确认)",
    r"(需反编译|未反编译|待补证|内部实现未知|后续拦截未知|行为未知|无法确认|待验证|候选|未知|未确认|待确认)[^。；\n]{0,60}(Interceptor|Filter|HandlerInterceptor|Servlet|Controller|父类|基类|AOP|网关|运行时路由)",
    r"(若|如果)[^。；\n]*?(父类|基类|Interceptor|Filter|Servlet|AOP)",
    r"\.class[^。；\n]*?(未知|未确认|待确认|无法确认)",
]
MIXED_MECHANISM_PATTERNS = [
    r"REST[^#]{0,120}(SOAP|WebService|文件上传|上传|长轮询|独立\s*Servlet)",
    r"SOAP[^#]{0,120}(REST|文件上传|上传|长轮询|独立\s*Servlet)",
    r"(文件上传|上传)[^#]{0,120}(REST|SOAP|WebService|长轮询)",
    r"长轮询[^#]{0,120}(REST|SOAP|WebService|文件上传|上传)",
]
CLIENT_CREDENTIAL_PATTERNS = [
    r"记住密码",
    r"明文\s*Cookie",
    r"明文密码",
    r"password[^。\n]{0,40}cookie",
    r"cookie[^。\n]{0,40}password",
    r"自动填充密码",
]

MAIN_SECTIONS = [
    "## 1. 鉴权框架识别",
    "## 2. 鉴权架构概览",
    "## 3. 结论统计",
    "## 4. 风险详情",
    "## 5. 相关文档",
]
MAPPING_SECTIONS = [
    "## 1. 鉴权状态说明",
    "## 2. 路由鉴权映射",
    "## 3. 风险统计汇总",
    "## 4. 相关文档",
]
README_SECTIONS = [
    "## 1. 审计概述",
    "## 2. 审计方法",
    "## 3. 审计局限性",
    "## 4. 待验证与复核建议",
    "## 5. 下一步建议",
    "## 6. 相关文档",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_matching(out_dir: Path, suffix: str, errors: list[str]) -> Path | None:
    pattern = re.compile(rf"^.+_{suffix}_{TIMESTAMP}\.md$")
    matches = sorted(path for path in out_dir.glob(f"*_{suffix}_*.md") if pattern.match(path.name))
    if len(matches) > 1:
        errors.append(f"{suffix}: expected one timestamped file, got {len(matches)}")
    return matches[0] if matches else None


def section_names(text: str) -> list[str]:
    return re.findall(r"^##\s+\d+\.\s+.+$", text, flags=re.MULTILINE)


def check_exact_sections(label: str, text: str, expected: list[str], errors: list[str]) -> None:
    got = section_names(text)
    if got != expected:
        errors.append(f"{label}: sections mismatch, got {got!r}")


def check_forbidden(label: str, text: str, errors: list[str]) -> None:
    for term in FORBIDDEN:
        if term in text:
            errors.append(f"{label}: forbidden term found: {term}")
    if "【填写】" in text or "TODO" in text:
        errors.append(f"{label}: placeholder remains")


def check_main(main_text: str, errors: list[str]) -> None:
    blocks = re.split(r"(?m)^###\s+", main_text)
    for block in blocks[1:]:
        title = block.splitlines()[0] if block.splitlines() else "<empty>"
        has_request = "Burp Suite 请求" in block or "Payload / 变体" in block
        has_final_status = "确认漏洞" in block or "条件成立" in block
        non_final_status = re.search(
            r"(\|\s*状态\s*\|\s*(待验证|不可确认|非漏洞)\s*\|)|(^状态[:：]\s*(待验证|不可确认|非漏洞)\s*$)",
            block,
            flags=re.MULTILINE,
        )
        if has_request and not has_final_status:
            errors.append(f"main:{title}: Burp/payload without confirmed or conditional status")
        if has_request and non_final_status:
            errors.append(f"main:{title}: Burp/payload appears in non-final status block")
        if has_final_status:
            if any(re.search(pattern, block, flags=re.IGNORECASE) for pattern in UNCERTAINTY_PATTERNS):
                errors.append(f"main:{title}: final risk depends on unknown internal auth implementation")
            if any(re.search(pattern, block, flags=re.IGNORECASE | re.DOTALL) for pattern in MIXED_MECHANISM_PATTERNS):
                errors.append(f"main:{title}: final risk mixes unrelated mechanisms or evidence levels")
            if any(re.search(pattern, block, flags=re.IGNORECASE) for pattern in CLIENT_CREDENTIAL_PATTERNS):
                errors.append(f"main:{title}: client-side credential storage belongs in README unless it directly bypasses auth")
            if "无需 Burp 请求" in block or "```http" not in block:
                errors.append(f"main:{title}: final risk must include an importable HTTP request")
            for heading in [
                "#### 受影响入口",
                "#### 关键代码",
                "#### 数据流与拦截链",
                "#### Burp Suite 请求",
                "#### Payload / 变体",
                "#### 授权验证说明",
                "#### 修复建议",
            ]:
                if heading not in block:
                    errors.append(f"main:{title}: missing {heading}")


def check_no_requests(label: str, text: str, errors: list[str]) -> None:
    for term in ["Burp Suite 请求", "Payload / 变体", "```http"]:
        if term in text:
            errors.append(f"{label}: request/payload material is not allowed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    out_dir = args.output_dir
    errors: list[str] = []

    if not out_dir.is_dir():
        print(f"not a directory: {out_dir}", file=sys.stderr)
        return 2

    main_file = find_matching(out_dir, "auth_audit", errors)
    mapping_file = find_matching(out_dir, "auth_mapping", errors)
    readme_file = find_matching(out_dir, "auth_README", errors)

    for label, path in [("main", main_file), ("mapping", mapping_file), ("readme", readme_file)]:
        if path is None:
            errors.append(f"{label}: expected timestamped file is missing")

    if main_file:
        text = read(main_file)
        check_exact_sections("main", text, MAIN_SECTIONS, errors)
        check_forbidden("main", text, errors)
        check_main(text, errors)

    if mapping_file:
        text = read(mapping_file)
        check_exact_sections("mapping", text, MAPPING_SECTIONS, errors)
        check_forbidden("mapping", text, errors)
        check_no_requests("mapping", text, errors)
        if "条件成立" in text:
            errors.append("mapping: 条件成立 is not a route auth status")

    if readme_file:
        text = read(readme_file)
        check_exact_sections("readme", text, README_SECTIONS, errors)
        check_forbidden("readme", text, errors)
        check_no_requests("readme", text, errors)
        if re.search(r"^###\s+", text, flags=re.MULTILINE):
            errors.append("readme: third-level headings are not allowed")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}", file=sys.stderr)
        return 1

    print("[OK] java-auth-audit output boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
