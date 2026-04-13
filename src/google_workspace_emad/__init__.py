"""
Google Workspace Service Broker eMAD.

Prometheus counters registered at import time.
"""

from prometheus_client import Counter

gws_api_calls_total = Counter(
    "gws_api_calls_total",
    "Google API calls",
    ["service", "operation"],
)
gws_api_errors_total = Counter(
    "gws_api_errors_total",
    "Google API errors",
    ["service", "error_type"],
)
gws_token_refreshes_total = Counter(
    "gws_token_refreshes_total",
    "Token refresh operations",
    ["account"],
)
gws_token_refresh_failures_total = Counter(
    "gws_token_refresh_failures_total",
    "Failed token refreshes",
    ["account"],
)

from google_workspace_emad.register import build_graph  # noqa: E402, F401
