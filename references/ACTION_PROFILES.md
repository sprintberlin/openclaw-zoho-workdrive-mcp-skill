# Zoho WorkDrive MCP Action Profiles & Task Recipes

This document provides human-readable guidance on the least-privilege profiles and task recipes configured in this skill.

The machine-readable source of truth is [`references/profiles.json`](profiles.json), validated against [`references/actions.jsonl`](actions.jsonl). Use the bundled CLI `scripts/lookup_actions.py` for automated inspection, token-efficient queries, and copy-ready lists.

## The 300-Action Server Limit

A Zoho MCP server accepts at most 300 selected Actions per connection. The entire WorkDrive catalog currently contains 178 Actions, so even the full administrative profile stays well below that ceiling and fits easily onto a single MCP server:

| Profile | Actions | Fits one MCP server |
|---|---|---|
| `file-browser` | 71 | yes |
| `content-collaborator` (inherits `file-browser`) | 110 | yes |
| `workdrive-admin` (inherits `content-collaborator`) | 167 | yes |

Using the smallest matching profile still matters: fewer Actions keep the session tool catalog small, save context tokens, and enforce least privilege. When a specific job needs an Action outside your profile, add it deliberately from a task recipe instead of enabling everything.

## Role Profiles Overview

Start with the smallest role profile that covers the user or agent's responsibilities.

```bash
# List all role profiles
python3 scripts/lookup_actions.py --profiles

# Inspect actions in a profile (including inherited actions)
python3 scripts/lookup_actions.py --profile file-browser
python3 scripts/lookup_actions.py --profile content-collaborator
python3 scripts/lookup_actions.py --profile workdrive-admin

# Get copy-ready action names only (one per line)
python3 scripts/lookup_actions.py --profile file-browser --names-only
python3 scripts/lookup_actions.py --profile content-collaborator --names-only
python3 scripts/lookup_actions.py --profile workdrive-admin --names-only
```

### 1. WorkDrive File Browser (`file-browser`) - 71 Actions
- **Focus:** Safe, read-only navigation, search, and document inspection.
- **Allowed:** Browse teams, team folders, My Folders, and folder contents (`getAllTeamsOfUser`, `listAllTeamFoldersOfaTeam`, `getTeamFoldersInfo`, `getFolderFiles`, `getFileList`, `subFolders`, `getmyfolderid`, `myFolderFiles`); inspect file details, previews, statistics, and versions (`getFileOrFolderDetails`, `getFilePreview`, `getFileStatistics`, `getVersion`); search across teams and folders (`searchTeamFoldersFiles`, `searchRecords`); read comments, labels, favorites, shared links, and collaborators (`getComments`, `getLabels`, `getSharedLinks`, `getSharedUsers`, `getUserCollaborators`); ask Zia contextual questions about indexed files (`fileQuery`); download files and ZIP packages.
- **Excluded:** Every create, upload, update, share, and delete Action. An agent with this profile cannot modify any file or workspace state.

### 2. WorkDrive Content Collaborator (`content-collaborator`) - 110 Actions resolved
- **Inherits:** `file-browser` (71) and adds 39 content and collaboration Actions.
- **Focus:** Daily document work on top of full read capability.
- **Allowed:** Upload files and new versions (`uploadFile`, `uploadNewVersion`); create folders, link files, and native Zoho Writer/Sheet/Show documents (`createFolder`, `createCustomizedFolder`, `createLinkFile`, `createNewFile`, `createNativeDocument`, `importToNative`); rename, move, and copy resources (`renameFileOrFolder`, `moveFileOrFolder`, `copyFileOrFolder`, `copyMultipleFilesFolders`); move to trash and restore (`moveToTrash`, `restoreToVersion`, `updateFilesFolders`); manage comments and reviews (`createComments`, `updateComments`, `deleteComment`); organize with labels, favorites, and follow updates (`createLabel`, `updateLabels`, `addResourceLabels`, `removeResourceLabels`, `updateMultipleFollowUpdates`); manage internal and external shares (`createExternalShareLink`, `createExternalShare`, `updateExternalShare`, `deleteExternalShareLink`, `deleteSharedLink`, `createFilesFoldersShare`, `updateFilesFoldersShare`, `deletePermission`); generate AI summaries (`generateFileSummary`).
- **Excluded:** Team folder creation, team settings, user invitations, group management, data templates, template libraries, and workflows.

