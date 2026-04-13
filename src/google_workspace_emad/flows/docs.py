"""
google_workspace_emad.flows.docs — Google Docs operations.

Ported from mads/brin/js/server.js (3 tools).
"""

import asyncio
import logging

from google_workspace_emad import brin_api_calls_total, brin_api_errors_total
from google_workspace_emad.google_client import get_docs_service

_log = logging.getLogger("google_workspace_emad")


async def read_document(user_email: str, document_id: str) -> str:
    """Read a Google Doc's content as plain text."""

    def _sync():
        service = get_docs_service(user_email)
        doc = service.documents().get(documentId=document_id).execute()
        title = doc.get("title", "Untitled")

        # Extract text from document body
        content = doc.get("body", {}).get("content", [])
        text_parts = []
        for element in content:
            paragraph = element.get("paragraph", {})
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun", {})
                text = text_run.get("content", "")
                if text.strip():
                    text_parts.append(text)

        return f"**{title}**\n\n{''.join(text_parts)}"

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="docs", operation="read").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="docs", error_type=type(exc).__name__
        ).inc()
        return f"Error reading document: {exc}"


async def write_document(user_email: str, document_id: str, content: str) -> str:
    """Write/append content to a Google Doc."""

    def _sync():
        service = get_docs_service(user_email)
        # Get current doc length to determine insert index
        doc = service.documents().get(documentId=document_id).execute()
        body_content = doc.get("body", {}).get("content", [])
        # Find the end index (last element's endIndex - 1)
        end_index = 1
        for element in body_content:
            if "endIndex" in element:
                end_index = element["endIndex"]

        requests = [
            {"insertText": {"location": {"index": end_index - 1}, "text": content}}
        ]
        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()
        return f"Written {len(content)} characters to document {document_id}."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="docs", operation="write").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="docs", error_type=type(exc).__name__
        ).inc()
        return f"Error writing document: {exc}"


async def create_document(user_email: str, title: str, body: str = "") -> str:
    """Create a new Google Doc."""

    def _sync():
        service = get_docs_service(user_email)
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]

        if body:
            requests = [{"insertText": {"location": {"index": 1}, "text": body}}]
            service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()

        return f"Created document '{title}' (id: {doc_id})."

    try:
        result = await asyncio.to_thread(_sync)
        brin_api_calls_total.labels(service="docs", operation="create").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        brin_api_errors_total.labels(
            service="docs", error_type=type(exc).__name__
        ).inc()
        return f"Error creating document: {exc}"
