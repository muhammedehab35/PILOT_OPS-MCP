"""PagerDuty tools: incident management."""
from __future__ import annotations

from typing import Any, Literal

import httpx

from config import settings

BASE_URL = "https://api.pagerduty.com"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Token token={settings.pagerduty_api_key}",
        "Accept": "application/vnd.pagerduty+json;version=2",
        "Content-Type": "application/json",
        "From": settings.pagerduty_from_email,
    }


async def get_pagerduty_incidents(
    status: str = "triggered,acknowledged",
    limit: int = 10,
) -> dict[str, Any]:
    """
    List PagerDuty incidents filtered by status.

    Args:
        status: Comma-separated statuses: 'triggered', 'acknowledged', 'resolved'
        limit: Max number of incidents to return (default 10)

    Returns list of incidents with id, title, severity, status, and created_at.
    """
    params = {
        "statuses[]": status.split(","),
        "limit": limit,
        "sort_by": "created_at:desc",
    }

    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/incidents", params=params)
        resp.raise_for_status()

    data = resp.json()
    incidents = [
        {
            "id": inc.get("id"),
            "number": inc.get("incident_number"),
            "title": inc.get("title"),
            "status": inc.get("status"),
            "urgency": inc.get("urgency"),
            "service": inc.get("service", {}).get("summary", ""),
            "created_at": inc.get("created_at"),
            "html_url": inc.get("html_url"),
            "assignees": [a.get("assignee", {}).get("summary", "") for a in inc.get("assignments", [])],
        }
        for inc in data.get("incidents", [])
    ]

    return {"total": len(incidents), "incidents": incidents}


async def create_pagerduty_incident(
    title: str,
    urgency: Literal["high", "low"] = "high",
    body: str = "",
) -> dict[str, Any]:
    """
    Create a new PagerDuty incident.

    Args:
        title: Short incident title (e.g. "P1: High CPU on prod-server-01")
        urgency: 'high' for P1/P2, 'low' for P3/P4
        body: Detailed incident description / impact summary

    Returns the created incident ID and URL.
    """
    payload: dict[str, Any] = {
        "incident": {
            "type": "incident",
            "title": title,
            "urgency": urgency,
            "service": {
                "id": settings.pagerduty_service_id,
                "type": "service_reference",
            },
            "escalation_policy": {
                "id": settings.pagerduty_escalation_policy_id,
                "type": "escalation_policy_reference",
            },
        }
    }
    if body:
        payload["incident"]["body"] = {"type": "incident_body", "details": body}

    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        resp = await client.post(f"{BASE_URL}/incidents", json=payload)
        resp.raise_for_status()

    inc = resp.json().get("incident", {})
    return {
        "success": True,
        "incident_id": inc.get("id"),
        "incident_number": inc.get("incident_number"),
        "html_url": inc.get("html_url"),
        "status": inc.get("status"),
        "message": f"Incident created: #{inc.get('incident_number')} - {title}",
    }


async def update_pagerduty_incident(
    incident_id: str,
    status: Literal["acknowledged", "resolved"] = "acknowledged",
    note: str = "",
) -> dict[str, Any]:
    """
    Update a PagerDuty incident status and optionally add a note.

    Args:
        incident_id: The PagerDuty incident ID
        status: New status: 'acknowledged' or 'resolved'
        note: Optional note to add to the incident timeline

    Returns updated incident status.
    """
    payload = {
        "incident": {
            "type": "incident",
            "status": status,
        }
    }

    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        resp = await client.put(f"{BASE_URL}/incidents/{incident_id}", json=payload)
        resp.raise_for_status()

        # Add note if provided
        if note:
            note_payload = {"note": {"content": note}}
            await client.post(f"{BASE_URL}/incidents/{incident_id}/notes", json=note_payload)

    inc = resp.json().get("incident", {})
    return {
        "success": True,
        "incident_id": incident_id,
        "new_status": inc.get("status"),
        "note_added": bool(note),
        "message": f"Incident {incident_id} updated to '{status}'.",
    }
