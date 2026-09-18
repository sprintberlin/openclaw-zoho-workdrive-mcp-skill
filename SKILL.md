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
- For binary file uploads: [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge). MCP cannot upload bytes. See [Binary file uploads](#binary-file-uploads).

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
7. For anything that moves file bytes, use the attachment bridge instead of an MCP upload Action.

## Binary file uploads

Zoho MCP cannot upload binary files. `uploadFile` and `uploadNewVersion` declare a `format: "binary"` parameter, but the Zoho MCP server never builds a `multipart/form-data` request, so the bytes are dropped. The call usually still reports success, which makes a trusting agent claim a file was uploaded while the folder stays empty.

**Treat an empty attachment or file array as a failure, never a success.** Never claim an upload succeeded without reading the resource back.

The companion skill [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge) exists for exactly this gap. It performs real `multipart/form-data` uploads against the Zoho REST API with Self Client OAuth and verifies every upload by SHA-256 read-back.

Division of labour:

| Task | Use |
|---|---|
| Browse, search, inspect, share, comment, manage folders | this skill (MCP) |
| Resolve the destination folder or file ID before an upload | this skill (MCP) |
| Transfer file bytes into WorkDrive | zoho-attachment-bridge |
| Confirm the uploaded file is really there | zoho-attachment-bridge read-back, then re-list with `getFolderFiles` |

Status: the bridge ships a WorkDrive adapter since release 0.4.0 ([issue #9](https://github.com/sprintberlin/zoho-attachment-bridge/issues/9)). Resolve the destination folder ID here, then hand the bytes over:

```bash
# New file in a folder
python3 scripts/zoho_attach.py --app workdrive --target file-upload --id <folder_id> --file <path>

# New version over an existing file of the same name
python3 scripts/zoho_attach.py --app workdrive --target new-version --id <folder_id> --filename <existing_name> --file <path>
```

The bridge uploads via `POST /workdrive/api/v1/upload` (multipart field `content`, max 250 MB) and verifies every upload by downloading the file again from the dedicated download host and comparing SHA-256. It exits non-zero unless the bytes are provably there. Its Self Client needs `WorkDrive.files.CREATE,WorkDrive.files.READ`; a Books- or CRM-only token fails with `F7007 Invalid OAuth scope`.

After an upload, re-list the folder here with `getFolderFiles` to confirm the result in the tree the user sees.

`createNewFile`, `createNativeDocument`, and `importToNative` create or convert Zoho-native documents server-side and do not transfer local bytes, so they are unaffected by this limitation.

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

Every helper accepts `--mcp-url`, `--profile`, `--profiles-file`, `--json`, and `--timeout`. List helpers add `--limit`, `--page-size`, and `--full`. Run any helper with `--help` for its exact options, without configuring credentials. Unknown or incomplete options exit with status 2.

No helper uploads files. Uploads belong to the attachment bridge.

## Role profiles and the 300-Action limit

A Zoho MCP server accepts at most 300 selected Actions per connection. The entire WorkDrive catalog currently has 178 Actions, so every profile fits on one MCP server. Use the smallest matching profile anyway so the session tool catalog stays small.

| Profile | Actions | Fits one MCP server |
|---|---|---|
| `file-browser` | 71 | yes |
| `content-collaborator` (inherits `file-browser`) | 110 | yes |
| `workdrive-admin` (inherits `content-collaborator`) | 167 | yes |

- **`file-browser`** (71): Read-only navigation, inspection, search, and downloads. No create, update, share, or delete Actions.
- **`content-collaborator`** (110 resolved): Inherits `file-browser` and adds folder and native document creation, rename/move/copy, trash and restore, comments, labels, favorites, and internal or external sharing.
- **`workdrive-admin`** (167 resolved): Inherits `content-collaborator` and adds team folder, team user, group, data template, template library, collection, and workflow administration. Denies permanent deletes, trash purges, and team-member removal.

If a task needs an Action outside a profile, add it deliberately from a task recipe rather than enabling a whole module. The upload Actions are included in the collaborator profile for completeness, but they do not transfer bytes; see [Binary file uploads](#binary-file-uploads).

## References

- [Action catalog](references/actions.jsonl): every known WorkDrive Action with its Zoho description, one JSON object per line
- [Profiles and task recipes](references/profiles.json): role profiles and per-task Action sets
- [Catalog format](references/CATALOG_FORMAT.md): why the catalog is JSON, the record shape, and how to refresh it
- [Action profiles overview](references/ACTION_PROFILES.md): human-readable summary of the configured profiles and tasks
- [Common workflows](references/COMMON_WORKFLOWS.md): verified step-by-step procedures for frequent WorkDrive tasks
- [Multi-account profiles](references/MULTI_ACCOUNT.md): portable endpoint selection for one or many Zoho accounts
- [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge): companion skill for verified binary uploads that MCP cannot perform

Query the catalog with `scripts/lookup_actions.py` instead of loading `actions.jsonl` into context. Load workflows when executing a covered task.

## Troubleshooting and safety

- **No endpoint configured**: set `ZOHO_WORKDRIVE_MCP_URL`, use `--profile`, or pass `--mcp-url`; never print the value.
- **Profile not found or wrong app**: verify `--profiles-file`, the profile name, and its `services.workdrive` entry.
- **Unknown resource ID**: resolve teams, folders, and files through lookup tools; do not guess IDs from paths or file names.
- **Upload reported success but the file is missing**: expected. MCP does not transfer bytes; use [zoho-attachment-bridge](https://github.com/sprintberlin/zoho-attachment-bridge) and verify by re-listing the folder.
- **OAuth scope error**: reconnect the affected MCP connection with the required scope; never switch to another customer's endpoint.
- Zoho WorkDrive contains customer documents and personal data. Load only required records and never copy contents into chats, logs, or repositories.
