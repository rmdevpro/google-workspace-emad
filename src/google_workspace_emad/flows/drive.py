"""
google_workspace_emad.flows.drive — Google Drive operations.

Ported from mads/brin/js/server.js (12 tools).
"""

import asyncio
import logging

from google_workspace_emad import gws_api_calls_total, gws_api_errors_total
from google_workspace_emad.google_client import get_drive_service

_log = logging.getLogger("google_workspace_emad")


async def list_files(
    user_email: str,
    folder_id: str = "root",
    limit: int = 50,
) -> str:
    """List files in a Drive folder."""

    def _sync():
        service = get_drive_service(user_email)
        query = f"'{folder_id}' in parents and trashed = false"
        results = (
            service.files()
            .list(
                q=query,
                pageSize=limit,
                fields="files(id, name, mimeType, size, modifiedTime)",
            )
            .execute()
        )
        files = results.get("files", [])
        if not files:
            return "No files found."
        lines = [f"Files ({len(files)}):"]
        for f in files:
            icon = (
                "[dir]"
                if f["mimeType"] == "application/vnd.google-apps.folder"
                else "[file]"
            )
            lines.append(f"  {icon} {f['name']} (id: {f['id']})")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="list").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error listing Drive files: {exc}"


async def search_files(
    user_email: str,
    query: str,
    limit: int = 20,
) -> str:
    """Search Drive files by name or content."""

    def _sync():
        service = get_drive_service(user_email)
        results = (
            service.files()
            .list(
                q=f"name contains '{query}' and trashed = false",
                pageSize=limit,
                fields="files(id, name, mimeType)",
            )
            .execute()
        )
        files = results.get("files", [])
        if not files:
            return f"No files matching '{query}'."
        lines = [f"Search results ({len(files)}):"]
        for f in files:
            lines.append(f"  {f['name']} (id: {f['id']})")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="search").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error searching Drive: {exc}"


async def create_folder(
    user_email: str,
    name: str,
    parent_id: str = "root",
) -> str:
    """Create a folder in Drive."""

    def _sync():
        service = get_drive_service(user_email)
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = service.files().create(body=metadata, fields="id, name").execute()
        return f"Created folder '{folder['name']}' (id: {folder['id']})."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="create_folder").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error creating folder: {exc}"


async def delete_file(user_email: str, file_id: str) -> str:
    """Delete a file or folder from Drive."""

    def _sync():
        service = get_drive_service(user_email)
        service.files().delete(fileId=file_id).execute()
        return f"Deleted file {file_id}."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="delete").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error deleting file: {exc}"


async def get_file(user_email: str, file_id: str) -> str:
    """Get file metadata."""

    def _sync():
        service = get_drive_service(user_email)
        f = (
            service.files()
            .get(
                fileId=file_id, fields="id, name, mimeType, size, modifiedTime, parents"
            )
            .execute()
        )
        return (
            f"**{f['name']}**\n"
            f"  ID: {f['id']}\n"
            f"  Type: {f['mimeType']}\n"
            f"  Size: {f.get('size', 'N/A')} bytes\n"
            f"  Modified: {f.get('modifiedTime', '?')}"
        )

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="get").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error getting file: {exc}"


async def move_file(user_email: str, file_id: str, new_parent_id: str) -> str:
    """Move a file to a different folder."""

    def _sync():
        service = get_drive_service(user_email)
        f = service.files().get(fileId=file_id, fields="parents").execute()
        old_parents = ",".join(f.get("parents", []))
        service.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=old_parents,
            fields="id, name",
        ).execute()
        return f"Moved file {file_id} to folder {new_parent_id}."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="move").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error moving file: {exc}"


async def copy_file(user_email: str, file_id: str, new_name: str = "") -> str:
    """Copy a file."""

    def _sync():
        service = get_drive_service(user_email)
        body = {}
        if new_name:
            body["name"] = new_name
        copy = (
            service.files().copy(fileId=file_id, body=body, fields="id, name").execute()
        )
        return f"Copied to '{copy['name']}' (id: {copy['id']})."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="copy").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error copying file: {exc}"


async def rename_file(user_email: str, file_id: str, new_name: str) -> str:
    """Rename a file."""

    def _sync():
        service = get_drive_service(user_email)
        service.files().update(
            fileId=file_id, body={"name": new_name}, fields="id, name"
        ).execute()
        return f"Renamed file {file_id} to '{new_name}'."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="rename").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error renaming file: {exc}"


async def list_shared_drives(user_email: str, limit: int = 20) -> str:
    """List shared drives."""

    def _sync():
        service = get_drive_service(user_email)
        results = service.drives().list(pageSize=limit).execute()
        drives = results.get("drives", [])
        if not drives:
            return "No shared drives found."
        lines = [f"Shared drives ({len(drives)}):"]
        for d in drives:
            lines.append(f"  {d['name']} (id: {d['id']})")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(
            service="drive", operation="list_shared_drives"
        ).inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error listing shared drives: {exc}"


async def list_permissions(user_email: str, file_id: str) -> str:
    """List permissions on a file."""

    def _sync():
        service = get_drive_service(user_email)
        results = (
            service.permissions()
            .list(fileId=file_id, fields="permissions(id, emailAddress, role, type)")
            .execute()
        )
        perms = results.get("permissions", [])
        if not perms:
            return "No permissions found."
        lines = [f"Permissions on {file_id}:"]
        for p in perms:
            lines.append(f"  {p.get('emailAddress', p['type'])} — {p['role']}")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="list_permissions").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error listing permissions: {exc}"


async def remove_permission(user_email: str, file_id: str, permission_id: str) -> str:
    """Remove a permission from a file."""

    def _sync():
        service = get_drive_service(user_email)
        service.permissions().delete(
            fileId=file_id, permissionId=permission_id
        ).execute()
        return f"Removed permission {permission_id} from file {file_id}."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(
            service="drive", operation="remove_permission"
        ).inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error removing permission: {exc}"


async def share_file(
    user_email: str,
    file_id: str,
    share_with: str,
    role: str = "reader",
) -> str:
    """Share a file with another user."""

    def _sync():
        service = get_drive_service(user_email)
        permission = {"type": "user", "role": role, "emailAddress": share_with}
        service.permissions().create(fileId=file_id, body=permission).execute()
        return f"Shared file {file_id} with {share_with} as {role}."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="drive", operation="share").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="drive", error_type=type(exc).__name__
        ).inc()
        return f"Error sharing file: {exc}"
