"""
google_workspace_emad.register — eMAD entry point.
"""

from langgraph.graph import StateGraph

EMAD_NAME = "google-workspace-emad"
DESCRIPTION = (
    "Google Workspace Service Broker — Gmail, Drive, Docs, Sheets, Slides, "
    "Calendar access with service account authentication."
)


def build_graph(params: dict | None = None) -> StateGraph:
    """Return the compiled Google Workspace Imperator StateGraph."""
    from google_workspace_emad.flows.imperator import build_imperator_graph

    return build_imperator_graph(params)