### 3. WorkDrive Administrator (`workdrive-admin`) - 167 Actions resolved
- **Inherits:** `content-collaborator` (110) and adds 57 administrative Actions.
- **Focus:** Full WorkDrive workspace and collaboration administration.
- **Allowed:** Everything in `content-collaborator` plus team folders and their member/group access (`createTeamFolder`, `updateTeamFolder`, `updateTeamFolderName`, `createTeamFolderMembers`, `updateTeamFolderMember`); team and folder settings (`getTeamSetting`, `updateSettings`, `allowUserDocumentConversion`); invite team members, manage groups and roles (`inviteNewUsers`, `createGroup`, `updateGroups`, `addMemberInGroup`, `updateMemberRole`); create and apply data templates and custom fields (`createDataTemplate`, `updateDatatemplates`, `createCustomField`, `updateCustomField`, `createMultipleCustommetadata`, `updateValuesOfAssociatedFilesFolders`, `disassociateFilesFoldersFromDataTemplate`); administer template libraries and categories (`fetchTeamLibraries`, `createTemplateCategory`, `updateTemplateCategory`, `updateCategory`, `removeTemplateCategory`, `saveResourceAsTemplate`, `updateOrgTemplateAdminRole`); manage external file-request collections (`createCollections`, `updateCollections`, `getListOfAllCollectionLinks`, `getListOfAllCollectionSubmissions`, `getListOfAllTheSubmittedFiles`); supervise and advance workflows (`startWorkflowForAFileFolder`, `getWorkflowInstance`, `performTransitionForAWorkflowInstance`, `abortWorkflowForAFileFolder`).
- **Explicitly Denied (Safety):** Permanent deletes (`deleteCollection`, `deleteCustomField`, `deleteDataTemplate`, `deleteGroup`, `deleteMember`, `deleteTeamfolder`, `deleteTeamFolderMember`, `deleteVersion`), trash purges (`emptyMyFolderTrash`, `emptyTrash`), and team member deletion (`updateUsers`).

## Task Recipes Overview

Task recipes answer the question: *"Which specific Actions do I need to unlock on the MCP server to solve this exact job?"*

```bash
# List all configured task recipes
python3 scripts/lookup_actions.py --tasks

# Inspect a specific task recipe
python3 scripts/lookup_actions.py --task file-and-folder-browsing

# Copy-ready action names for Zoho MCP setup UI
python3 scripts/lookup_actions.py --task file-and-folder-browsing --names-only
```

Available recipes:
- `file-and-folder-browsing`: Browse teams, team folders, My Folders, and folder contents.
- `file-search`: Find files and folders across teams, team folders, and shared locations.
- `file-upload-and-versioning`: Upload files, add new versions, and restore an earlier version.
- `folder-structure-management`: Create, rename, move, copy, and trash folders and files.
- `external-sharing`: Create, inspect, update, and revoke external share links.
- `internal-sharing-and-permissions`: Share with team members and groups and manage their access.
- `comments-and-review`: Read, add, resolve, and remove comments on a file.
- `labels-and-favorites`: Organize resources with labels, favorites, and follow updates.
- `trash-and-restore`: Review trashed items and restore them without permanent deletion.
- `team-folder-administration`: Create team folders, manage their members, and change their settings.
- `team-user-and-group-administration`: Invite team members and maintain groups and group roles.
- `data-templates-and-metadata`: Define data templates and custom metadata and apply them to resources.
- `template-library-management`: Maintain template libraries, categories, and saved template files.
- `workflow-operations`: Start, track, advance, and abort WorkDrive workflows on a resource.
- `file-intelligence`: Summarize file content and ask Zia questions about an indexed file.
- `bulk-download-and-zip`: Package multiple resources as ZIP and track download or extraction progress.
- `change-tracking`: Track recent changes in a WorkDrive account using change tokens.
- `file-request-collections`: Run external file-request collections and read submitted files.

## Format and Philosophy

See [`references/CATALOG_FORMAT.md`](CATALOG_FORMAT.md) for full documentation on why and how the catalog format is standardized on JSONL + JSON across the SprintCX Zoho MCP skills.
