---
name: "zoho-workdrive-mcp"
description: "Zoho WorkDrive via MCP with action catalog, least-privilege profiles, team, folder, file, search, and share helper scripts, and verified document workflows."
---

# Zoho WorkDrive MCP

Use Zoho WorkDrive through an MCP endpoint from `mcp.zoho.eu`. This skill is the canonical home for WorkDrive-specific MCP action documentation and least-privilege action profiles.

Source: [sprintberlin/openclaw-zoho-workdrive-mcp-skill](https://github.com/sprintberlin/openclaw-zoho-workdrive-mcp-skill)

## Requirements

- A Zoho WorkDrive MCP endpoint from `mcp.zoho.eu`
- `mcporter`
- Endpoint configuration via `ZOHO_WORKDRIVE_MCP_URL`, `--profile`, or `--mcp-url`

Treat the endpoint as a credential. Never print it, commit it, or copy it into tickets, prompts, or chats.

## First setup

1. Create or open a Zoho WorkDrive connection at `mcp.zoho.eu`.
2. Select only the required Actions. Resolve the exact list from the JSON catalog:

```bash
python3 scripts/lookup_actions.py --profiles
python3 scripts/lookup_actions.py --profile file-browser --names-only
python3 scripts/lookup_actions.py --profile content-collaborator --names-only
python3 scripts/lookup_actions.py --profile workdrive-admin --names-only
python3 scripts/lookup_actions.py --task file-and-folder-browsing --names-only
```

3. Search the catalog when a profile or task lacks a required Action:

```bash
python3 scripts/lookup_actions.py --search "share"
python3 scripts/lookup_actions.py --action getFolderFiles
```

4. Configure one default endpoint with `ZOHO_WORKDRIVE_MCP_URL`, or create named profiles using [references/MULTI_ACCOUNT.md](references/MULTI_ACCOUNT.md).
5. Inspect the selected live server before relying on an Action:

```bash
mcporter list "$ZOHO_WORKDRIVE_MCP_URL"
```

The catalog describes possible Actions. It does not prove that an Action is enabled on a particular MCP server. Runtime tool names usually have the `ZohoWorkDrive_` prefix, while the Zoho MCP setup UI uses the Action name without that prefix.

## Endpoint selection

For one account, set `ZOHO_WORKDRIVE_MCP_URL`. For multiple accounts, pass `--profile NAME` to a bundled helper. Profiles live in `~/.config/zoho-mcp/profiles.json` by default and can resolve endpoints through an environment variable, a local URL file, or a direct URL. One-off `--mcp-url URL` overrides everything, but may expose the credential in shell history or process listings.

Resolution order is `--mcp-url`, selected profile, then the environment fallback. Profile selection is `--profile`, `ZOHO_WORKDRIVE_MCP_PROFILE`, then `ZOHO_MCP_PROFILE`. See [references/MULTI_ACCOUNT.md](references/MULTI_ACCOUNT.md) for the shared CRM, People, Books, Desk, and WorkDrive format.

## Safe workflow

1. Confirm the correct Zoho account and organization. Never reuse an endpoint from another customer.
2. Identify the team first. `getAllTeamsOfUser` is the first-choice lookup. Confirm with `getTeamInfo`.
3. Resolve folders and files through lookup tools (`listAllTeamFoldersOfaTeam`, `getFolderFiles`, `searchTeamFoldersFiles`). Never invent a resource ID from a path or file name.
4. Read before writing. Inspect a resource with `getFileOrFolderDetails` and reconstruct its location with `breadcrumbsOfFile`.
5. For writes, send only intended fields and read the affected resource back immediately.
6. Keep permanent deletes, trash empties, and team-member removal disabled unless the task explicitly requires them.

## Common calls

List teams for the current user:

```bash
cat > /tmp/workdrive_teams.json <<'JSON'
{}
JSON
mcporter call "$ZOHO_WORKDRIVE_MCP_URL.ZohoWorkDrive_getAllTeamsOfUser" --args "$(< /tmp/workdrive_teams.json)"
```

Look up a file or folder by resource ID:

```bash
cat > /tmp/workdrive_resource.json <<'JSON'
{"path_variables": {"resourceId": "abc123"}}
JSON
mcporter call "$ZOHO_WORKDRIVE_MCP_URL.ZohoWorkDrive_getFileOrFolderDetails" --args "$(< /tmp/workdrive_resource.json)"
```

Use the schema shown by the live MCP server when it differs from these examples. For deeply nested arguments, use a temporary JSON file instead of fragile shell quoting.

## Answering "which Actions do I need"

The catalog is JSON, not prose. Never read the whole catalog into context to answer an Action question. Query it instead.

```bash
# Role profiles, inheritance resolved
python3 scripts/lookup_actions.py --profile file-browser
python3 scripts/lookup_actions.py --profile content-collaborator
python3 scripts/lookup_actions.py --profile workdrive-admin

# One concrete job
python3 scripts/lookup_actions.py --tasks
python3 scripts/lookup_actions.py --task file-and-folder-browsing

# Keyword search across every Action name and description
python3 scripts/lookup_actions.py --search "share"

# Full Zoho description of a single Action, including its dependencyTools note
python3 scripts/lookup_actions.py --action getFolderFiles

# Check that profiles and tasks still match the catalog
python3 scripts/lookup_actions.py --validate
```

Add `--names-only` for a copy-ready list for the Zoho MCP setup UI, or `--json` for structured output.

Data files: [references/actions.jsonl](references/actions.jsonl) holds every known Action with its Zoho description; [references/profiles.json](references/profiles.json) holds role profiles and task recipes. Format and maintenance: [references/CATALOG_FORMAT.md](references/CATALOG_FORMAT.md).

## Bundled scripts

The scripts resolve the endpoint via `--mcp-url`, `--profile` (`~/.config/zoho-mcp/profiles.json`), or `ZOHO_WORKDRIVE_MCP_URL`, call `mcporter` without shell expansion, paginate results, and normalize common Zoho MCP response envelopes.

```bash
python3 scripts/list_teams.py
python3 scripts/list_team_folders.py --team-id 123456789 --json
python3 scripts/list_folder_files.py abc123 --limit 20
python3 scripts/inspect_resource.py abc123 --breadcrumbs --share-links
python3 scripts/search_files.py "contract" --team-id 123456789
python3 scripts/list_share_links.py abc123
```

Supported options:

- `list_teams.py`: `--user-id`, `--full`, `--json`, `--timeout`
- `list_team_folders.py`: `--team-id` (required), `--limit`, `--page-size`, `--full`, `--json`, `--timeout`
- `list_folder_files.py`: positional `folder_id`, `--limit`, `--page-size`, `--full`, `--json`, `--timeout`
- `inspect_resource.py`: positional `resource_id`, `--share-links`, `--breadcrumbs`, `--json`, `--timeout`
- `search_files.py`: positional `query`, `--team-id`, `--limit`, `--page-size`, `--full`, `--json`, `--timeout`
- `list_share_links.py`: positional `resource_id`, `--full`, `--json`, `--timeout`
- All helpers: `--mcp-url`, `--profile`, `--profiles-file`

Run any helper with `--help` without configuring credentials. Unknown or incomplete options must exit with status 2.

## Role profiles and the 300-Action limit

A Zoho MCP server accepts at most 300 selected Actions per connection. The entire WorkDrive catalog currently has 178 Actions, so every profile fits on one MCP server. Use the smallest matching profile anyway so the session tool catalog stays small.

| Profile | Actions | Fits one MCP server |
|---|---|---|
| `file-browser` | 71 | yes |
| `content-collaborator` (inherits `file-browser`) | 110 | yes |
| `workdrive-admin` (inherits `content-collaborator`) | 167 | yes |

- **`file-browser`** (71): Read-only navigation. Teams, team folders, My Folders, folder contents, file metadata, previews, versions, comments, labels, shared links, collaborators, search, and downloads. No create, update, share, or delete Actions.
- **`content-collaborator`** (110 resolved): Inherits `file-browser` and adds daily document work: upload and versioning, folder and native document creation, rename/move/copy, trash and restore, comments, labels, favorites, and internal or external sharing.
- **`workdrive-admin`** (167 resolved): Inherits `content-collaborator` and adds team folder, team user, group, data template, template library, collection, and workflow administration. Explicitly denies permanent deletes, trash purges, and team-member removal.

If a task needs an Action outside a profile, add it deliberately from a task recipe rather than enabling a whole module.

## References

- [Action catalog](references/actions.jsonl): every known WorkDrive Action with its Zoho description, one JSON object per line
- [Profiles and task recipes](references/profiles.json): role profiles and per-task Action sets
- [Catalog format](references/CATALOG_FORMAT.md): why the catalog is JSON, the record shape, and how to refresh it
- [Action profiles overview](references/ACTION_PROFILES.md): human-readable summary of the configured profiles and tasks
- [Common workflows](references/COMMON_WORKFLOWS.md): verified step-by-step procedures for frequent WorkDrive tasks
- [Multi-account profiles](references/MULTI_ACCOUNT.md): portable endpoint selection for one or many Zoho accounts

Query the catalog with `scripts/lookup_actions.py` instead of loading `actions.jsonl` into context. Load workflows when executing a covered task.

## Troubleshooting and safety

- **No endpoint configured**: set `ZOHO_WORKDRIVE_MCP_URL`, use `--profile`, or pass `--mcp-url`; never print the value.
- **Profile not found or wrong app**: verify `--profiles-file`, the profile name, and its `services.workdrive` entry.
- **Unknown resource ID**: resolve teams, folders, and files through lookup tools; do not guess IDs from paths or file names.
- **OAuth scope error**: reconnect the affected MCP connection with the required scope; never switch to another customer's endpoint.
- Zoho WorkDrive contains customer documents and personal data. Load only required records and never copy contents into chats, logs, or repositories.
