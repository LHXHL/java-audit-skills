#!/usr/bin/env python3
"""运行 Java Web 审计 Query Pack，生成内部 search-hits 证据。"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QueryGroup:
    slug: str
    title: str
    primary_family: str
    mapped_families: tuple[str, ...]
    priority: str
    patterns: tuple[str, ...]


SKIP_DIR_NAMES = {"tools", "logs", "reports", "evidence"}
GENERATED_BY = "run_discovery_queries.py"
DEFAULT_QUERY_PACK = Path(__file__).resolve().parents[1] / "references" / "discovery-query-pack.yaml"
DEFAULT_QUERY_PACK_VERSION = "3"
MANIFEST_FILE = "manifest.json"


def parse_yaml_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped in {"true", "True"}:
        return True
    if stripped in {"false", "False"}:
        return False
    if not stripped:
        return ""
    if stripped[0] in {"'", '"', "["}:
        try:
            return ast.literal_eval(stripped)
        except (SyntaxError, ValueError):
            return stripped.strip("'\"")
    return stripped


def fallback_yaml_load(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    groups: list[dict[str, Any]] = []
    current_group: dict[str, Any] | None = None
    in_patterns = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        top_match = re.match(r"^([a-zA-Z_]+):\s*(.*)$", line)
        if top_match:
            key, value = top_match.groups()
            if key == "groups":
                continue
            data[key] = parse_yaml_scalar(value)
            continue

        group_match = re.match(r"^\s{2}-\s+slug:\s*(.+)$", line)
        if group_match:
            if current_group is not None:
                groups.append(current_group)
            current_group = {"slug": parse_yaml_scalar(group_match.group(1)), "patterns": []}
            in_patterns = False
            continue

        field_match = re.match(r"^\s{4}([a-zA-Z_]+):\s*(.*)$", line)
        if field_match and current_group is not None:
            key, value = field_match.groups()
            if key == "patterns":
                current_group.setdefault("patterns", [])
                in_patterns = True
            else:
                current_group[key] = parse_yaml_scalar(value)
                in_patterns = False
            continue

        pattern_match = re.match(r"^\s{6}-\s+(.+)$", line)
        if pattern_match and current_group is not None and in_patterns:
            current_group.setdefault("patterns", []).append(str(parse_yaml_scalar(pattern_match.group(1))))

    if current_group is not None:
        groups.append(current_group)
    data["groups"] = groups
    return data


def load_query_pack(path: Path) -> tuple[tuple[QueryGroup, ...], str, str]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
        loader = "pyyaml"
    except Exception:
        data = fallback_yaml_load(text)
        loader = "fallback"

    if not isinstance(data, dict):
        raise RuntimeError(f"Query Pack YAML 格式非法: {path}")

    raw_groups = data.get("groups")
    if not isinstance(raw_groups, list):
        raise RuntimeError(f"Query Pack YAML 缺少 groups: {path}")

    groups: list[QueryGroup] = []
    for index, entry in enumerate(raw_groups, start=1):
        if not isinstance(entry, dict):
            raise RuntimeError(f"Query Pack 第 {index} 个 group 不是对象")

        mapped_families = entry.get("mapped_families", [])
        if isinstance(mapped_families, str):
            mapped_families = [item.strip() for item in mapped_families.split("、") if item.strip()]
        patterns = entry.get("patterns", [])
        if isinstance(patterns, str):
            patterns = [patterns]

        groups.append(QueryGroup(
            slug=str(entry.get("slug", "") or "").strip(),
            title=str(entry.get("title", "") or "").strip(),
            primary_family=str(entry.get("primary_family", "") or "").strip(),
            mapped_families=tuple(str(item).strip() for item in mapped_families if str(item).strip()),
            priority=str(entry.get("priority", "") or "").strip(),
            patterns=tuple(str(item) for item in patterns if str(item)),
        ))

    errors = validate_query_groups(tuple(groups))
    if errors:
        joined = "\n- ".join(errors)
        raise RuntimeError(f"Query Pack YAML 校验失败: {path}\n- {joined}")

    version = str(data.get("version", "") or DEFAULT_QUERY_PACK_VERSION)
    return tuple(groups), version, loader


def validate_query_groups(groups: tuple[QueryGroup, ...]) -> list[str]:
    errors: list[str] = []
    seen_slugs: set[str] = set()
    for index, group in enumerate(groups, start=1):
        label = group.slug or f"第 {index} 组"
        if not group.slug:
            errors.append(f"{label} 缺少 slug")
        if group.slug in seen_slugs:
            errors.append(f"查询组 slug 重复: {group.slug}")
        seen_slugs.add(group.slug)

        if not group.title:
            errors.append(f"{label} 缺少 title")
        if not group.primary_family:
            errors.append(f"{label} 缺少 primary_family")
        if not group.priority:
            errors.append(f"{label} 缺少 priority")
        if not group.patterns:
            errors.append(f"{label} 缺少 patterns")

        for pattern_index, pattern in enumerate(group.patterns, start=1):
            try:
                re.compile(pattern, flags=re.IGNORECASE)
            except re.error as exc:
                errors.append(f"{label} 第 {pattern_index} 条正则无法编译: {exc}")
    return errors

def markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def candidate_sources(workspace: Path, explicit_sources: list[Path]) -> list[Path]:
    sources = [path.resolve() for path in explicit_sources if path.exists()]
    if sources:
        return sources

    defaults = [
        workspace / "decompiled",
        workspace / "src",
        workspace / "source",
        workspace / "sources",
        workspace / "classes",
        workspace / "unpacked",
        workspace / "exploded",
        workspace / "bytecode",
    ]
    return [path.resolve() for path in defaults if path.exists()]


def iter_source_files(sources: list[Path]):
    for source in sources:
        if source.is_file():
            yield source
            continue
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.relative_to(source).parts[:-1]):
                continue
            yield path


def run_python_regex(pattern: str, sources: list[Path], max_hits: int) -> list[tuple[str, str, str]]:
    try:
        regex = re.compile(pattern, flags=re.IGNORECASE)
    except re.error as exc:
        raise RuntimeError(f"Python regex 编译失败: {pattern}: {exc}") from exc

    hits: list[tuple[str, str, str]] = []
    for path in iter_source_files(sources):
        if len(hits) >= max_hits:
            break
        try:
            text = path.read_bytes().decode("latin-1", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                hits.append((str(path), str(line_no), line.strip()))
                if len(hits) >= max_hits:
                    break
    return hits


def run_rg(rg_bin: str, pattern: str, sources: list[Path], max_hits: int) -> list[tuple[str, str, str]]:
    command = [
        rg_bin,
        "-n",
        "-a",
        "-i",
        "--no-heading",
        "--color",
        "never",
        "-g",
        "!tools/**",
        "-g",
        "!logs/**",
        "-g",
        "!reports/**",
        "-g",
        "!evidence/**",
        "--",
        pattern,
        *[str(source) for source in sources],
    ]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode not in {0, 1}:
        raise RuntimeError(proc.stderr.strip() or f"rg 执行失败: {pattern}")

    hits: list[tuple[str, str, str]] = []
    for line in proc.stdout.splitlines():
        if len(hits) >= max_hits:
            break
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        hits.append((parts[0], parts[1], parts[2]))
    return hits


def resolve_engine(requested: str) -> tuple[str, str | None]:
    if requested == "python":
        return "python", None

    rg_bin = shutil.which("rg")
    if requested == "rg":
        if not rg_bin:
            raise RuntimeError("未找到 rg；请改用 --engine python，或安装 ripgrep")
        return "rg", rg_bin

    if requested == "auto":
        if rg_bin:
            return "rg", rg_bin
        return "python", None

    raise RuntimeError(f"未知检索引擎: {requested}")


def run_query(engine: str, engine_bin: str | None, pattern: str, sources: list[Path], max_hits: int) -> list[tuple[str, str, str]]:
    if engine == "rg":
        if not engine_bin:
            raise RuntimeError("rg 引擎缺少可执行路径")
        return run_rg(engine_bin, pattern, sources, max_hits)
    return run_python_regex(pattern, sources, max_hits)


def select_query_groups(selected: list[str], available_groups: tuple[QueryGroup, ...]) -> tuple[QueryGroup, ...]:
    if not selected:
        return available_groups

    selected_set = set(selected)
    groups = tuple(group for group in available_groups if group.slug in selected_set)
    missing = sorted(selected_set - {group.slug for group in groups})
    if missing:
        valid = ", ".join(group.slug for group in available_groups)
        raise ValueError(f"未知查询组: {', '.join(missing)}；可用查询组: {valid}")
    return groups


def write_group_hits(
    output_dir: Path,
    group: QueryGroup,
    rows: list[dict[str, str]],
    engine: str,
    query_pack_version: str,
    queries_path: Path,
) -> None:
    path = output_dir / f"{group.slug}.md"
    lines = [
        f"# {group.title} Query Hits",
        "",
        f"生成工具: {GENERATED_BY}",
        f"Query Pack 版本: {query_pack_version}",
        f"Query Pack 文件: {queries_path}",
        f"查询组: {group.slug}",
        f"检索引擎: {engine}",
        "",
        "| 编号 | 漏洞族 | 优先级 | 命中模式 | 文件 | 行号 | 上下文 | 可映射漏洞族 | 处理状态 | 候选 ID | 处理说明 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {family} | {priority} | {pattern} | {file} | {line} | {context} | {mapped} | 未处理 |  |  |".format(
                id=row["id"],
                family=markdown_cell(row["family"]),
                priority=markdown_cell(row["priority"]),
                pattern=markdown_cell(row["pattern"]),
                file=markdown_cell(row["file"]),
                line=markdown_cell(row["line"]),
                context=markdown_cell(row["context"]),
                mapped=markdown_cell(row["mapped"]),
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index(
    output_dir: Path,
    workspace: Path,
    sources: list[Path],
    summaries: list[tuple[QueryGroup, int]],
    engine: str,
    generated_at: str,
    query_pack_version: str,
    queries_path: Path,
    yaml_loader: str,
) -> None:
    lines = [
        "# Query Pack 检索索引",
        "",
        f"生成工具: {GENERATED_BY}",
        f"Query Pack 版本: {query_pack_version}",
        f"Query Pack 文件: {queries_path}",
        f"YAML 加载器: {yaml_loader}",
        f"生成时间: {generated_at}",
        f"审计工作目录: {workspace}",
        f"检索引擎: {engine}",
        f"Manifest: {MANIFEST_FILE}",
        "",
        "## 检索范围",
        "",
    ]
    for source in sources:
        lines.append(f"- {source}")
    lines.extend([
        "",
        "## 汇总",
        "",
        "| 查询组 | 文件 | 命中数 | 未处理 | 说明 |",
        "|---|---|---:|---:|---|",
    ])
    for group, count in summaries:
        hit_file = f"{group.slug}.md" if count else "无"
        lines.append(f"| {markdown_cell(group.title)} | {hit_file} | {count} | {count} | 命中需归类，不能直接作为漏洞 |")
    output_dir.joinpath("index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(
    output_dir: Path,
    workspace: Path,
    sources: list[Path],
    summaries: list[tuple[QueryGroup, int]],
    engine: str,
    generated_at: str,
    query_pack_version: str,
    queries_path: Path,
    yaml_loader: str,
) -> None:
    manifest = {
        "generated_by": GENERATED_BY,
        "query_pack_version": query_pack_version,
        "queries_file": str(queries_path),
        "yaml_loader": yaml_loader,
        "generated_at": generated_at,
        "workspace": str(workspace),
        "engine": engine,
        "sources": [str(source) for source in sources],
        "groups": [
            {
                "slug": group.slug,
                "title": group.title,
                "file": f"{group.slug}.md" if count else "",
                "hit_count": count,
            }
            for group, count in summaries
        ],
        "total_hits": sum(count for _, count in summaries),
    }
    output_dir.joinpath(MANIFEST_FILE).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def reset_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for markdown_file in output_dir.glob("*.md"):
        markdown_file.unlink()
    manifest_path = output_dir / MANIFEST_FILE
    if manifest_path.exists():
        manifest_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 Java Web 审计 Query Pack")
    parser.add_argument("--workspace", type=Path, help="审计工作目录")
    parser.add_argument("--queries", type=Path, default=DEFAULT_QUERY_PACK, help="Query Pack YAML 文件")
    parser.add_argument("--source", type=Path, action="append", default=[], help="额外检索源码或反编译目录，可重复")
    parser.add_argument("--group", action="append", default=[], help="只运行指定查询组 slug，可重复")
    parser.add_argument("--list-groups", action="store_true", help="列出查询组后退出")
    parser.add_argument("--validate-queries", action="store_true", help="只校验 Query Pack YAML 后退出")
    parser.add_argument("--engine", choices=["python", "auto", "rg"], default="python", help="检索引擎；默认 python 不依赖外部命令")
    parser.add_argument("--max-hits-per-query", type=int, default=200, help="单个查询模式最多记录命中数")
    args = parser.parse_args()

    queries_path = args.queries.resolve()
    try:
        available_groups, query_pack_version, yaml_loader = load_query_pack(queries_path)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    if args.validate_queries:
        print(f"[OK] Query Pack YAML 校验通过，groups={len(available_groups)}，version={query_pack_version}，loader={yaml_loader}")
        return 0

    if args.list_groups:
        for group in available_groups:
            print(f"{group.slug}\t{group.title}\t{group.priority}")
        return 0

    if not args.workspace:
        print("[FAIL] 必须提供 --workspace，或使用 --validate-queries / --list-groups", file=sys.stderr)
        return 1

    try:
        query_groups = select_query_groups(args.group, available_groups)
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    try:
        engine, engine_bin = resolve_engine(args.engine)
    except RuntimeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    workspace = args.workspace.resolve()
    sources = candidate_sources(workspace, args.source)
    if not sources:
        print("[FAIL] 未找到可检索源码或反编译目录，请使用 --source 指定目标", file=sys.stderr)
        return 1

    output_dir = workspace / "evidence" / "search-hits"
    reset_output_dir(output_dir)

    summaries: list[tuple[QueryGroup, int]] = []
    total_hits = 0
    generated_at = datetime.now().isoformat(timespec="seconds")
    for group in query_groups:
        rows: list[dict[str, str]] = []
        seen: set[tuple[str, str, str, str]] = set()
        for pattern in group.patterns:
            hits = run_query(engine, engine_bin, pattern, sources, args.max_hits_per_query)
            for file_path, line_no, context in hits:
                key = (file_path, line_no, context, pattern)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "id": f"HIT-{group.slug.upper().replace('-', '_')}-{len(rows) + 1:03d}",
                    "family": group.primary_family,
                    "priority": group.priority,
                    "pattern": pattern,
                    "file": file_path,
                    "line": line_no,
                    "context": context[:240],
                    "mapped": "、".join(group.mapped_families),
                })
        if rows:
            write_group_hits(output_dir, group, rows, engine, query_pack_version, queries_path)
        summaries.append((group, len(rows)))
        total_hits += len(rows)

    write_index(output_dir, workspace, sources, summaries, engine, generated_at, query_pack_version, queries_path, yaml_loader)
    write_manifest(output_dir, workspace, sources, summaries, engine, generated_at, query_pack_version, queries_path, yaml_loader)
    print(f"[OK] Query Pack 完成，engine={engine}，groups={len(query_groups)}，命中 {total_hits} 条，输出目录: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
