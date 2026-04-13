"""
google_workspace_emad.flows.imperator — Brin Imperator StateGraph.

CB-style ReAct agent for Google Workspace service brokering.
"""

import logging
from pathlib import Path
from typing import Annotated, TypedDict

import httpx
import openai
from langchain_core.messages import AIMessage, AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

_log = logging.getLogger("google_workspace_emad")

_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "imperator_identity.md"
)
_MAX_ITERATIONS = 15


class BrinImperatorState(TypedDict):
    payload: dict  # Full OpenAI request body
    messages: Annotated[list[AnyMessage], add_messages]
    conversation_id: str | None
    response_text: str | None
    error: str | None
    iteration_count: int


# ── Tools — Gmail ────────────────────────────────────────────────────────


@tool
async def gmail_read(user_email: str, query: str = "is:unread", limit: int = 20) -> str:
    """Read Gmail messages matching a search query.

    Args:
        user_email: Google Workspace email (e.g., jerry@rmdev.pro).
        query: Gmail search query (default: is:unread).
        limit: Max messages to return.
    """
    from google_workspace_emad.flows.gmail import read_messages

    return await read_messages(user_email, query, limit)


@tool
async def gmail_send(
    user_email: str,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    attachment_path: str = "",
) -> str:
    """Send a Gmail message.

    Args:
        user_email: Sender (Google Workspace email).
        to: Recipient email.
        subject: Subject line.
        body: Message body.
        cc: CC recipient (optional).
        attachment_path: File path to attach (optional).
    """
    from google_workspace_emad.flows.gmail import send_message

    return await send_message(
        user_email, to, subject, body, cc or None, attachment_path or None
    )


@tool
async def gmail_search(user_email: str, query: str, limit: int = 10) -> str:
    """Search Gmail messages.

    Args:
        user_email: Google Workspace email.
        query: Search text.
        limit: Max results.
    """
    from google_workspace_emad.flows.gmail import search_messages

    return await search_messages(user_email, query, limit)


# ── Tools — Drive ────────────────────────────────────────────────────────


@tool
async def drive_list(user_email: str, folder_id: str = "root", limit: int = 50) -> str:
    """List files in a Drive folder.

    Args:
        user_email: Google Workspace email.
        folder_id: Folder ID (default: root).
        limit: Max items.
    """
    from google_workspace_emad.flows.drive import list_files

    return await list_files(user_email, folder_id, limit)


@tool
async def drive_search(user_email: str, query: str, limit: int = 20) -> str:
    """Search Drive files by name.

    Args:
        user_email: Google Workspace email.
        query: Search text.
        limit: Max results.
    """
    from google_workspace_emad.flows.drive import search_files

    return await search_files(user_email, query, limit)


@tool
async def drive_create_folder(
    user_email: str, name: str, parent_id: str = "root"
) -> str:
    """Create a folder in Drive.

    Args:
        user_email: Google Workspace email.
        name: Folder name.
        parent_id: Parent folder ID (default: root).
    """
    from google_workspace_emad.flows.drive import create_folder

    return await create_folder(user_email, name, parent_id)


@tool
async def drive_delete(user_email: str, file_id: str) -> str:
    """Delete a file or folder from Drive.

    Args:
        user_email: Google Workspace email.
        file_id: File/folder ID to delete.
    """
    from google_workspace_emad.flows.drive import delete_file

    return await delete_file(user_email, file_id)


@tool
async def drive_share(
    user_email: str, file_id: str, share_with: str, role: str = "reader"
) -> str:
    """Share a Drive file with another user.

    Args:
        user_email: File owner.
        file_id: File ID.
        share_with: Email to share with.
        role: Permission role (reader, writer, commenter).
    """
    from google_workspace_emad.flows.drive import share_file

    return await share_file(user_email, file_id, share_with, role)


# ── Tools — Sheets ───────────────────────────────────────────────────────


@tool
async def sheets_read(user_email: str, spreadsheet_id: str, range_notation: str) -> str:
    """Read cells from a Google Sheet.

    Args:
        user_email: Google Workspace email.
        spreadsheet_id: Spreadsheet ID.
        range_notation: A1 notation (e.g., Sheet1!A1:C10).
    """
    from google_workspace_emad.flows.sheets import read_range

    return await read_range(user_email, spreadsheet_id, range_notation)


