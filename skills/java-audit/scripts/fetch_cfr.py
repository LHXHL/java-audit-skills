#!/usr/bin/env python3
"""下载 CFR 到审计工作目录。"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime
from pathlib import Path


DEFAULT_URL = "https://xget.xi-xu.me/gh/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar"
DEFAULT_FILENAME = "cfr-0.152.jar"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="下载 CFR 反编译器到 workspace/tools")
    parser.add_argument("--workspace", type=Path, default=Path("java-audit-workspace"), help="审计工作目录")
    parser.add_argument("--url", default=DEFAULT_URL, help="CFR 下载地址")
    parser.add_argument("--filename", default=DEFAULT_FILENAME, help="保存文件名")
    parser.add_argument("--force", action="store_true", help="即使文件已存在也重新下载")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    tools_dir = workspace / "tools"
    logs_dir = workspace / "logs"
    tools_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    target = tools_dir / args.filename
    log_path = logs_dir / "fetch_cfr.log"
    if target.exists() and not args.force:
        result = {"status": "exists", "path": str(target), "sha256": sha256(target)}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    tmp = target.with_suffix(target.suffix + ".part")
    started = datetime.now().isoformat(timespec="seconds")
    try:
        request = urllib.request.Request(
            args.url,
            headers={"User-Agent": "Mozilla/5.0 java-audit-skill/1.0"},
        )
        with urllib.request.urlopen(request) as response, tmp.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        tmp.replace(target)
        result = {"status": "downloaded", "path": str(target), "sha256": sha256(target)}
        log_path.write_text(
            json.dumps({"started_at": started, "url": args.url, **result}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001
        if tmp.exists():
            tmp.unlink()
        log_path.write_text(
            json.dumps({"started_at": started, "url": args.url, "status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "failed", "error": str(exc), "log": str(log_path)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
