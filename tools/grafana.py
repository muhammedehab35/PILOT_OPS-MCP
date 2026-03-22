"""Grafana tools: dashboards and annotations."""
from __future__ import annotations

import time
from typing import Any

import httpx

from config import settings


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.grafana_api_key}",
        "Content-Type": "application/json",
        "X-Grafana-Org-Id": str(settings.grafana_org_id),
    }


async def get_grafana_dashboards(query: str = "") -> dict[str, Any]:
    """
    List Grafana dashboards, optionally filtered by name.

    Args:
        query: Search string to filter dashboards by title

    Returns list of dashboards with uid, title, url, and tags.
    """
    params: dict[str, Any] = {"type": "dash-db", "limit": 50}
    if query:
        params["query"] = query

    url = f"{settings.grafana_url}/api/search"
    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    dashboards = resp.json()
    result = [
        {
            "uid": d.get("uid"),
            "title": d.get("title"),
            "url": f"{settings.grafana_url}{d.get('url', '')}",
            "tags": d.get("tags", []),
            "folder": d.get("folderTitle", "General"),
        }
        for d in dashboards
    ]
    return {"total": len(result), "dashboards": result}


async def create_grafana_annotation(
    text: str,
    tags: list[str] | None = None,
    dashboard_uid: str = "",
) -> dict[str, Any]:
    """
    Create a Grafana annotation to mark an incident on dashboards.

    Args:
        text: Annotation message (e.g. "P1 Incident: high CPU on prod-server-01")
        tags: List of tags (e.g. ["incident", "P1", "cpu"])
        dashboard_uid: UID of specific dashboard (empty = global annotation)

    Returns the created annotation ID.
    """
    body: dict[str, Any] = {
        "time": int(time.time() * 1000),
        "text": text,
        "tags": tags or ["incident", "mcp-autopilot"],
    }
    if dashboard_uid:
        body["dashboardUID"] = dashboard_uid

    url = f"{settings.grafana_url}/api/annotations"
    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        resp = await client.post(url, json=body)
        resp.raise_for_status()

    data = resp.json()
    return {
        "success": True,
        "annotation_id": data.get("id"),
        "message": f"Annotation created: '{text}'",
    }
