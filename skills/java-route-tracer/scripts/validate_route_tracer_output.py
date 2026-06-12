#!/usr/bin/env python3
"""Boundary checks for java-route-tracer reports."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FULL_SECTIONS = [
    "## 0. 上游上下文",
    "## 1. 追踪对象",
    "## 2. HTTP/SOAP 请求与参数",
    "## 3. 调用链证据",
    "## 4. Sink 识别",
    "## 5. 参数流向与可控性",
    "## 6. 分支条件与路径状态",
    "## 7. 下游交接结论",
]

SIMPLE_SECTIONS = [
    "## 0. 上游上下文",
    "## 1. 入口与请求",
    "## 2. 调用链与 Sink",
    "## 3. 可控性与分支",
    "## 4. 下游交接结论",
]

INDEX_SECTIONS = [
    "## 0. 上游上下文",
    "## 1. 方法清单",
    "## 2. 覆盖统计",
    "## 3. 未完成或限制",
    "## 4. 下游交接",
]

FORBIDDEN = [
    "## 输出自检",
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
    "验证通过",
    "可利用",
    "风险极低",
    "注入不成立",
    "漏洞不存在",
    "无风险",
    "用户名枚举",
    "账户状态枚举",
    "认证/授权缺失",
    "认证基线",
    "入站认证",
    "认证拦截器",
    "传输加密",
    "登录失败",
    "登录锁定",
    "限速",
    "密码存储",
    "密码等值",
    "IP 白名单",
    "Tomcat Valve",
    "Realm",
    "网关",
    "jaxws:inInterceptors",
    "注入面",
    "本方法之外",
    "同 DAO",
    "推断为",
    "安全风险",
    "关键发现",
    "明文密码",
    "无 WS-Security 保护",
    "WS-Security",
    "WSS4J",
    "安全过滤器",
    "PrivilegeFilter",
    "CsrfFilter",
    "XssFilter",
    "UPFWFilter",
    "反向代理",
    "网络层访问控制",
    "MD5",
    "哈希",
    "存储格式",
    "等价于",
    "getshell",
    "webshell",
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
    return path.read_text(encoding="utf-8")


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
    if re.search(r"(等价于|PreparedStatement[:：])\s*`?SELECT\b", text, flags=re.IGNORECASE):
        errors.append(f"{path}: inferred generated SQL found")
    if re.search(r"(~\s*\d+|约\s*\d+|大约\s*\d+|若干|多项)", text):
        errors.append(f"{path}: approximate count wording found")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    reports = sorted(
        path
        for path in args.output_dir.rglob("*.md")
        if path.name != "ACCEPTANCE.md"
    )
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
