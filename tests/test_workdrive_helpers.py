"""Credential-free tests for WorkDrive helper CLIs and shared client helpers."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import inspect_resource  # noqa: E402
import list_folder_files  # noqa: E402
import list_share_links  # noqa: E402
import list_team_folders  # noqa: E402
import list_teams  # noqa: E402
import search_files  # noqa: E402
import workdrive_client  # noqa: E402


class WorkDriveClientHelperTests(unittest.TestCase):
    def test_rows_unwraps_nested_data_lists(self):
        result = {"data": {"data": [{"id": "1"}, {"id": "2"}]}}
        self.assertEqual(workdrive_client.rows(result), [{"id": "1"}, {"id": "2"}])

    def test_rows_unwraps_files_key(self):
        result = {"data": {"files": [{"id": "f1"}]}}
        self.assertEqual(workdrive_client.rows(result), [{"id": "f1"}])

    def test_rows_returns_empty_on_error(self):
        self.assertEqual(workdrive_client.rows({"error": "boom"}), [])

    def test_field_reads_jsonapi_attributes(self):
        record = {"id": "abc", "attributes": {"name": "Contracts", "type": "folder"}}
        self.assertEqual(workdrive_client.field(record, ["name"]), "Contracts")
        self.assertEqual(workdrive_client.field(record, ["id"]), "abc")

    def test_field_reads_nested_name(self):
        record = {"created_by": {"name": "Ada Lovelace", "id": "9"}}
        self.assertEqual(workdrive_client.field(record, ["created_by"]), "Ada Lovelace")

    def test_positive_int_rejects_zero(self):
        with self.assertRaises(Exception):
            workdrive_client.positive_int("0")


class HelperParserTests(unittest.TestCase):
    def test_list_teams_help_exits_zero(self):
        with self.assertRaises(SystemExit) as ctx:
            list_teams.build_parser().parse_args(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_list_teams_unknown_option_exits_two(self):
        with self.assertRaises(SystemExit) as ctx:
            list_teams.build_parser().parse_args(["--not-a-real-flag"])
        self.assertEqual(ctx.exception.code, 2)

    def test_list_team_folders_requires_team_id(self):
        with self.assertRaises(SystemExit) as ctx:
            list_team_folders.build_parser().parse_args([])
        self.assertEqual(ctx.exception.code, 2)

    def test_list_folder_files_requires_folder_id(self):
        with self.assertRaises(SystemExit) as ctx:
            list_folder_files.build_parser().parse_args([])
        self.assertEqual(ctx.exception.code, 2)

    def test_inspect_resource_requires_id(self):
        with self.assertRaises(SystemExit) as ctx:
            inspect_resource.build_parser().parse_args([])
        self.assertEqual(ctx.exception.code, 2)

    def test_search_files_requires_query(self):
        with self.assertRaises(SystemExit) as ctx:
            search_files.build_parser().parse_args([])
        self.assertEqual(ctx.exception.code, 2)

    def test_list_share_links_requires_id(self):
        with self.assertRaises(SystemExit) as ctx:
            list_share_links.build_parser().parse_args([])
        self.assertEqual(ctx.exception.code, 2)

    def test_list_teams_without_endpoint_exits_one(self):
        with mock.patch.object(list_teams.ENDPOINT, "configure"):
            with mock.patch.object(
                list_teams,
                "call",
                return_value={"error": "no Zoho WorkDrive MCP endpoint configured"},
            ):
                code = list_teams.main([])
        self.assertEqual(code, 1)

    def test_inspect_resource_summary_uses_attributes(self):
        resource = {
            "id": "abc123",
            "attributes": {
                "name": "Q3 Report",
                "type": "file",
                "extn": "pdf",
                "size": "1024",
            },
        }
        inspect_resource.print_summary(resource)


if __name__ == "__main__":
    unittest.main()
