#!/usr/bin/env python3
"""初始化 Java 审计工作目录。"""

from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime
from pathlib import Path


DIRS = ["tools", "decompiled", "reports", "tmp", "logs", "evidence"]


def create_workspace(base: Path, name: str, reuse: bool) -> tuple[Path, bool]:
    base.mkdir(parents=True, exist_ok=True)

    if reuse:
        workspace = base / name
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace, False

    candidate_name = name
    for _ in range(100):
        workspace = base / candidate_name
        try:
            workspace.mkdir(parents=True, exist_ok=False)
            return workspace, candidate_name != name
        except FileExistsError:
            candidate_name = f"{secrets.token_hex(3)}-{name}"

    raise RuntimeError(f"无法创建唯一工作目录: {base / name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="创建标准 Java 审计工作目录")
    parser.add_argument("--base", type=Path, default=Path.cwd(), help="工作目录创建位置")
    parser.add_argument("--name", default="java-audit-workspace", help="工作目录名称")
    parser.add_argument("--reuse", action="store_true", help="若目录已存在则复用，不自动创建随机前缀目录")
    args = parser.parse_args()

    base = args.base.resolve()
    workspace, renamed = create_workspace(base, args.name, args.reuse)

    created = []
    for dirname in DIRS:
        path = workspace / dirname
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))

    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "workspace": str(workspace),
        "requested_name": args.name,
        "actual_name": workspace.name,
        "renamed_due_to_conflict": renamed,
        "conflict_strategy": "random-prefix-before-requested-name" if renamed else "none",
        "directories": {dirname: str(workspace / dirname) for dirname in DIRS},
    }
    manifest_path = workspace / "workspace_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"workspace": str(workspace), "created": created, "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
