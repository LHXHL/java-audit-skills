#!/usr/bin/env python3
"""通过 CFR CLI 反编译 Java 编译产物。"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path


def safe_name(path: Path) -> str:
    stem = path.name
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", stem)


def main() -> int:
    parser = argparse.ArgumentParser(description="调用 CFR 反编译 JAR/WAR/class")
    parser.add_argument("target", type=Path, help="待反编译的 JAR/WAR/class 文件")
    parser.add_argument("--workspace", type=Path, default=Path("java-audit-workspace"), help="审计工作目录")
    parser.add_argument("--cfr", type=Path, help="CFR jar 路径，默认使用 workspace/tools/cfr-0.152.jar")
    parser.add_argument("--output-dir", type=Path, help="输出目录，默认 workspace/decompiled/<目标名>")
    parser.add_argument("--analyseas", choices=["DETECT", "JAR", "WAR", "CLASS"], default="DETECT", help="强制解析类型")
    parser.add_argument("--jarfilter", help="仅反编译 FQN 匹配该正则的类")
    parser.add_argument("--extra-classpath", help="传给 CFR 的额外 classpath")
    parser.add_argument("--java", default="java", help="Java 可执行文件")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    target = args.target.resolve()
    cfr = args.cfr.resolve() if args.cfr else workspace / "tools" / "cfr-0.152.jar"
    output_dir = args.output_dir.resolve() if args.output_dir else workspace / "decompiled" / safe_name(target)
    logs_dir = workspace / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        print(json.dumps({"status": "failed", "error": f"目标文件不存在: {target}"}, ensure_ascii=False))
        return 2
    if not cfr.exists():
        print(json.dumps({"status": "failed", "error": f"CFR 不存在，请先运行 fetch_cfr.py: {cfr}"}, ensure_ascii=False))
        return 2

    cmd = [args.java, "-jar", str(cfr), str(target), "--outputdir", str(output_dir)]
    if args.analyseas != "DETECT":
        cmd.extend(["--analyseas", args.analyseas])
    if args.jarfilter:
        cmd.extend(["--jarfilter", args.jarfilter])
    if args.extra_classpath:
        cmd.extend(["--extraclasspath", args.extra_classpath])

    started = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"decompile_{safe_name(target)}_{started}.log"
    proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    log_path.write_text(
        "\n".join(
            [
                f"started_at: {started}",
                "command: " + " ".join(shlex.quote(part) for part in cmd),
                f"returncode: {proc.returncode}",
                "",
                "[stdout]",
                proc.stdout,
                "",
                "[stderr]",
                proc.stderr,
            ]
        ),
        encoding="utf-8",
    )

    result = {
        "status": "ok" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "target": str(target),
        "output_dir": str(output_dir),
        "log": str(log_path),
    }
    print(json.dumps(result, ensure_ascii=False))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
