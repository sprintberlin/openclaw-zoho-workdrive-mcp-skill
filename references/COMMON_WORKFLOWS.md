# Verified Zoho WorkDrive MCP Workflows

Step-by-step procedures for frequent WorkDrive tasks. All operations assume `mcporter` and a configured `ZOHO_WORKDRIVE_MCP_URL`. Inspect the live tool schema with `mcporter list` before the first write.

WorkDrive resource IDs are opaque strings. Never invent an ID from a path, file name, or chat message. Resolve teams, folders, and files through lookup tools first.

## 1. Find a team and inspect its folders

```text
getAllTeamsOfUser -> getTeamInfo -> listAllTeamFoldersOfaTeam -> getTeamFoldersInfo
```

1. List the user's teams with `getAllTeamsOfUser`.
2. Confirm the team with `getTeamInfo` using the team ID from that list.
3. List team folders with `listAllTeamFoldersOfaTeam` or `getAllTeamFolders`.
4. Open the chosen team folder with `getTeamFoldersInfo` or `getTeamFolderInfo`.

## 2. Browse a folder and inspect a file

```text
getTeamFolderFiles / getFolderFiles -> getFileOrFolderDetails -> breadcrumbsOfFile
```

1. List contents with `getTeamFolderFiles` (team folder) or `getFolderFiles` (regular folder).
2. For My Folders, resolve the private space with `getmyfolderid` or `getMyFolderId`, then list with `myFolderFiles` or `getFilesInMyFolders`.
3. Open the exact resource with `getFileOrFolderDetails` using its resource ID.
4. Reconstruct the path with `breadcrumbsOfFile` when the location is unclear.

## 3. Search for a file or folder

```text
searchTeamFoldersFiles / searchRecords -> getFileOrFolderDetails
```

1. Search by keyword with `searchTeamFoldersFiles`.
2. If the result set is too broad, search a specific location with `searchRecords` (My Folders, a team folder, a folder, a team, or Shared with Me).
3. Confirm the match with `getFileOrFolderDetails` before downloading, sharing, or writing.

## 4. Upload a file or a new version

```text
getFolderFiles -> uploadFile / uploadNewVersion -> getFileOrFolderDetails
```

1. Confirm the destination folder ID with `getFolderFiles` or `getFileOrFolderDetails`.
2. Upload a new file with `uploadFile`. Track a stream upload with `uploadStatus` when the server returns an upload ID.
3. For an existing file, use `uploadNewVersion` rather than creating a duplicate.
4. Read the resource back with `getFileOrFolderDetails` and `getVersion`.

Generic Zoho MCP uploads are not always reliable for binary files. If an upload fails, use the live schema from `mcporter list` and retry with the documented payload. Do not fall back to another customer's WorkDrive endpoint.

## 5. Create, rename, move, or trash a resource

```text
getFileOrFolderDetails -> createFolder / renameFileOrFolder / moveFileOrFolder / moveToTrash
```

1. Read the current resource so parent ID, name, and type are known.
2. Create a folder with `createFolder` in the confirmed parent.
3. Rename with `renameFileOrFolder`. Never reuse a name from another team or customer.
4. Move or copy with `moveFileOrFolder` / `copyFileOrFolder` using destination folder IDs from a lookup.
5. Soft-delete with `moveToTrash`. Permanent deletes and trash empties stay disabled in the shipped profiles.

## 6. Share a file internally or externally

```text
getFileOrFolderDetails -> getSharedUsers / getFileShareLinks -> createFilesFoldersShare / createExternalShareLink
```

1. Confirm the resource ID and current permissions.
2. For internal access, inspect existing collaborators with `getSharedUsers` and grant access with `createFilesFoldersShare`.
3. For an external link, inspect existing links with `getFileShareLinks` or `getSharedLinks`.
4. Create a new external link with `createExternalShareLink` (password, expiration, and download settings as required).
5. Revoke with `deleteExternalShareLink` or `deleteSharedLink` when the link is no longer needed.
6. Read the resource's share state back immediately.

## 7. Comment on a file

```text
getFileOrFolderDetails -> getComments -> createComments / updateComments
```

1. Confirm the file ID.
2. Load existing comments with `getComments`.
3. Add a comment or reply with `createComments`.
4. Resolve, edit, or reopen with `updateComments`. Delete only with `deleteComment` when authorized.

## 8. Administer a team folder (admin)

```text
getTeamInfo -> listAllTeamFoldersOfaTeam -> createTeamFolder / createTeamFolderMembers -> getTeamFolderSharedUsers
```

1. Confirm the team ID.
2. List existing team folders so a duplicate is not created.
3. Create with `createTeamFolder` or `createTeamFolderUi` depending on the live server's Action name.
4. Add members or groups with `createTeamFolderMembers`.
5. Verify with `getTeamFoldersInfo` and `getTeamFolderSharedUsers`.
