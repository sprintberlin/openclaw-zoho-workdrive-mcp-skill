#!/usr/bin/env python3
"""Shared Zoho WorkDrive MCP call helpers for the bundled CLIs.

Every helper resolves its endpoint through mcp_endpoint.EndpointSelector and
calls `mcporter` through subprocess.run([...]) without shell expansion, so the
credential-bearing MCP URL is never expanded by a shell.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from mcp_endpoint import (  # noqa: E402
    EndpointResolutionError,
    EndpointSelector,
    add_endpoint_arguments,
)

SERVICE = "workdrive"
ENV_VARS = ("ZOHO_WORKDRIVE_MCP_URL",)
TOOL_PREFIX = "ZohoWorkdrive_"

# The live Zoho MCP server names most tools after the setup-UI Action with
# spaces replaced by underscores, but some actions keep a different camelCase
# or Title_Snake name. Map every action used by the bundled helpers to its
# verified live tool name (confirmed against a live server on 2026-09-21).
TOOL_ALIASES = {
    "getUserInfo": "Get_User_Info",
    "getAllTeamsOfUser": "Get_All_Teams_Of_User",
    "breadcrumbsOfFile": "Breadcrumbs_Of_File",
}


def runtime_tool(tool):
    """Resolve a catalog action name to the live MCP tool name."""
    for prefix in (TOOL_PREFIX, "ZohoWorkDrive_"):
        if tool.startswith(prefix):
            tool = tool[len(prefix):]
            break
    tool = TOOL_ALIASES.get(tool, tool)
    return f"{TOOL_PREFIX}{tool}"


ENDPOINT = EndpointSelector(SERVICE, ENV_VARS)


def positive_int(value):
    """argparse type for a positive integer."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def build_base_parser(description):
    """Return a parser carrying the shared endpoint and timeout options."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument(
        "--timeout",
        type=positive_int,
        default=30,
        help="MCP call timeout in seconds (default: 30)",
    )
    add_endpoint_arguments(parser)
    return parser


def call(tool, args, timeout=30):
    """Call one WorkDrive MCP Action and return a parsed dict or {"error": ...}."""
    try:
        mcp_url = ENDPOINT.get()
    except EndpointResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    tool = runtime_tool(tool)

    command = [
        "mcporter",
        "call",
        f"{mcp_url}.{tool}",
        "--args",
        json.dumps(args, ensure_ascii=False),
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return {"error": "mcporter executable not found"}
    except subprocess.TimeoutExpired:
        return {"error": "mcporter call timed out"}

    if result.returncode != 0:
        return {"error": result.stderr.strip() or "mcporter call failed"}
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": result.stderr.strip() or "mcporter returned invalid JSON"}
    if not isinstance(parsed, dict):
        return {"data": parsed}
    if parsed.get("status") in {"error", "failure"}:
        return {
            "error": parsed.get("error")
            or parsed.get("message")
            or parsed.get("data")
            or "Zoho WorkDrive request failed"
        }
    return parsed


def rows(result):
    """Normalize the common WorkDrive MCP envelopes down to a list of records."""
    if not isinstance(result, dict) or "error" in result:
        return []

    def extract(node):
        if isinstance(node, list):
            return node
        if isinstance(node, dict):
            for key in ("data", "files", "folders", "teams", "response", "result"):
                if key in node:
                    inner = extract(node[key])
                    if inner is not None:
                        return inner
        return None

    found = extract(result.get("data", result))
    return found if found is not None else []


def attributes(record):
    """Return the JSON:API style `attributes` object when WorkDrive wraps a record."""
    if not isinstance(record, dict):
        return {}
    inner = record.get("attributes")
    return inner if isinstance(inner, dict) else {}


def field(record, candidates, default="-"):
    """Read the first matching field from a record or its attributes, case-insensitively."""
    if not isinstance(record, dict):
        return default

    for source in (record, attributes(record)):
        if not source:
            continue
        lowered = {str(key).lower(): key for key in source}
        for candidate in candidates:
            actual = lowered.get(candidate.lower())
            if actual is None:
                continue
            value = source[actual]
            if value in (None, ""):
                continue
            if isinstance(value, dict):
                for nested in ("name", "display_name", "displayName", "email", "id"):
                    if value.get(nested):
                        return str(value[nested])
                return str(value)
            if isinstance(value, bool):
                return "yes" if value else "no"
            return str(value)
    return default


def paginate(
    tool,
    path_variables=None,
    params=None,
    page_size=50,
    max_records=None,
    timeout=30,
    offset_key="page[offset]",
    limit_key="page[limit]",
):
    """Collect records across WorkDrive `page[offset]`/`page[limit]` pagination."""
    collected = []
    offset = 0

    while True:
        request_limit = page_size
        if max_records is not None:
            remaining = max_records - len(collected)
            if remaining <= 0:
                break
            request_limit = min(request_limit, remaining)

        query = dict(params or {})
        query[offset_key] = str(offset)
        query[limit_key] = str(request_limit)

        payload = {"path_variables": dict(path_variables or {}), "query_params": query}
        result = call(tool, payload, timeout=timeout)
        if "error" in result:
            return result

        page = rows(result)
        collected.extend(page)
        if not page or len(page) < request_limit:
            break
        offset += len(page)

    if max_records is not None:
        collected = collected[:max_records]
    return {"data": collected, "info": {"count": len(collected)}}


def print_table(records, columns, empty="No records found."):
    """Print a compact aligned table for a list of records."""
    if not records:
        print(empty)
        return

    widths = {}
    for label, keys in columns:
        longest = max((len(field(row, keys)) for row in records), default=0)
        widths[label] = max(len(label), min(longest, 40))

    print(" | ".join(label.ljust(widths[label]) for label, _ in columns))
    print("-+-".join("-" * widths[label] for label, _ in columns))
    for row in records:
        cells = []
        for label, keys in columns:
            value = field(row, keys)
            if len(value) > 40:
                value = value[:37] + "..."
            cells.append(value.ljust(widths[label]))
        print(" | ".join(cells))
    print(f"\n{len(records)} record(s)")


def finish(result, records, args, columns, empty="No records found."):
    """Render a helper result and return the process exit code."""
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print_table(records, columns, empty=empty)
    return 0
