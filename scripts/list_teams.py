#!/usr/bin/env python3
"""List the Zoho WorkDrive teams a user belongs to, through mcporter."""

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
    rows,
)

COLUMNS = [
    ("ID", ["id", "team_id", "teamId"]),
    ("Name", ["name", "team_name", "display_name"]),
    ("Edition", ["edition", "plan"]),
    ("Role", ["role", "user_role"]),
]


def build_parser():
    parser = build_base_parser("List Zoho WorkDrive teams for a user.")
    parser.add_argument(
        "--user-id",
        metavar="ID",
        help="Zoho user ID (zuid); omit to let the server use the current user",
    )
    parser.add_argument("--full", action="store_true", help="with --json, print complete records")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    ENDPOINT.configure(args)

    payload = {}
    if args.user_id:
        payload["path_variables"] = {"userId": args.user_id}

    result = call("getAllTeamsOfUser", payload, timeout=args.timeout)
    records = rows(result) if "error" not in result else []

    if args.json and not args.full:
        records = [
            {
                "id": field(row, ["id", "team_id"], ""),
                "name": field(row, ["name", "team_name", "display_name"], ""),
                "edition": field(row, ["edition", "plan"], ""),
            }
            for row in records
        ]
    return finish(result, records, args, COLUMNS, empty="No teams found.")


if __name__ == "__main__":
    sys.exit(main())
