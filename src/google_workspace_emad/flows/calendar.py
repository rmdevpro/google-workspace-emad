"""
google_workspace_emad.flows.calendar — Google Calendar operations.

Ported from mads/brin/js/server.js (5 tools).
"""

import asyncio
import logging

from google_workspace_emad import brin_api_calls_total, brin_api_errors_total
from google_workspace_emad.google_client import get_calendar_service

_log = logging.getLogger("google_workspace_emad")


async def list_events(
    user_email: str,
    days_ahead: int = 7,
    limit: int = 20,
) -> str:
    """List upcoming calendar events."""

    def _sync():
        from datetime import datetime, timedelta, timezone

        service = get_calendar_service(user_email)
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        if not events:
            return f"No events in the next {days_ahead} days."

        lines = [f"Events ({len(events)}):"]
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "(no title)")
            lines.append(f"- **{summary}** at {start}")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="calendar", operation="list_events").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="calendar", error_type=type(exc).__name__
        ).inc()
        return f"Error listing events: {exc}"


async def create_event(
    user_email: str,
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    attendees: list[str] | None = None,
) -> str:
    """Create a calendar event."""

    def _sync():
        service = get_calendar_service(user_email)
        event = {
            "summary": summary,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
        }
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]

        result = service.events().insert(calendarId="primary", body=event).execute()
        return f"Created event '{summary}' (id: {result['id']})."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="calendar", operation="create").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="calendar", error_type=type(exc).__name__
        ).inc()
        return f"Error creating event: {exc}"


async def update_event(
    user_email: str,
    event_id: str,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> str:
    """Update a calendar event."""

    def _sync():
        service = get_calendar_service(user_email)
        body = {}
        if summary:
            body["summary"] = summary
        if start:
            body["start"] = {"dateTime": start, "timeZone": "UTC"}
        if end:
            body["end"] = {"dateTime": end, "timeZone": "UTC"}
        if description:
            body["description"] = description
        if location:
            body["location"] = location

        service.events().patch(
            calendarId="primary", eventId=event_id, body=body
        ).execute()
        return f"Updated event {event_id}."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="calendar", operation="update").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="calendar", error_type=type(exc).__name__
        ).inc()
        return f"Error updating event: {exc}"


async def get_event(user_email: str, event_id: str) -> str:
    """Get details of a specific calendar event."""

    def _sync():
        service = get_calendar_service(user_email)
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        return (
            f"**{event.get('summary', '(no title)')}**\n"
            f"  Start: {start}\n"
            f"  End: {end}\n"
            f"  Location: {event.get('location', 'N/A')}\n"
            f"  Description: {event.get('description', 'N/A')}"
        )

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="calendar", operation="get").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="calendar", error_type=type(exc).__name__
        ).inc()
        return f"Error getting event: {exc}"


async def list_calendars(user_email: str) -> str:
    """List available calendars."""

    def _sync():
        service = get_calendar_service(user_email)
        results = service.calendarList().list().execute()
        calendars = results.get("items", [])
        if not calendars:
            return "No calendars found."
        lines = [f"Calendars ({len(calendars)}):"]
        for cal in calendars:
            lines.append(f"  {cal.get('summary', '?')} (id: {cal['id']})")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(
            service="calendar", operation="list_calendars"
        ).inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="calendar", error_type=type(exc).__name__
        ).inc()
        return f"Error listing calendars: {exc}"


async def delete_event(user_email: str, event_id: str) -> str:
    """Delete a calendar event."""

    def _sync():
        service = get_calendar_service(user_email)
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"Deleted event {event_id}."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="calendar", operation="delete").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="calendar", error_type=type(exc).__name__
        ).inc()
        return f"Error deleting event: {exc}"
