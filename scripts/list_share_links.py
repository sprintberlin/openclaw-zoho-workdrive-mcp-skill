#!/usr/bin/env python3
"""List the external share links of a Zoho WorkDrive resource through mcporter."""

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
    ("ID", ["id", "link_id"]),
    ("Type", ["link_type", "type", "role_id"]),
    ("Link", ["link", "share_link", "download_link", "url"]),
    ("Expires", ["expiration_date", "expiry_date"]),
    ("Password", ["is_password_protected", "password_protected"]),
]


def build_parser():
    parser = build_base_parser("List external share links of a Zoho WorkDrive resource.")
    parser.add_argument("resource_id", help="WorkDrive file or folder resource ID")
    parser.add_argument("--full", action="store_true", help="with --json, print complete records")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    ENDPOINT.configure(args)

    result = call(
        "getFileShareLinks",
        {"path_variables": {"resourceId": args.resource_id}},
        timeout=args.timeout,
    )
    records = rows(result) if "error" not in result else []

    if args.json and not args.full:
        records = [
            {
                "id": field(row, ["id", "link_id"], ""),
                "type": field(row, ["link_type", "type", "role_id"], ""),
                "link": field(row, ["link", "share_link", "download_link", "url"], ""),
                "expires": field(row, ["expiration_date", "expiry_date"], ""),
            }
            for row in records
        ]
    return finish(result, records, args, COLUMNS, empty="No external share links found.")


if __name__ == "__main__":
    sys.exit(main())
