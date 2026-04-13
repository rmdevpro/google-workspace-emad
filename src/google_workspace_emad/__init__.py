"""
Brin — Google Workspace Service Broker eMAD.

Prometheus counters registered at import time.
"""

from prometheus_client import Counter

brin_api_calls_total = Counter(
    "brin_api_calls_total",
    "Google API calls",
    ["service", "operation"],
)
brin_api_errors_total = Counter(
    "brin_api_errors_total",
    "Google API errors",
    ["service", "error_type"],
)
brin_token_refreshes_total = Counter(
    "brin_token_refreshes_total",
    "Token refresh operations",
    ["account"],
)
brin_token_refresh_failures_total = Counter(
    "brin_token_refresh_failures_total",
    "Failed token refreshes",
    ["account"],
)