@tool
async def sheets_write(
    user_email: str,
    spreadsheet_id: str,
    range_notation: str,
    values: str,
) -> str:
    """Write values to a Google Sheet.

    Args:
        user_email: Google Workspace email.
        spreadsheet_id: Spreadsheet ID.
        range_notation: A1 notation.
        values: JSON array of arrays (e.g., '[["A", "B"], ["1", "2"]]').
    """
    import json

    from google_workspace_emad.flows.sheets import write_range

    parsed = json.loads(values)
    return await write_range(user_email, spreadsheet_id, range_notation, parsed)


@tool
async def sheets_append(
    user_email: str,
    spreadsheet_id: str,
    range_notation: str,
    values: str,
) -> str:
    """Append rows to a Google Sheet.

    Args:
        user_email: Google Workspace email.
        spreadsheet_id: Spreadsheet ID.
        range_notation: A1 notation.
        values: JSON array of arrays.
    """
    import json

    from google_workspace_emad.flows.sheets import append_rows

    parsed = json.loads(values)
    return await append_rows(user_email, spreadsheet_id, range_notation, parsed)


@tool
async def sheets_metadata(user_email: str, spreadsheet_id: str) -> str:
    """Get spreadsheet metadata (sheet names, dimensions).

    Args:
        user_email: Google Workspace email.
        spreadsheet_id: Spreadsheet ID.
    """
    from google_workspace_emad.flows.sheets import get_metadata

    return await get_metadata(user_email, spreadsheet_id)


# ── Tools — Docs ─────────────────────────────────────────────────────────


@tool
async def docs_read(user_email: str, document_id: str) -> str:
    """Read a Google Doc as plain text.

    Args:
        user_email: Google Workspace email.
        document_id: Document ID.
    """
    from google_workspace_emad.flows.docs import read_document

    return await read_document(user_email, document_id)


@tool
async def docs_create(user_email: str, title: str, body: str = "") -> str:
    """Create a new Google Doc.

    Args:
        user_email: Google Workspace email.
        title: Document title.
        body: Initial content (optional).
    """
    from google_workspace_emad.flows.docs import create_document

    return await create_document(user_email, title, body)


# ── Tools — Calendar ─────────────────────────────────────────────────────


@tool
async def calendar_list_events(
    user_email: str, days_ahead: int = 7, limit: int = 20
) -> str:
    """List upcoming calendar events.

    Args:
        user_email: Google Workspace email.
        days_ahead: How many days ahead.
        limit: Max events.
    """
    from google_workspace_emad.flows.calendar import list_events

    return await list_events(user_email, days_ahead, limit)


@tool
async def calendar_create_event(
    user_email: str,
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    attendees: str = "",
) -> str:
    """Create a calendar event.

    Args:
        user_email: Google Workspace email.
        summary: Event title.
        start: Start time (ISO format).
        end: End time (ISO format).
        description: Event description (optional).
        location: Location (optional).
        attendees: Comma-separated emails (optional).
    """
    from google_workspace_emad.flows.calendar import create_event

    attendee_list = (
        [a.strip() for a in attendees.split(",") if a.strip()] if attendees else None
    )
    return await create_event(
        user_email, summary, start, end, description, location, attendee_list
    )


# ── Tools — Drive (remaining) ────────────────────────────────────────────


@tool
async def drive_get(user_email: str, file_id: str) -> str:
    """Get file metadata from Drive.

    Args:
        user_email: Google Workspace email.
        file_id: File ID.
    """
    from google_workspace_emad.flows.drive import get_file

    return await get_file(user_email, file_id)


@tool
async def drive_move(user_email: str, file_id: str, new_parent_id: str) -> str:
    """Move a file to a different folder.

    Args:
        user_email: Google Workspace email.
        file_id: File ID.
        new_parent_id: Destination folder ID.
    """
    from google_workspace_emad.flows.drive import move_file

    return await move_file(user_email, file_id, new_parent_id)


@tool
async def drive_copy(user_email: str, file_id: str, new_name: str = "") -> str:
    """Copy a file.

    Args:
        user_email: Google Workspace email.
        file_id: File ID.
        new_name: Name for the copy (optional).
    """
    from google_workspace_emad.flows.drive import copy_file

    return await copy_file(user_email, file_id, new_name)


@tool
async def drive_rename(user_email: str, file_id: str, new_name: str) -> str:
    """Rename a file.

    Args:
        user_email: Google Workspace email.
        file_id: File ID.
        new_name: New name.
    """
    from google_workspace_emad.flows.drive import rename_file

    return await rename_file(user_email, file_id, new_name)


