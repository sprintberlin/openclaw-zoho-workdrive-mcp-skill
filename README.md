# Zoho WorkDrive MCP

Connect your agent to Zoho WorkDrive through the Model Context Protocol (MCP). This skill provides everything you need to browse teams and folders, inspect files, search documents, and manage shares using `mcporter`.

This repository contains the public source for the ClawHub skill [`@sprintcx/zoho-workdrive-mcp`](https://clawhub.ai/sprintcx/skills/zoho-workdrive-mcp).

## What This Skill Includes

- Agent Skill instructions in `SKILL.md` (portable SKILL.md format)
- ClawHub release card metadata in `skill-card.md`
- Ready-to-use Python helpers for teams, team folders, folder contents, file inspection, search, and share links
- A JSON Action catalog with three least-privilege profiles: **file-browser**, **content-collaborator**, and **workdrive-admin**
- Security-conscious `mcporter` calls through `subprocess.run([...])` without shell expansion
- Explicit pairing with [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge) for binary file uploads (MCP cannot upload bytes)

## Requirements

| Requirement | Details |
|---|---|
| Zoho WorkDrive MCP Server | A configured endpoint from [mcp.zoho.eu](https://mcp.zoho.eu) |
| mcporter | MCP client CLI (bundled with OpenClaw; elsewhere `npm i -g mcporter`) |
| Endpoint selection | `ZOHO_WORKDRIVE_MCP_URL` for one account; named profiles or `--mcp-url` for multiple accounts |
| Binary file uploads | [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge) — MCP upload actions drop binary bytes; see [Binary file uploads](#binary-file-uploads) |

### Single-account setup

For the common single-account case, set `ZOHO_WORKDRIVE_MCP_URL`. The helper scripts also support named profiles and one-off URL overrides.

Add this to your shell profile, for example `~/.bashrc` or `~/.zshrc`:

```bash
export ZOHO_WORKDRIVE_MCP_URL="https://your-org-zoho-workdrive-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message"
```

Or set it per session:

```bash
ZOHO_WORKDRIVE_MCP_URL="https://your-org-zoho-workdrive-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message" python3 scripts/list_teams.py
```

To verify that it is set without printing the credential:

```bash
if [ -n "$ZOHO_WORKDRIVE_MCP_URL" ]; then echo "ZOHO_WORKDRIVE_MCP_URL is set"; else echo "ZOHO_WORKDRIVE_MCP_URL is not set"; fi
```

Treat `ZOHO_WORKDRIVE_MCP_URL` like a password. It contains WorkDrive access credentials.

## How to Get Your MCP URL

1. Go to [mcp.zoho.eu](https://mcp.zoho.eu) and sign in with your Zoho account.
2. Click **Add Connection** or **New Connection**.
3. Select **Zoho WorkDrive** from the list of available apps.
4. Choose the data center matching your Zoho account: EU, US, IN, AU, JP, or CN.
5. Grant the requested OAuth scopes. Enable only the Actions from the profile you intend to use.
6. After authorization, copy the generated MCP endpoint URL. It looks like:

   ```text
   https://your-org-zoho-workdrive-xxxxx.zohomcp.eu/mcp/abc123def456/message
   ```

7. Set it as `ZOHO_WORKDRIVE_MCP_URL`.

### Multiple organizations and customer accounts

Use one shared profile file instead of changing global environment variables:

```json
{
  "version": 1,
  "profiles": {
    "acme": {
      "services": {
        "workdrive": {"env": "ACME_WORKDRIVE_MCP_URL"}
      }
    }
  }
}
```

```bash
python3 scripts/list_teams.py --profile acme
```

The default file is `~/.config/zoho-mcp/profiles.json`. Endpoint resolution is `--mcp-url`, selected profile, then the app environment variable. Prefer profile entries using `env` or `url_file`; direct URLs in JSON are supported but make the file credential-bearing. Full format: [`references/MULTI_ACCOUNT.md`](references/MULTI_ACCOUNT.md).

## Quick Start

### List available tools on your MCP server

```bash
mcporter list $ZOHO_WORKDRIVE_MCP_URL
```

### List teams

```bash
cat << 'EOF' > /tmp/workdrive_teams.json
{}
EOF
mcporter call "$ZOHO_WORKDRIVE_MCP_URL.ZohoWorkDrive_getAllTeamsOfUser" --args "$(< /tmp/workdrive_teams.json)"
```

### Inspect one file or folder

```bash
cat << 'EOF' > /tmp/workdrive_resource.json
{
  "path_variables": {"resourceId": "abc123"}
}
EOF
mcporter call "$ZOHO_WORKDRIVE_MCP_URL.ZohoWorkDrive_getFileOrFolderDetails" --args "$(< /tmp/workdrive_resource.json)"
```

## Python Scripts

Ready-to-use scripts for common WorkDrive operations. They accept `--profile`, `--profiles-file`, and `--mcp-url`, with `ZOHO_WORKDRIVE_MCP_URL` as the single-account fallback.

The bundled Python scripts call `mcporter` directly through `subprocess.run([...])` and do not invoke a shell. This avoids shell expansion of the credential-bearing `ZOHO_WORKDRIVE_MCP_URL`.

### `list_teams.py`

```bash
python3 scripts/list_teams.py
python3 scripts/list_teams.py --json
```

### `list_team_folders.py`

```bash
python3 scripts/list_team_folders.py --team-id 123456789
python3 scripts/list_team_folders.py --team-id 123456789 --json --limit 20
```

### `list_folder_files.py`

```bash
python3 scripts/list_folder_files.py abc123
python3 scripts/list_folder_files.py abc123 --json --limit 20
```

### `inspect_resource.py`

```bash
python3 scripts/inspect_resource.py abc123
python3 scripts/inspect_resource.py abc123 --breadcrumbs --share-links --json
```

### `search_files.py`

```bash
python3 scripts/search_files.py "contract"
python3 scripts/search_files.py "contract" --team-id 123456789 --json
```

### `list_share_links.py`

```bash
python3 scripts/list_share_links.py abc123
python3 scripts/list_share_links.py abc123 --json
```

## WorkDrive Action Catalog and Profiles

Zoho WorkDrive currently exposes 178 MCP Actions. A single Zoho MCP server accepts at most **300 selected Actions**, so the full catalog still fits, but enabling everything gives a normal agent unnecessary access to team settings, data templates, workflows, and destructive deletes while inflating the per-session tool catalog.

All three profiles in this skill are sized to fit one MCP server:

| Profile | Actions | Fits the 300 limit |
|---|---|---|
| `file-browser` | 71 | yes |
| `content-collaborator` (inherits `file-browser`) | 110 | yes |
| `workdrive-admin` (inherits `content-collaborator`) | 167 | yes |

The catalog is JSON, not prose, so an agent can answer "which Actions do I need for this task" without reading thousands of lines:

- [`references/actions.jsonl`](references/actions.jsonl) is the complete catalog, one JSON object per Action, with the description Zoho itself delivers.
- [`references/profiles.json`](references/profiles.json) holds the role profiles and the per-task Action recipes.
- [`references/CATALOG_FORMAT.md`](references/CATALOG_FORMAT.md) documents the format and how to refresh it after a Zoho catalog change.
- [`references/ACTION_PROFILES.md`](references/ACTION_PROFILES.md) is a short human-readable overview of the configured profiles and tasks.
- [`references/COMMON_WORKFLOWS.md`](references/COMMON_WORKFLOWS.md) contains verified step-by-step procedures.

Query it with the bundled CLI:

```bash
# Which role profiles and task recipes exist
python3 scripts/lookup_actions.py --profiles
python3 scripts/lookup_actions.py --tasks

# Which Actions does a role need, inheritance resolved
python3 scripts/lookup_actions.py --profile file-browser
python3 scripts/lookup_actions.py --profile content-collaborator
python3 scripts/lookup_actions.py --profile workdrive-admin

# Which Actions does one concrete job need, copy-ready for the Zoho setup UI
python3 scripts/lookup_actions.py --task file-and-folder-browsing --names-only

# Find an Action, or read its full Zoho description
python3 scripts/lookup_actions.py --search "share"
python3 scripts/lookup_actions.py --action getFolderFiles

# Check that profiles and tasks still match the catalog
python3 scripts/lookup_actions.py --validate
```

The three roles this skill ships are:

1. **WorkDrive File Browser** (`file-browser`, 71 Actions): read-only lookup. Browse teams, team folders, My Folders, and folder contents; inspect file metadata, previews, versions, comments, labels, shared links, and collaborators; search and download. No create, update, share, or delete Actions.
2. **WorkDrive Content Collaborator** (`content-collaborator`, 110 Actions resolved): inherits `file-browser` and adds daily document work covering uploads, folder and native document creation, rename/move/copy, trash and restore, comments, labels, favorites, and internal or external sharing. No team, group, data template, template library, or workflow administration.
3. **WorkDrive Administrator** (`workdrive-admin`, 167 Actions resolved): inherits `content-collaborator` and adds team folder, team user, group, data template, template library, collection, and workflow administration. All permanent deletes, trash empties, and team-member removal stay denied.

When a specific job needs an Action outside these profiles, add it from a task recipe instead of enabling a whole module:

```bash
python3 scripts/lookup_actions.py --task external-sharing --names-only
```

After configuring the connection at [mcp.zoho.eu](https://mcp.zoho.eu), verify the actual result rather than trusting the profile document:

```bash
mcporter list "$ZOHO_WORKDRIVE_MCP_URL"
```

The profile and catalog use the Action names shown in the Zoho MCP setup UI. Runtime tool names normally add the `ZohoWorkDrive_` prefix.

## Token Optimization (Large MCP Catalogs)

Connecting large MCP servers to OpenClaw can cost a large number of input tokens per session if all tool schemas are loaded eagerly up front.

To avoid loading schemas on session start, enable OpenClaw's built-in Tool Search in `~/.openclaw/openclaw.json`:

```json5
{
  tools: {
    toolSearch: {
      mode: "directory"
    }
  }
}
```

## Troubleshooting

### No endpoint configured

Set `ZOHO_WORKDRIVE_MCP_URL`, use `--profile`, or pass `--mcp-url`. For profile errors, verify the selected name, `--profiles-file`, and the `services.workdrive` entry. See [Multi-account profiles](references/MULTI_ACCOUNT.md).

### `Invalid oauth scope to access this URL`

The MCP connection token may have expired or may not include the required scope. Go to [mcp.zoho.eu](https://mcp.zoho.eu), revoke and reconnect the affected app to get a fresh token.

### Unknown resource ID

WorkDrive resource IDs are opaque. Resolve teams, folders, and files through lookup tools before writing. Never invent an ID from a path or file name.

### Upload reported success but the file is missing

This is the classic Zoho MCP silent failure. Zoho MCP upload actions (`uploadFile`, `uploadNewVersion`) declare `format: "binary"` but drop the bytes because the server builds no `multipart/form-data` request. Use [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge) and verify by re-listing the folder.

## Binary file uploads

Zoho MCP is great for records, navigation, search, sharing, and metadata. **It cannot upload binary files.**

When an agent calls `uploadFile` or `uploadNewVersion` over MCP, the MCP server usually returns `"status": "success"` while the folder remains empty. An agent that trusts that response will falsely claim the file was uploaded.

**Rule: an empty file or attachment response is a failure, never a success.** Always re-list the folder to verify.

Use the companion skill [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge) to move bytes:

| Step | Responsible skill |
|---|---|
| 1. Find the destination team folder or folder ID | `zoho-workdrive-mcp` (this skill) |
| 2. Upload the local file via REST `multipart/form-data` with SHA-256 read-back | `zoho-attachment-bridge` |
| 3. Read metadata, create share links, or set labels on the uploaded file | `zoho-workdrive-mcp` (this skill) |

WorkDrive support in the bridge is tracked in [issue #9](https://github.com/sprintberlin/zoho-attachment-bridge/issues/9). Until that adapter is released, resolve the destination folder via MCP, then use direct REST `multipart/form-data` and verify by re-listing with `list_folder_files.py`.

Native document creation tools (`createNewFile`, `createNativeDocument`, `importToNative`) create or convert Zoho Writer/Sheet/Show documents entirely on the server and do not transfer local bytes, so they work over MCP as expected.

## Repository Files

- `SKILL.md`: Agent Skill instructions.
- `references/actions.jsonl`: Complete Action catalog, one JSON object per Action.
- `references/profiles.json`: Role profiles and per-task Action recipes.
- `references/CATALOG_FORMAT.md`: Catalog format, record shape, and refresh procedure.
- `references/ACTION_PROFILES.md`: Human-readable overview of profiles and task recipes.
- `references/COMMON_WORKFLOWS.md`: Verified workflows for frequent WorkDrive tasks.
- `references/MULTI_ACCOUNT.md`: Portable single-account and multi-account endpoint profiles.
- `skill-card.md`: ClawHub release card metadata.
- `scripts/lookup_actions.py`: Query Actions, profiles, and task recipes; validate them.
- `scripts/import_actions.py`: Rebuild the catalog from a Zoho MCP setup UI dump.
- `scripts/list_teams.py`: List WorkDrive teams for a user.
- `scripts/list_team_folders.py`: List team folders of a team.
- `scripts/list_folder_files.py`: List files and subfolders in a folder.
- `scripts/inspect_resource.py`: Inspect one file or folder, optionally with breadcrumbs and share links.
- `scripts/search_files.py`: Search team folders, folders, and files.
- `scripts/list_share_links.py`: List external share links of a resource.
- `scripts/workdrive_client.py`: Shared MCP caller, pagination, and table helpers.
- `scripts/mcp_endpoint.py`: Shared endpoint and profile resolver.
- `tests/test_endpoint_resolution.py`: Credential-free resolver tests.
- `tests/test_actions_lookup.py`: Catalog, profile, and lookup CLI tests.
- `tests/test_workdrive_helpers.py`: CLI parser and client helper tests.

## Security Notes

The repository version calls `mcporter` directly through `subprocess.run([...])` without shell expansion.

Zoho WorkDrive contains customer documents. Load only required records and never copy contents into chats, logs, or repositories.

## Publish

Publish under the SprintCX ClawHub organization:

```bash
clawhub skill publish . \
  --slug zoho-workdrive-mcp \
  --name "Zoho WorkDrive MCP" \
  --owner sprintcx \
  --version 1.0.0 \
  --source-repo sprintberlin/openclaw-zoho-workdrive-mcp-skill \
  --source-ref main \
  --source-path . \
  --changelog "Initial public WorkDrive MCP skill with JSON action catalog, file-browser, content-collaborator and workdrive-admin profiles, and helper CLIs"
```
