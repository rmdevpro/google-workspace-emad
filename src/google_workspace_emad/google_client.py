"""
google_workspace_emad.google_client — Google API authentication via service account.

Uses domain-wide delegation to impersonate users in the the configured Workspace domain.
Service account key file at /storage/credentials/google-workspace/service-account.json.
No OAuth dance — service accounts authenticate server-to-server.
"""

import logging
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

_log = logging.getLogger("google_workspace_emad")

_SERVICE_ACCOUNT_PATH = Path(
    os.environ.get(
        "GOOGLE_WORKSPACE_SERVICE_ACCOUNT",
        "/storage/credentials/oauth/google/credentials.json",
    )
)

ALL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/calendar",
]


def _get_credentials(user_email: str, scopes: list[str] | None = None):
    """Get delegated credentials for a Workspace user."""
    if not _SERVICE_ACCOUNT_PATH.exists():
        raise RuntimeError(
            f"Service account key not found at {_SERVICE_ACCOUNT_PATH}. "
            "Create a GCP service account and download the JSON key."
        )

    creds = service_account.Credentials.from_service_account_file(
        str(_SERVICE_ACCOUNT_PATH),
        scopes=scopes or ALL_SCOPES,
    )
    # Delegate to the target user
    delegated = creds.with_subject(user_email)
    return delegated


def get_gmail_service(user_email: str):
    """Get a Gmail API service for the specified user."""
    creds = _get_credentials(
        user_email,
        [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.send",
        ],
    )
    return build("gmail", "v1", credentials=creds)


def get_drive_service(user_email: str):
    """Get a Drive API service for the specified user."""
    creds = _get_credentials(user_email, ["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)


def get_docs_service(user_email: str):
    """Get a Docs API service for the specified user."""
    creds = _get_credentials(user_email, ["https://www.googleapis.com/auth/documents"])
    return build("docs", "v1", credentials=creds)


def get_sheets_service(user_email: str):
    """Get a Sheets API service for the specified user."""
    creds = _get_credentials(
        user_email, ["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)


def get_slides_service(user_email: str):
    """Get a Slides API service for the specified user."""
    creds = _get_credentials(
        user_email, ["https://www.googleapis.com/auth/presentations"]
    )
    return build("slides", "v1", credentials=creds)


def get_calendar_service(user_email: str):
    """Get a Calendar API service for the specified user."""
    creds = _get_credentials(user_email, ["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=creds)
