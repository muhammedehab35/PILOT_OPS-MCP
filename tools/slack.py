"""Slack tools: send notifications and alerts."""
from __future__ import annotations

from typing import Any

import httpx

from config import settings

SLACK_API = "https://slack.com/api"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.slack_bot_token}",
        "Content-Type": "application/json",
    }


async def notify_slack(
    message: str,
    channel: str = "",
    severity: str = "info",
    title: str = "",
) -> dict[str, Any]:
    """
    Send a notification to a Slack channel.

    Args:
        message: The message body to send
        channel: Slack channel (e.g. '#incidents'). Uses default if empty.
        severity: 'critical', 'warning', 'info', 'resolved' - controls color
        title: Optional bold title shown above the message

    Returns success status and message timestamp.
    """
    target_channel = channel or settings.slack_default_channel

    color_map = {
        "critical": "#FF0000",
        "warning": "#FFA500",
        "info": "#0000FF",
        "resolved": "#00FF00",
    }
    color = color_map.get(severity, "#808080")

    emoji_map = {
        "critical": ":rotating_light:",
        "warning": ":warning:",
        "info": ":information_source:",
        "resolved": ":white_check_mark:",
    }
    emoji = emoji_map.get(severity, ":bell:")

    blocks: list[dict] = []
    if title:
        blocks.append({
            "type": "header",
            "text": {"type": "plain_text", "text": f"{emoji} {title}"},
        })

    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": message},
    })

    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"*Severity:* {severity.upper()} | Sent by Incident Response Autopilot"}],
    })

    payload = {
        "channel": target_channel,
        "blocks": blocks,
        "attachments": [{"color": color, "fallback": f"{title}: {message}"}],
    }

    async with httpx.AsyncClient(headers=_headers(), timeout=10) as client:
        resp = await client.post(f"{SLACK_API}/chat.postMessage", json=payload)
        resp.raise_for_status()

    data = resp.json()
    if not data.get("ok"):
        return {"success": False, "error": data.get("error", "unknown Slack error")}

    return {
        "success": True,
        "channel": target_channel,
        "timestamp": data.get("ts"),
        "message": f"Notification sent to {target_channel}.",
    }
