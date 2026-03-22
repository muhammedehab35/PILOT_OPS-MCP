"""Prometheus tools: alerts, metrics, silences."""
from __future__ import annotations

import time
from typing import Any

import httpx

from config import settings


def _auth() -> httpx.BasicAuth | None:
    if settings.prometheus_username:
        return httpx.BasicAuth(settings.prometheus_username, settings.prometheus_password)
    return None


async def get_active_alerts() -> dict[str, Any]:
    """
    Fetch all currently firing alerts from Prometheus Alertmanager.
    Returns a structured dict with alert name, labels, severity, and start time.
    """
    url = f"{settings.prometheus_url}/api/v2/alerts"
    async with httpx.AsyncClient(auth=_auth(), timeout=10) as client:
        resp = await client.get(url, params={"active": "true", "silenced": "false"})
        resp.raise_for_status()

    alerts = resp.json()
    result = []
    for a in alerts:
        result.append({
            "name": a.get("labels", {}).get("alertname", "unknown"),
            "severity": a.get("labels", {}).get("severity", "unknown"),
            "status": a.get("status", {}).get("state", "unknown"),
            "labels": a.get("labels", {}),
            "annotations": a.get("annotations", {}),
            "starts_at": a.get("startsAt", ""),
        })

    return {"total": len(result), "alerts": result}


async def get_metrics(query: str, start: str = "now-15m", end: str = "now", step: str = "60s") -> dict[str, Any]:
    """
    Query Prometheus metrics using PromQL.

    Args:
        query: PromQL expression (e.g. 'node_cpu_seconds_total{mode="idle"}')
        start: Start time (e.g. 'now-15m' or Unix timestamp)
        end: End time (e.g. 'now' or Unix timestamp)
        step: Query resolution step (e.g. '60s', '5m')

    Returns dict with metric name, labels, and time series values.
    """
    now = int(time.time())

    def parse_time(t: str) -> int:
        if t == "now":
            return now
        if t.startswith("now-"):
            suffix = t[4:]
            mult = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            return now - int(suffix[:-1]) * mult.get(suffix[-1], 1)
        return int(t)

    params = {
        "query": query,
        "start": parse_time(start),
        "end": parse_time(end),
        "step": step,
    }
    url = f"{settings.prometheus_url}/api/v1/query_range"
    async with httpx.AsyncClient(auth=_auth(), timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    data = resp.json()
    results = data.get("data", {}).get("result", [])

    formatted = []
    for series in results:
        formatted.append({
            "metric": series.get("metric", {}),
            "values": [{"timestamp": v[0], "value": v[1]} for v in series.get("values", [])],
        })

    return {"query": query, "series_count": len(formatted), "results": formatted}


async def silence_alert(
    alert_name: str,
    duration_minutes: int = 60,
    comment: str = "Silenced by Incident Response Autopilot",
    created_by: str = "mcp-autopilot",
) -> dict[str, Any]:
    """
    Silence a Prometheus alert for a given duration.

    Args:
        alert_name: Name of the alert to silence (matches alertname label)
        duration_minutes: How long to silence (default 60 minutes)
        comment: Reason for silencing
        created_by: Who is creating the silence

    Returns the created silence ID.
    """
    now = time.time()
    ends_at = now + duration_minutes * 60

    import datetime
    body = {
        "matchers": [{"name": "alertname", "value": alert_name, "isRegex": False}],
        "startsAt": datetime.datetime.utcfromtimestamp(now).isoformat() + "Z",
        "endsAt": datetime.datetime.utcfromtimestamp(ends_at).isoformat() + "Z",
        "createdBy": created_by,
        "comment": comment,
    }

    url = f"{settings.prometheus_url}/api/v2/silences"
    async with httpx.AsyncClient(auth=_auth(), timeout=10) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()

    data = resp.json()
    return {
        "success": True,
        "silence_id": data.get("silenceID"),
        "alert_name": alert_name,
        "duration_minutes": duration_minutes,
        "message": f"Alert '{alert_name}' silenced for {duration_minutes} minutes.",
    }
