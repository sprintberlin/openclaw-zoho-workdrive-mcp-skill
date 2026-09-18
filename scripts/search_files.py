#!/usr/bin/env python3
"""Search Zoho WorkDrive team folders, folders, and files through mcporter."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workdrive_client import (  # noqa: E402
    ENDPOINT,
    build_base_parser,
    field,
    finish,
    paginate,
    positive_int,
    rows,
)

COLUMNS = [
    ("ID", ["id", "resource_id"]),
    ("Name", ["name", "display_attr_name"]),
    ("Type", ["type", "resource_type"]),
    ("Parent", ["parent_id", "parent_name"]),
    ("Modified", ["modified_time", "last_modified_time"]),
]


def build_parser():
    parser = build_base_parser("Search Zoho WorkDrive files and folders.")
    parser.add_argument("query", help="search keyword")
    parser.add_argument("--team-id", metavar="ID", help="restrict the search to one team")
    parser.add_argument("--limit", type=positive_int, help="return at most this many results")
    parser.add_argument("--page-size", type=positive_int, default=50, help="page size (default: 50)")
    parser.add_argument("--full", action="store_true", help="with --json, print complete records")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    ENDPOINT.configure(args)

    params = {"query": args.query}
    if args.team_id:
        params["teamId"] = args.team_id

    result = paginate(
        "searchTeamFoldersFiles",
        params,
        page_size=args.page_size,
        max_records=args.limit,
        timeout=args.timeout,
    )
    records = rows(result) if "error" not in result else []

    if args.json and not args.full:
        records = [
            {
                "id": field(row, ["id", "resource_id"], ""),
                "name": field(row, ["name", "display_attr_name"], ""),
                "type": field(row, ["type", "resource_type"], ""),
            }
            for row in records
        ]
    return finish(result, records, args, COLUMNS, empty="No matching files or folders found.")


if __name__ == "__main__":
    sys.exit(main())