@tool
async def drive_list_shared_drives(user_email: str, limit: int = 20) -> str:
    """List shared drives.

    Args:
        user_email: Google Workspace email.
        limit: Max results.
    """
    from google_workspace_emad.flows.drive import list_shared_drives

    return await list_shared_drives(user_email, limit)


@tool
async def drive_list_permissions(user_email: str, file_id: str) -> str:
    """List permissions on a file.

    Args:
        user_email: Google Workspace email.
        file_id: File ID.
    """
    from google_workspace_emad.flows.drive import list_permissions

    return await list_permissions(user_email, file_id)


@tool
async def drive_remove_permission(
    user_email: str, file_id: str, permission_id: str
) -> str:
    """Remove a permission from a file.

    Args:
        user_email: Google Workspace email.
        file_id: File ID.
        permission_id: Permission ID to remove.
    """
    from google_workspace_emad.flows.drive import remove_permission

    return await remove_permission(user_email, file_id, permission_id)


# ── Tools — Docs (remaining) ────────────────────────────────────────────


@tool
async def docs_write(user_email: str, document_id: str, content: str) -> str:
    """Write/append content to a Google Doc.

    Args:
        user_email: Google Workspace email.
        document_id: Document ID.
        content: Text to append.
    """
    from google_workspace_emad.flows.docs import write_document

    return await write_document(user_email, document_id, content)


# ── Tools — Sheets (remaining) ──────────────────────────────────────────


@tool
async def sheets_clear(
    user_email: str, spreadsheet_id: str, range_notation: str
) -> str:
    """Clear a range of cells in a Google Sheet.

    Args:
        user_email: Google Workspace email.
        spreadsheet_id: Spreadsheet ID.
        range_notation: A1 notation.
    """
    from google_workspace_emad.flows.sheets import clear_range

    return await clear_range(user_email, spreadsheet_id, range_notation)


@tool
async def sheets_create(user_email: str, title: str) -> str:
    """Create a new Google Spreadsheet.

    Args:
        user_email: Google Workspace email.
        title: Spreadsheet title.
    """
    from google_workspace_emad.flows.sheets import create_spreadsheet

    return await create_spreadsheet(user_email, title)


# ── Tools — Slides ──────────────────────────────────────────────────────


@tool
async def slides_get(user_email: str, presentation_id: str) -> str:
    """Get a Google Slides presentation.

    Args:
        user_email: Google Workspace email.
        presentation_id: Presentation ID.
    """
    from google_workspace_emad.flows.slides import get_presentation

    return await get_presentation(user_email, presentation_id)


@tool
async def slides_create(user_email: str, title: str) -> str:
    """Create a new Google Slides presentation.

    Args:
        user_email: Google Workspace email.
        title: Presentation title.
    """
    from google_workspace_emad.flows.slides import create_presentation

    return await create_presentation(user_email, title)


# ── Tools — Calendar (remaining) ────────────────────────────────────────


