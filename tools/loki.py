"""Loki tools: fetch and search logs."""
from __future__ import annotations

import time
from typing import Any

import httpx

from config import settings


def _auth() -> httpx.BasicAuth | None:
    if settings.loki_username:
        return httpx.BasicAuth(settings.loki_username, settings.loki_password)
    return None


async def get_logs(
    query: str,
    last_minutes: int = 15,
    limit: int = 100,
    level: str = "",
) -> dict[str, Any]:
    """
    Fetch logs from Loki using LogQL.

    Args:
        query: LogQL stream selector (e.g. '{app="payments-api"}' or '{host="prod-server-01"}')
        last_minutes: How many minutes back to search (default 15)
        limit: Max number of log lines to return (default 100)
        level: Filter by log level: 'error', 'warn', 'info' (empty = all levels)

    Returns structured list of log entries with timestamp and message.
    """
    now_ns = int(time.time() * 1e9)
    start_ns = int((time.time() - last_minutes * 60) * 1e9)

    # Add level filter if specified
    log_query = query
    if level:
        log_query = f'{query} |= `{level}`'

    params = {
        "query": log_query,
        "start": str(start_ns),
        "end": str(now_ns),
        "limit": limit,
        "direction": "backward",
    }

    url = f"{settings.loki_url}/loki/api/v1/query_range"
    async with httpx.AsyncClient(auth=_auth(), timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    data = resp.json()
    streams = data.get("data", {}).get("result", [])

    entries = []
    for stream in streams:
        labels = stream.get("stream", {})
        for ts, line in stream.get("values", []):
            entries.append({
                "timestamp": int(ts) / 1e9,  # convert ns to seconds
                "message": line,
                "labels": labels,
            })

    # Sort by timestamp descending (most recent first)
    entries.sort(key=lambda x: x["timestamp"], reverse=True)

    # Detect error patterns
    error_count = sum(1 for e in entries if any(
        kw in e["message"].lower() for kw in ["error", "exception", "fatal", "panic", "critical"]
    ))

    return {
        "query": log_query,
        "last_minutes": last_minutes,
        "total_lines": len(entries),
        "error_lines": error_count,
        "entries": entries[:limit],
    }
