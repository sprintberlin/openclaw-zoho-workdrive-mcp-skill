#!/usr/bin/env python3
"""List files and folders inside a Zoho WorkDrive folder through mcporter."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workdrive_client import (  # noqa: E402
    ENDPOINT,
    build_base_parser,
    call,
    field,
    finish,
    positive_int,
    rows,
)

COLUMNS = [
    ("ID", ["id", "resource_id"]),
    ("Name", ["name", "display_attr_name"]),
    ("Type", ["type", "resource_type"]),
    ("Size", ["size", "storage_info"]),
    ("Modified", ["modified_time", "last_modified_time"]),
]


def build_parser():
    parser = build_base_parser("List files and subfolders in a Zoho WorkDrive folder.")
    parser.add_argument("folder_id", help="WorkDrive folder resource ID")
    parser.add_argument("--limit", type=positive_int, help="return at most this many items")
    parser.add_argument("--page-size", type=positive_int, default=50, help="page size (default: 50)")
    parser.add_argument("--full", action="store_true", help="with --json, print complete records")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    ENDPOINT.configure(args)

    result = call(
        "getFolderFiles",
        {"path_variables": {"folder_id": args.folder_id}},
        timeout=args.timeout,
    )
    records = rows(result) if "error" not in result else []
    if args.limit is not None:
        records = records[: args.limit]

    if args.json and not args.full:
        records = [
            {
                "id": field(row, ["id", "resource_id"], ""),
                "name": field(row, ["name", "display_attr_name"], ""),
                "type": field(row, ["type", "resource_type"], ""),
                "size": field(row, ["size"], ""),
            }
            for row in records
        ]
    return finish(result, records, args, COLUMNS, empty="No files or folders found.")


if __name__ == "__main__":
    sys.exit(main())