@tool
async def calendar_update_event(
    user_email: str,
    event_id: str,
    summary: str = "",
    start: str = "",
    end: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """Update a calendar event.

    Args:
        user_email: Google Workspace email.
        event_id: Event ID.
        summary: New title (optional).
        start: New start (ISO, optional).
        end: New end (ISO, optional).
        description: New description (optional).
        location: New location (optional).
    """
    from google_workspace_emad.flows.calendar import update_event

    return await update_event(
        user_email,
        event_id,
        summary or None,
        start or None,
        end or None,
        description or None,
        location or None,
    )


@tool
async def calendar_get_event(user_email: str, event_id: str) -> str:
    """Get details of a calendar event.

    Args:
        user_email: Google Workspace email.
        event_id: Event ID.
    """
    from google_workspace_emad.flows.calendar import get_event

    return await get_event(user_email, event_id)


@tool
async def calendar_list_calendars(user_email: str) -> str:
    """List available calendars.

    Args:
        user_email: Google Workspace email.
    """
    from google_workspace_emad.flows.calendar import list_calendars

    return await list_calendars(user_email)


@tool
async def calendar_delete_event(user_email: str, event_id: str) -> str:
    """Delete a calendar event.

    Args:
        user_email: Google Workspace email.
        event_id: Event ID.
    """
    from google_workspace_emad.flows.calendar import delete_event

    return await delete_event(user_email, event_id)


_TOOLS = [
    # Gmail (3)
    gmail_read,
    gmail_send,
    gmail_search,
    # Drive (12)
    drive_list,
    drive_search,
    drive_get,
    drive_create_folder,
    drive_delete,
    drive_move,
    drive_copy,
    drive_rename,
    drive_share,
    drive_list_shared_drives,
    drive_list_permissions,
    drive_remove_permission,
    # Docs (3)
    docs_read,
    docs_write,
    docs_create,
    # Sheets (6)
    sheets_read,
    sheets_write,
    sheets_append,
    sheets_clear,
    sheets_create,
    sheets_metadata,
    # Slides (2)
    slides_get,
    slides_create,
    # Calendar (6)
    calendar_list_calendars,
    calendar_list_events,
    calendar_get_event,
    calendar_create_event,
    calendar_update_event,
    calendar_delete_event,
]


# ── System prompt ────────────────────────────────────────────────────────


def _load_system_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    return "You are Brin, the Google Workspace service broker."


# ── Graph nodes ──────────────────────────────────────────────────────────


async def init_node(state: BrinImperatorState) -> dict:
    """Parse payload, set up conversation. Append-only on resumed turns."""
    import uuid
    from langchain_core.messages import HumanMessage

    payload = state.get("payload", {})
    existing_messages = state.get("messages", [])

    conv_id = payload.get("conversation_id")
    if conv_id == "new":
        conv_id = str(uuid.uuid4())
    elif not conv_id:
        conv_id = f"default-{payload.get('model', 'brin')}"

    # Extract last user message
    raw_messages = payload.get("messages", [])
    new_user_msg = None
    for m in reversed(raw_messages):
        if m.get("role") == "user":
            new_user_msg = HumanMessage(content=m.get("content", ""))
            break
    if not new_user_msg:
        new_user_msg = HumanMessage(content="")

    # Resumed conversation
    if existing_messages:
        return {"messages": [new_user_msg], "conversation_id": conv_id, "iteration_count": 0}

    # First turn
    system_content = _load_system_prompt()
    messages = [SystemMessage(content=system_content), new_user_msg]
    return {"messages": messages, "conversation_id": conv_id, "iteration_count": 0}


async def agent_node(state: BrinImperatorState) -> dict:
    from google_workspace_emad.inference import get_llm

    llm = get_llm("fast")
    llm_with_tools = llm.bind_tools(_TOOLS)

    messages = list(state["messages"])

    max_messages = 30
    if len(messages) > max_messages:
        cut_index = len(messages) - (max_messages - 1)
        while cut_index < len(messages) and isinstance(
            messages[cut_index], ToolMessage
        ):
            cut_index += 1
        messages = [messages[0]] + messages[cut_index:]

    try:
        response = await llm_with_tools.ainvoke(messages)
    except (openai.APIError, httpx.HTTPError, ValueError, RuntimeError) as exc:
        _log.error("Brin LLM call failed: %s", exc, exc_info=True)
        return {
            "messages": [
                AIMessage(content="I encountered an error processing your request.")
            ],
            "error": str(exc),
        }

    return {
        "messages": [response],
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def should_continue(state: BrinImperatorState) -> str:
    if state.get("error"):
        return "finalize"
    messages = state["messages"]
    if not messages:
        return "finalize"
    last = messages[-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        if state.get("iteration_count", 0) >= _MAX_ITERATIONS:
            return "finalize"
        return "tool_node"
    return "finalize"


def finalize(state: BrinImperatorState) -> dict:
    for msg in reversed(state["messages"]):
        if (
            isinstance(msg, AIMessage)
            and msg.content
            and not getattr(msg, "tool_calls", None)
        ):
            return {
                "response_text": str(msg.content),
                "conversation_id": state.get("conversation_id"),
            }
    return {
        "response_text": "[No response generated]",
        "conversation_id": state.get("conversation_id"),
    }


# ── Graph builder ────────────────────────────────────────────────────────


def build_imperator_graph(params: dict | None = None) -> StateGraph:
    tool_node_instance = ToolNode(_TOOLS)

    workflow = StateGraph(BrinImperatorState)
    workflow.add_node("init_node", init_node)
    workflow.add_node("agent_node", agent_node)
    workflow.add_node("tool_node", tool_node_instance)
    workflow.add_node("finalize", finalize)

    workflow.set_entry_point("init_node")
    workflow.add_edge("init_node", "agent_node")
    workflow.add_conditional_edges(
        "agent_node",
        should_continue,
        {"tool_node": "tool_node", "finalize": "finalize"},
    )
    workflow.add_edge("tool_node", "agent_node")
    workflow.add_edge("finalize", END)

    from app.checkpointer import get_checkpointer

    return workflow.compile(checkpointer=get_checkpointer())
