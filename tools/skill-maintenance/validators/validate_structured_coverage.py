#!/usr/bin/env python3
"""Validate structured coverage outputs for Java audit skill regressions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


FORBIDDEN_VAGUE = ("等", "部分", "主要", "更多", "其他", "...")
REQUIRED_ROUTE_FIELDS = {
    "schema_version",
    "route_id",
    "mechanism_id",
    "entry_type",
    "path",
    "class",
    "method",
    "params",
    "evidence",
    "confidence",
    "status",
}
REQUIRED_DISPATCHER_FIELDS = {
    "schema_version",
    "dispatcher_id",
    "mechanism_id",
    "entry_route_id",
    "dispatch_type",
    "dispatch_keys",
    "target_rule",
    "evidence",
    "status",
}
REQUIRED_SINK_FIELDS = {
    "schema_version",
    "sink_id",
    "sink_types",
    "sink_api",
    "wrapper_chain",
    "class",
    "method",
    "evidence",
    "dispatch_to",
    "status",
}
REQUIRED_TRACE_FIELDS = {
    "schema_version",
    "trace_id",
    "route_id",
    "source_param",
    "sink_types",
    "sink_api",
    "call_chain",
    "guards",
    "class",
    "method",
    "evidence",
    "helper",
    "controllability",
    "dispatch_to",
    "status",
}
DISPATCH_REQUIREMENTS = {
    "SQL": {"java-sql-audit"},
    "XML": {"java-xxe-audit"},
    "DESERIALIZE": {"java-deserialization-audit"},
    "FILE": {"java-file-read-audit"},
    "FILE_READ": {"java-file-read-audit"},
    "UPLOAD": {"java-file-upload-audit"},
    "FILE_WRITE": {"java-file-upload-audit"},
}
FINAL_OPERATION_ENTRY_HINTS = ("SERVICE", "RPC", "SOAP", "CUSTOM", "DISPATCH")


def read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"{path}: missing file")
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
    return None


def read_jsonl(path: Path, errors: list[str], required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            errors.append(f"{path}: missing file")
        return []
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}:{lineno}: invalid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path}:{lineno}: row must be a JSON object")
            continue
        rows.append(value)
    return rows


def contains_vague(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in FORBIDDEN_VAGUE)
    if isinstance(value, list):
        return any(contains_vague(item) for item in value)
    return False


def as_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item) for item in value}
    if value is None:
        return set()
    return {str(value)}


def has_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def validate_mechanisms(structured: Path, errors: list[str]) -> dict[str, dict[str, Any]]:
    path = structured / "route_mechanisms.json"
    data = read_json(path, errors)
    if not isinstance(data, dict):
        return {}
    mechanisms = data.get("mechanisms")
    if not isinstance(mechanisms, list):
        errors.append(f"{path}: mechanisms must be a list")
        return {}

    by_id: dict[str, dict[str, Any]] = {}
    for index, mechanism in enumerate(mechanisms):
        if not isinstance(mechanism, dict):
            errors.append(f"{path}: mechanisms[{index}] must be an object")
            continue
        mechanism_id = mechanism.get("mechanism_id")
        if not mechanism_id:
            errors.append(f"{path}: mechanisms[{index}] missing mechanism_id")
            continue
        mechanism_id = str(mechanism_id)
        if mechanism_id in by_id:
            errors.append(f"{path}: duplicate mechanism_id {mechanism_id!r}")
        by_id[mechanism_id] = mechanism
        for key in ("type", "entry_root", "route_rule", "operation_rule", "evidence", "confidence"):
            if key not in mechanism:
                errors.append(f"{path}: mechanism {mechanism_id} missing {key}")
        if contains_vague(mechanism.get("operation_rule")):
            errors.append(f"{path}: mechanism {mechanism_id} has vague operation_rule")
    return by_id


def validate_routes(structured: Path, errors: list[str]) -> list[dict[str, Any]]:
    path = structured / "routes.jsonl"
    routes = read_jsonl(path, errors)
    seen: set[str] = set()
    for index, route in enumerate(routes, 1):
        missing = sorted(REQUIRED_ROUTE_FIELDS - route.keys())
        if missing:
            errors.append(f"{path}:{index}: missing fields: {', '.join(missing)}")
        route_id = str(route.get("route_id", ""))
        if not route_id:
            errors.append(f"{path}:{index}: route_id is empty")
        elif route_id in seen:
            errors.append(f"{path}:{index}: duplicate route_id {route_id!r}")
        seen.add(route_id)
        for key in ("operation", "method", "params"):
            if contains_vague(route.get(key)):
                errors.append(f"{path}:{index}: vague marker found in {key}")
        entry_type = str(route.get("entry_type", "")).upper()
        if any(hint in entry_type for hint in FINAL_OPERATION_ENTRY_HINTS) and not has_meaningful(route.get("operation")):
            errors.append(f"{path}:{index}: operation-style entry must include operation")
        status = route.get("status")
        if status not in {"discovered", "active", "candidate", "blocked", "needs_expansion"}:
            errors.append(f"{path}:{index}: invalid route status {status!r}")
    return routes


def validate_dispatchers(structured: Path, errors: list[str]) -> list[dict[str, Any]]:
    path = structured / "dispatchers.jsonl"
    dispatchers = read_jsonl(path, errors, required=True)
    seen: set[str] = set()
    for index, dispatcher in enumerate(dispatchers, 1):
        missing = sorted(REQUIRED_DISPATCHER_FIELDS - dispatcher.keys())
        if missing:
            errors.append(f"{path}:{index}: missing fields: {', '.join(missing)}")
        dispatcher_id = str(dispatcher.get("dispatcher_id", ""))
        if not dispatcher_id:
            errors.append(f"{path}:{index}: dispatcher_id is empty")
        elif dispatcher_id in seen:
            errors.append(f"{path}:{index}: duplicate dispatcher_id {dispatcher_id!r}")
        seen.add(dispatcher_id)
        if dispatcher.get("status") not in {"expanded", "needs_expansion", "blocked", "candidate"}:
            errors.append(f"{path}:{index}: invalid dispatcher status {dispatcher.get('status')!r}")
        if dispatcher.get("status") in {"needs_expansion", "blocked"} and not has_meaningful(dispatcher.get("target_rule")):
            errors.append(f"{path}:{index}: blocked dispatcher must keep target_rule evidence")
    return dispatchers


def validate_dispatch_categories(row: dict[str, Any], path: Path, index: int, errors: list[str]) -> None:
    sink_types = as_set(row.get("sink_types"))
    dispatch_to = as_set(row.get("dispatch_to"))
    for sink_type in sink_types:
        required = DISPATCH_REQUIREMENTS.get(sink_type)
        if required and not required.issubset(dispatch_to):
            errors.append(
                f"{path}:{index}: sink type {sink_type!r} must dispatch to {', '.join(sorted(required))}"
            )


def validate_sinks(structured: Path, errors: list[str], required: bool) -> list[dict[str, Any]]:
    path = structured / "sink_candidates.jsonl"
    sinks = read_jsonl(path, errors, required=required)
    seen: set[str] = set()
    for index, sink in enumerate(sinks, 1):
        missing = sorted(REQUIRED_SINK_FIELDS - sink.keys())
        if missing:
            errors.append(f"{path}:{index}: missing fields: {', '.join(missing)}")
        sink_id = str(sink.get("sink_id", ""))
        if not sink_id:
            errors.append(f"{path}:{index}: sink_id is empty")
        elif sink_id in seen:
            errors.append(f"{path}:{index}: duplicate sink_id {sink_id!r}")
        seen.add(sink_id)
        if not as_set(sink.get("sink_types")):
            errors.append(f"{path}:{index}: sink_types is empty")
        if not as_set(sink.get("dispatch_to")):
            errors.append(f"{path}:{index}: dispatch_to is empty")
        validate_dispatch_categories(sink, path, index, errors)
    return sinks


def validate_traces(structured: Path, errors: list[str], required: bool) -> list[dict[str, Any]]:
    path = structured / "trace_sinks.jsonl"
    traces = read_jsonl(path, errors, required=required)
    seen: set[str] = set()
    for index, trace in enumerate(traces, 1):
        missing = sorted(REQUIRED_TRACE_FIELDS - trace.keys())
        if missing:
            errors.append(f"{path}:{index}: missing fields: {', '.join(missing)}")
        trace_id = str(trace.get("trace_id", ""))
        if not trace_id:
            errors.append(f"{path}:{index}: trace_id is empty")
        elif trace_id in seen:
            errors.append(f"{path}:{index}: duplicate trace_id {trace_id!r}")
        seen.add(trace_id)
        helper = trace.get("helper")
        if not isinstance(helper, dict):
            errors.append(f"{path}:{index}: helper must be an object")
        else:
            for key in ("script", "output", "mode"):
                if key not in helper:
                    errors.append(f"{path}:{index}: helper missing {key}")
            if helper.get("mode") not in {"scripted", "manual"}:
                errors.append(f"{path}:{index}: invalid helper mode {helper.get('mode')!r}")
        validate_dispatch_categories(trace, path, index, errors)
    return traces


def validate_coverage(
    structured: Path,
    mechanisms: dict[str, dict[str, Any]],
    routes: list[dict[str, Any]],
    dispatchers: list[dict[str, Any]],
    sinks: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    errors: list[str],
) -> None:
    path = structured / "coverage_report.json"
    data = read_json(path, errors)
    if not isinstance(data, dict):
        return

    expected_counts = {
        "route_total": len(routes),
        "dispatcher_total": len(dispatchers),
    }
    if "sink_total" in data or sinks:
        expected_counts["sink_total"] = len(sinks)
    if "trace_sink_total" in data or traces:
        expected_counts["trace_sink_total"] = len(traces)
    for key, expected in expected_counts.items():
        actual = data.get(key)
        if actual != expected:
            errors.append(f"{path}: {key}={actual!r} does not match actual count {expected}")

    blocked_ids = {
        str(item.get("item_id"))
        for item in data.get("blocked", [])
        if isinstance(item, dict) and item.get("item_id") is not None
    }
    covered_mechanisms = {str(route.get("mechanism_id")) for route in routes if route.get("mechanism_id")}
    covered_mechanisms.update(
        str(dispatcher.get("mechanism_id"))
        for dispatcher in dispatchers
        if dispatcher.get("mechanism_id")
    )
    route_operations_by_mechanism: dict[str, int] = {}
    for route in routes:
        mechanism_id = str(route.get("mechanism_id", ""))
        if has_meaningful(route.get("operation")):
            route_operations_by_mechanism[mechanism_id] = route_operations_by_mechanism.get(mechanism_id, 0) + 1

    for mechanism_id, mechanism in mechanisms.items():
        confidence = str(mechanism.get("confidence", "")).lower()
        if confidence not in {"high", "medium"}:
            continue
        if mechanism_id not in covered_mechanisms and mechanism_id not in blocked_ids:
            errors.append(f"{path}: mechanism {mechanism_id!r} has no route/dispatcher coverage or blocked record")
        operation_rule = str(mechanism.get("operation_rule", "")).strip().lower()
        needs_operation = operation_rule not in {"", "none", "n/a", "no", "false"}
        if needs_operation:
            has_route_operation = route_operations_by_mechanism.get(mechanism_id, 0) > 0
            has_dispatcher = any(str(d.get("mechanism_id")) == mechanism_id for d in dispatchers)
            if not has_route_operation and not has_dispatcher and mechanism_id not in blocked_ids:
                errors.append(f"{path}: mechanism {mechanism_id!r} declares operation_rule but has no operation route, dispatcher, or blocked record")

    for section in ("skipped", "blocked"):
        rows = data.get(section, [])
        if rows is None:
            continue
        if not isinstance(rows, list):
            errors.append(f"{path}: {section} must be a list")
            continue
        for index, item in enumerate(rows):
            if not isinstance(item, dict):
                errors.append(f"{path}: {section}[{index}] must be an object")
                continue
            for key in ("item_id", "item_type", "reason", "evidence", "next_action"):
                if key not in item:
                    errors.append(f"{path}: {section}[{index}] missing {key}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument(
        "--scope",
        choices=("route", "trace", "all"),
        default="all",
        help="route validates route mapper outputs; trace also requires trace_sinks; all requires sink candidates too.",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    structured = output_dir / "structured"
    errors: list[str] = []

    if not structured.is_dir():
        errors.append(f"{structured}: missing structured output directory")
    else:
        mechanisms = validate_mechanisms(structured, errors)
        routes = validate_routes(structured, errors)
        dispatchers = validate_dispatchers(structured, errors)
        sinks = validate_sinks(structured, errors, required=args.scope == "all")
        traces = validate_traces(structured, errors, required=args.scope in {"trace", "all"})
        validate_coverage(structured, mechanisms, routes, dispatchers, sinks, traces, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("[OK] structured coverage checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
