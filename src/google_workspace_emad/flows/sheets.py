"""
google_workspace_emad.flows.sheets — Google Sheets operations.

Ported from mads/brin/js/server.js (6 tools).
"""

import asyncio
import logging

from google_workspace_emad import brin_api_calls_total, brin_api_errors_total
from google_workspace_emad.google_client import get_sheets_service

_log = logging.getLogger("google_workspace_emad")


async def read_range(
    user_email: str,
    spreadsheet_id: str,
    range_notation: str,
) -> str:
    """Read a range of cells from a spreadsheet."""

    def _sync():
        service = get_sheets_service(user_email)
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_notation)
            .execute()
        )
        values = result.get("values", [])
        if not values:
            return "No data in range."
        lines = [f"Data from {range_notation}:"]
        for row in values:
            lines.append(" | ".join(str(c) for c in row))
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="sheets", operation="read").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="sheets", error_type=type(exc).__name__
        ).inc()
        return f"Error reading sheet: {exc}"


async def write_range(
    user_email: str,
    spreadsheet_id: str,
    range_notation: str,
    values: list[list[str]],
) -> str:
    """Write values to a range of cells."""

    def _sync():
        service = get_sheets_service(user_email)
        body = {"values": values}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        return f"Written to {range_notation}."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="sheets", operation="write").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="sheets", error_type=type(exc).__name__
        ).inc()
        return f"Error writing sheet: {exc}"


async def append_rows(
    user_email: str,
    spreadsheet_id: str,
    range_notation: str,
    values: list[list[str]],
) -> str:
    """Append rows to a sheet."""

    def _sync():
        service = get_sheets_service(user_email)
        body = {"values": values}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()
        return f"Appended {len(values)} rows to {range_notation}."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="sheets", operation="append").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="sheets", error_type=type(exc).__name__
        ).inc()
        return f"Error appending to sheet: {exc}"


async def clear_range(
    user_email: str,
    spreadsheet_id: str,
    range_notation: str,
) -> str:
    """Clear a range of cells."""

    def _sync():
        service = get_sheets_service(user_email)
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_notation,
        ).execute()
        return f"Cleared {range_notation}."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="sheets", operation="clear").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="sheets", error_type=type(exc).__name__
        ).inc()
        return f"Error clearing range: {exc}"


async def create_spreadsheet(user_email: str, title: str) -> str:
    """Create a new spreadsheet."""

    def _sync():
        service = get_sheets_service(user_email)
        body = {"properties": {"title": title}}
        ss = service.spreadsheets().create(body=body).execute()
        return f"Created spreadsheet '{title}' (id: {ss['spreadsheetId']})."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="sheets", operation="create").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="sheets", error_type=type(exc).__name__
        ).inc()
        return f"Error creating spreadsheet: {exc}"


async def get_metadata(
    user_email: str,
    spreadsheet_id: str,
) -> str:
    """Get spreadsheet metadata (sheet names, dimensions)."""

    def _sync():
        service = get_sheets_service(user_email)
        result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        title = result.get("properties", {}).get("title", "Untitled")
        sheets = result.get("sheets", [])
        lines = [f"Spreadsheet: {title}"]
        for s in sheets:
            props = s.get("properties", {})
            grid = props.get("gridProperties", {})
            lines.append(
                f"  Sheet: {props.get('title', '?')} "
                f"({grid.get('rowCount', '?')} rows x {grid.get('columnCount', '?')} cols)"
            )
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="sheets", operation="metadata").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="sheets", error_type=type(exc).__name__
        ).inc()
        return f"Error getting metadata: {exc}"
