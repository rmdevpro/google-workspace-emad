"""
google_workspace_emad.flows.gmail — Gmail operations via Google API.

NEW — not in the original Brin pMAD.
Uses service account with domain-wide delegation (no OAuth dance).
"""

import asyncio
import base64
import logging
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google_workspace_emad import gws_api_calls_total, gws_api_errors_total
from google_workspace_emad.google_client import get_gmail_service

_log = logging.getLogger("google_workspace_emad")


async def read_messages(
    user_email: str,
    query: str = "is:unread",
    limit: int = 20,
) -> str:
    """Read Gmail messages matching a query."""

    def _read_sync():
        service = get_gmail_service(user_email)
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=limit)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            return f"No messages matching '{query}'."

        lines = [f"Found {len(messages)} message(s):"]
        for msg_ref in messages:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_ref["id"], format="metadata")
                .execute()
            )
            headers = {
                h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])
            }
            subject = headers.get("Subject", "(no subject)")
            sender = headers.get("From", "unknown")
            date = headers.get("Date", "")
            lines.append(f"- **{subject}** from {sender} ({date})")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_read_sync)
        gws_api_calls_total.labels(service="gmail", operation="read").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="gmail", error_type=type(exc).__name__
        ).inc()
        return f"Error reading Gmail: {exc}"


async def send_message(
    user_email: str,
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
    attachment_path: str | None = None,
) -> str:
    """Send a Gmail message."""

    def _send_sync():
        service = get_gmail_service(user_email)

        if attachment_path:
            msg = MIMEMultipart()
            msg["to"] = to
            msg["from"] = user_email
            msg["subject"] = subject
            if cc:
                msg["cc"] = cc
            msg.attach(MIMEText(body, "plain"))

            path = Path(attachment_path)
            if path.exists():
                part = MIMEBase("application", "octet-stream")
                part.set_payload(path.read_bytes())
                import email.encoders

                email.encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={path.name}",
                )
                msg.attach(part)
        else:
            msg = MIMEText(body)
            msg["to"] = to
            msg["from"] = user_email
            msg["subject"] = subject
            if cc:
                msg["cc"] = cc

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = (
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
        )
        return f"Email sent to {to} (ID: {result['id']})."

    try:
        result = await asyncio.to_thread(_send_sync)
        gws_api_calls_total.labels(service="gmail", operation="send").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="gmail", error_type=type(exc).__name__
        ).inc()
        return f"Error sending Gmail: {exc}"


async def search_messages(
    user_email: str,
    query: str,
    limit: int = 10,
) -> str:
    """Search Gmail messages."""
    return await read_messages(user_email, query=query, limit=limit)
