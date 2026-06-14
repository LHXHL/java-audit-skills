#!/usr/bin/env python3
"""初始化 Java 审计工作目录。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


DIRS = ["tools", "decompiled", "reports", "tmp", "logs", "evidence"]


def unique_workspace(base: Path, name: str) -> Path:
    candidate = base / name
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        candidate = base / f"{name}-{index}"
        if not candidate.exists():
            return candidate
        index += 1


def main() -> int:
    parser = argparse.ArgumentParser(description="创建标准 Java 审计工作目录")
    parser.add_argument("--base", type=Path, default=Path.cwd(), help="工作目录创建位置")
    parser.add_argument("--name", default="java-audit-workspace", help="工作目录名称")
    parser.add_argument("--reuse", action="store_true", help="若目录已存在则复用，不自动追加序号")
    args = parser.parse_args()

    base = args.base.resolve()
    workspace = base / args.name if args.reuse else unique_workspace(base, args.name)
    workspace.mkdir(parents=True, exist_ok=True)

    created = []
    for dirname in DIRS:
        path = workspace / dirname
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "directories": {dirname: str(workspace / dirname) for dirname in DIRS},
    }
    manifest_path = workspace / "workspace_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"workspace": str(workspace), "created": created, "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
