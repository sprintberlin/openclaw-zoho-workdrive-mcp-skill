"""Tests for the WorkDrive actions catalog, profiles, and lookup CLI."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

REPOSITORY = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPOSITORY / "references" / "actions.jsonl"
PROFILES_PATH = REPOSITORY / "references" / "profiles.json"
LOOKUP_SCRIPT = REPOSITORY / "scripts" / "lookup_actions.py"

sys.path.insert(0, str(REPOSITORY / "scripts"))
import lookup_actions  # noqa: E402
import import_actions  # noqa: E402


class ActionsCatalogAndLookupTests(unittest.TestCase):
    def test_catalog_file_is_valid_jsonl(self):
        self.assertTrue(CATALOG_PATH.exists(), f"missing {CATALOG_PATH}")
        lines = [
            line.strip()
            for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertGreaterEqual(len(lines), 178)
        keys = set()
        for idx, line in enumerate(lines, start=1):
            data = json.loads(line)
            for required in ("key", "name", "summary", "description"):
                self.assertIn(required, data)
                self.assertTrue(str(data[required]).strip())
            self.assertNotIn(data["key"], keys, f"duplicate key {data['key']} at line {idx}")
            keys.add(data["key"])

    def test_profiles_file_is_valid_and_consistent(self):
        self.assertTrue(PROFILES_PATH.exists(), f"missing {PROFILES_PATH}")
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        self.assertEqual(data.get("version"), 1)
        self.assertEqual(data.get("service"), "workdrive")
        self.assertIn("profiles", data)
        self.assertIn("tasks", data)

        result = subprocess.run(
            [sys.executable, str(LOOKUP_SCRIPT), "--validate"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0, f"validation failed:\n{result.stdout}\n{result.stderr}"
        )
        self.assertIn("Validation OK", result.stdout)

    def test_lookup_cli_profiles_listing(self):
        result = subprocess.run(
            [sys.executable, str(LOOKUP_SCRIPT), "--profiles"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("file-browser", result.stdout)
        self.assertIn("content-collaborator", result.stdout)
        self.assertIn("workdrive-admin", result.stdout)

    def test_lookup_cli_task_inspection(self):
        result = subprocess.run(
            [sys.executable, str(LOOKUP_SCRIPT), "--task", "file-and-folder-browsing"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("getFolderFiles", result.stdout)
        self.assertIn("getFileOrFolderDetails", result.stdout)

    def test_lookup_cli_search_names_only(self):
        result = subprocess.run(
            [sys.executable, str(LOOKUP_SCRIPT), "--search", "share", "--names-only"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("createExternalShareLink", result.stdout)

    def test_lookup_cli_action_inspection(self):
        result = subprocess.run(
            [sys.executable, str(LOOKUP_SCRIPT), "--action", "getFolderFiles", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data.get("key"), "getFolderFiles")
        self.assertIn("files", data.get("description", "").lower())

    def test_all_profiles_fit_within_300_action_limit(self):
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        browser = lookup_actions.resolve_profile_actions("file-browser", profiles)
        member = lookup_actions.resolve_profile_actions("team-member", profiles)
        collaborator = lookup_actions.resolve_profile_actions("content-collaborator", profiles)
        admin = lookup_actions.resolve_profile_actions("workdrive-admin", profiles)
        self.assertEqual(len(browser), 71)
        self.assertEqual(len(member), 102)
        self.assertEqual(len(collaborator), 110)
        self.assertEqual(len(admin), 167)
        self.assertLessEqual(len(admin), 300)

    def test_file_browser_is_read_only(self):
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        actions = lookup_actions.resolve_profile_actions("file-browser", profiles)
        self.assertIn("getFolderFiles", actions)
        self.assertIn("getFileOrFolderDetails", actions)
        self.assertIn("searchTeamFoldersFiles", actions)
        self.assertNotIn("uploadFile", actions)
        self.assertNotIn("createFolder", actions)
        self.assertNotIn("createExternalShareLink", actions)
        self.assertNotIn("createTeamFolder", actions)

    def test_content_collaborator_inherits_browser_and_adds_writes(self):
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        actions = lookup_actions.resolve_profile_actions("content-collaborator", profiles)
        self.assertIn("getFolderFiles", actions)
        self.assertIn("uploadFile", actions)
        self.assertIn("createFolder", actions)
        self.assertIn("createExternalShareLink", actions)
        self.assertNotIn("createTeamFolder", actions)
        self.assertNotIn("inviteNewUsers", actions)

    def test_team_member_can_write_but_not_delete(self):
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        actions = lookup_actions.resolve_profile_actions("team-member", profiles)
        for write_action in (
            "uploadFile",
            "uploadNewVersion",
            "createFolder",
            "createNewFile",
            "createNativeDocument",
            "createComments",
            "updateComments",
            "renameFileOrFolder",
            "moveFileOrFolder",
            "copyFileOrFolder",
            "createExternalShareLink",
            "createFilesFoldersShare",
            "updateFilesFoldersShare",
            "createLabel",
            "updateLabels",
            "restoreToVersion",
        ):
            self.assertIn(write_action, actions)
        for denied in (
            "deleteComment",
            "deleteExternalShareLink",
            "deleteLabel",
            "deletePermission",
            "deleteSharedLink",
            "moveToTrash",
            "updateFilesFolders",
            "updateMultipleFilesFolders",
            "emptyTrash",
            "emptyMyFolderTrash",
            "deleteTeamfolder",
            "deleteVersion",
        ):
            self.assertNotIn(denied, actions)

    def test_collaborator_adds_delete_actions_on_top_of_team_member(self):
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        member = lookup_actions.resolve_profile_actions("team-member", profiles)
        collaborator = lookup_actions.resolve_profile_actions("content-collaborator", profiles)
        self.assertEqual(
            sorted(set(collaborator) - set(member)),
            sorted(
                [
                    "deleteComment",
                    "deleteExternalShareLink",
                    "deleteLabel",
                    "deletePermission",
                    "deleteSharedLink",
                    "moveToTrash",
                    "updateFilesFolders",
                    "updateMultipleFilesFolders",
                ]
            ),
        )

    def test_workdrive_admin_denies_destructive_actions(self):
        data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
        profiles = data["profiles"]
        actions = lookup_actions.resolve_profile_actions("workdrive-admin", profiles)
        self.assertIn("createTeamFolder", actions)
        self.assertIn("inviteNewUsers", actions)
        for denied in (
            "deleteTeamfolder",
            "emptyTrash",
            "emptyMyFolderTrash",
            "deleteGroup",
            "updateUsers",
        ):
            self.assertNotIn(denied, actions)

    def test_importer_parses_dump_and_handles_variants(self):
        sample_dump = (
            "Authorize On Demand\n"
            "Group view\n"
            "All Tools\n"
            "Tools Name\n"
            "getFolderFiles Retrieve a list of files and subfolders.\n"
        )
        parsed = import_actions.parse_dump(sample_dump)
        keys = {entry["key"]: entry for entry in parsed}
        self.assertIn("getFolderFiles", keys)
        self.assertEqual(keys["getFolderFiles"]["name"], "getFolderFiles")

    def test_importer_merges_additions_and_marks_removals(self):
        known = {
            "oldAction": {
                "key": "oldAction",
                "name": "oldAction",
                "summary": "Old",
                "description": "Old action",
                "added": "2026-08-01",
            }
        }
        current_entries = [
            {
                "key": "newAction",
                "name": "newAction",
                "summary": "New",
                "description": "New action",
            }
        ]
        merged = import_actions.merge(current_entries, known, today="2026-09-18")
        by_key = {item["key"]: item for item in merged}
        self.assertEqual(by_key["newAction"]["added"], "2026-09-18")
        self.assertNotIn("removed", by_key["newAction"])
        self.assertEqual(by_key["oldAction"]["removed"], "2026-09-18")


if __name__ == "__main__":
    unittest.main()
