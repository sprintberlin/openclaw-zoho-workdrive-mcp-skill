#!/usr/bin/env python3
"""Inspect one Zoho WorkDrive file or folder by resource ID through mcporter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from workdrive_client import ENDPOINT, build_base_parser, call, field, rows  # noqa: E402


def build_parser():
    parser = build_base_parser("Inspect one Zoho WorkDrive file or folder.")
    parser.add_argument("resource_id", help="WorkDrive file or folder resource ID")
    parser.add_argument(
        "--share-links",
        action="store_true",
        help="also fetch the external share links of the resource",
    )
    parser.add_argument(
        "--breadcrumbs",
        action="store_true",
        help="also fetch the folder hierarchy of the resource",
    )
    return parser


def print_summary(resource):
    print(f"Resource:   {field(resource, ['name', 'display_attr_name'])} ({field(resource, ['id', 'resource_id'])})")
    print(f"Type:       {field(resource, ['type', 'resource_type'])}")
    print(f"Extension:  {field(resource, ['extn', 'extension'])}")
    print(f"Size:       {field(resource, ['size', 'storage_info'])}")
    print(f"Owner:      {field(resource, ['created_by', 'owner_name', 'creator'])}")
    print(f"Parent:     {field(resource, ['parent_id', 'parentId'])}")
    print(f"Created:    {field(resource, ['created_time', 'created_time_in_millisecond'])}")
    print(f"Modified:   {field(resource, ['modified_time', 'last_modified_time'])}")


def unwrap(result):
    payload = result.get("data", result)
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        payload = payload["data"]
    return payload if isinstance(payload, dict) else {}


def main(argv=None):
    args = build_parser().parse_args(argv)
    ENDPOINT.configure(args)

    result = call(
        "getFileOrFolderDetails",
        {"path_variables": {"resource_id": args.resource_id}},
        timeout=args.timeout,
    )
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    resource = unwrap(result)
    payload = {"resource": resource}

    if args.share_links:
        links = call(
            "getFileShareLinks",
            {"path_variables": {"resource_id": args.resource_id}},
            timeout=args.timeout,
        )
        if "error" in links:
            print(f"Error: {links['error']}", file=sys.stderr)
            return 1
        payload["share_links"] = rows(links)

    if args.breadcrumbs:
        trail = call(
            "breadcrumbsOfFile",
            {"path_variables": {"resource_id": args.resource_id}},
            timeout=args.timeout,
        )
        if "error" in trail:
            print(f"Error: {trail['error']}", file=sys.stderr)
            return 1
        payload["breadcrumbs"] = rows(trail)

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print_summary(resource)

    if args.breadcrumbs:
        trail = payload.get("breadcrumbs") or []
        names = [field(item, ["name", "display_attr_name"], "") for item in trail]
        print(f"\nPath: {' / '.join(name for name in names if name) or '-'}")

    if args.share_links:
        links = payload.get("share_links") or []
        if not links:
            print("\nNo external share links found.")
        else:
            print(f"\n{len(links)} share link(s):")
            for link in links:
                url = field(link, ["link", "share_link", "download_link", "url"], "")
                kind = field(link, ["link_type", "type", "role_id"], "link")
                print(f"  - {kind}: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
