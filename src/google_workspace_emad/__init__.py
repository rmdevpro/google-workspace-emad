"""
Google Workspace Service Broker eMAD.

Prometheus counters registered at import time.
Safe for module re-import (hot-reload).
"""

from prometheus_client import Counter, CollectorRegistry, REGISTRY


def _get_or_create_counter(name, description, labelnames):
    """Get existing counter or create new one. Safe for reimport."""
    try:
        return Counter(name, description, labelnames)
    except ValueError:
        # Already registered — retrieve from registry
        for collector in REGISTRY._names_to_collectors.values():
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        # Fallback: unregister and re-register
        try:
            REGISTRY.unregister(REGISTRY._names_to_collectors.get(name))
        except (KeyError, AttributeError):
            pass
        return Counter(name, description, labelnames)


gws_api_calls_total = _get_or_create_counter(
    "gws_api_calls_total",
    "Google API calls",
    ["service", "operation"],
)
gws_api_errors_total = _get_or_create_counter(
    "gws_api_errors_total",
    "Google API errors",
    ["service", "error_type"],
)
gws_token_refreshes_total = _get_or_create_counter(
    "gws_token_refreshes_total",
    "Token refresh operations",
    ["account"],
)
gws_token_refresh_failures_total = _get_or_create_counter(
    "gws_token_refresh_failures_total",
    "Failed token refreshes",
    ["account"],
)

from google_workspace_emad.register import build_graph  # noqa: E402, F401
