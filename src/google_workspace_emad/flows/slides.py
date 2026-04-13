"""
google_workspace_emad.flows.slides — Google Slides operations.

Ported from mads/brin/js/server.js (2 tools).
"""

import asyncio
import logging

from google_workspace_emad import gws_api_calls_total, gws_api_errors_total
from google_workspace_emad.google_client import get_slides_service

_log = logging.getLogger("google_workspace_emad")


async def get_presentation(user_email: str, presentation_id: str) -> str:
    """Get presentation content."""

    def _sync():
        service = get_slides_service(user_email)
        pres = service.presentations().get(presentationId=presentation_id).execute()
        title = pres.get("title", "Untitled")
        slides = pres.get("slides", [])
        lines = [f"**{title}** ({len(slides)} slides)"]
        for i, slide in enumerate(slides, 1):
            elements = slide.get("pageElements", [])
            text_parts = []
            for elem in elements:
                shape = elem.get("shape", {})
                text_content = shape.get("text", {})
                for te in text_content.get("textElements", []):
                    text_run = te.get("textRun", {})
                    content = text_run.get("content", "").strip()
                    if content:
                        text_parts.append(content)
            if text_parts:
                lines.append(f"  Slide {i}: {' | '.join(text_parts[:3])}")
            else:
                lines.append(f"  Slide {i}: (no text)")
        return "\n".join(lines)

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="slides", operation="get").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="slides", error_type=type(exc).__name__
        ).inc()
        return f"Error getting presentation: {exc}"


async def create_presentation(user_email: str, title: str) -> str:
    """Create a new presentation."""

    def _sync():
        service = get_slides_service(user_email)
        body = {"title": title}
        pres = service.presentations().create(body=body).execute()
        return f"Created presentation '{title}' (id: {pres['presentationId']})."

    try:
        result = await asyncio.to_thread(_sync)
        gws_api_calls_total.labels(service="slides", operation="create").inc()
        return result
    except (RuntimeError, OSError, ValueError) as exc:
        gws_api_errors_total.labels(
            service="slides", error_type=type(exc).__name__
        ).inc()
        return f"Error creating presentation: {exc}"
