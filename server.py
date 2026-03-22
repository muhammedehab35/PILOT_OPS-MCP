"""
Incident Response Autopilot - MCP Server
=========================================
A powerful MCP server that connects Claude to your monitoring stack
(Prometheus, Grafana, Loki, PagerDuty, Slack) for automated incident response.

Usage:
    python server.py
    # or via MCP CLI:
    mcp run server.py
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from tools.prometheus import get_active_alerts, get_metrics, silence_alert
from tools.grafana import get_grafana_dashboards, create_grafana_annotation
from tools.loki import get_logs
from tools.pagerduty import get_pagerduty_incidents, create_pagerduty_incident, update_pagerduty_incident
from tools.slack import notify_slack
from core.correlator import analyze_incident as _analyze_incident
from core.runbook import generate_runbook as _generate_runbook

mcp = FastMCP(
    name="incident-response-autopilot",
    instructions=(
        "You are an expert Site Reliability Engineer (SRE). "
        "Use the available tools to monitor infrastructure, detect incidents, "
        "correlate alerts with logs and metrics, generate runbooks, create PagerDuty incidents, "
        "and notify the team via Slack. Always start by fetching active alerts, "
        "then gather context (metrics + logs), analyze the incident, and propose a runbook."
    ),
)


# ─── Prometheus ───────────────────────────────────────────────────────────────

@mcp.tool()
async def prometheus_get_active_alerts() -> dict[str, Any]:
    """
    Fetch all currently firing alerts from Prometheus Alertmanager.
    Returns alert names, severity, labels, annotations, and start times.
    Use this as the first step when investigating any incident.
    """
    return await get_active_alerts()


@mcp.tool()
async def prometheus_get_metrics(
    query: str,
    start: str = "now-15m",
    end: str = "now",
    step: str = "60s",
) -> dict[str, Any]:
    """
    Query Prometheus time-series metrics using PromQL.

    Use this to investigate resource usage (CPU, memory, disk, network, latency).

    Common queries:
    - CPU usage: 100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
    - Memory usage: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100
    - HTTP error rate: rate(http_requests_total{status=~"5.."}[5m])
    - Disk usage: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100
    """
    return await get_metrics(query, start, end, step)


@mcp.tool()
async def prometheus_silence_alert(
    alert_name: str,
    duration_minutes: int = 60,
    comment: str = "Silenced by Incident Response Autopilot",
) -> dict[str, Any]:
    """
    Silence a Prometheus alert for a specified duration.
    Use this to suppress known/expected alerts during maintenance or investigation.
    Always provide a clear comment explaining why you are silencing the alert.
    """
    return await silence_alert(alert_name, duration_minutes, comment)


# ─── Grafana ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def grafana_get_dashboards(query: str = "") -> dict[str, Any]:
    """
    List available Grafana dashboards, optionally filtered by name.
    Returns dashboard titles, UIDs, URLs, and tags.
    Use this to find the relevant dashboard to share with the team during an incident.
    """
    return await get_grafana_dashboards(query)


@mcp.tool()
async def grafana_create_annotation(
    text: str,
    tags: list[str] | None = None,
    dashboard_uid: str = "",
) -> dict[str, Any]:
    """
    Create a Grafana annotation to mark an incident event on dashboards.
    This creates a visible marker on the timeline for post-incident analysis.
    Always create an annotation when an incident is declared (start) and resolved (end).
    Example text: '[P1 START] High CPU on prod-server-01 - Incident #42'
    """
    return await create_grafana_annotation(text, tags, dashboard_uid)


# ─── Loki ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def loki_get_logs(
    query: str,
    last_minutes: int = 15,
    limit: int = 100,
    level: str = "",
) -> dict[str, Any]:
    """
    Fetch logs from Loki using LogQL.
    Use this to investigate error patterns and correlate logs with alerts.

    LogQL examples:
    - All logs from an app: {app="payments-api"}
    - Logs from a host: {host="prod-server-01"}
    - Error logs only: {app="payments-api"} |= "error"
    - Kubernetes pod logs: {namespace="production", pod=~"api-.*"}

    Set level="error" to automatically filter for error-level messages.
    """
    return await get_logs(query, last_minutes, limit, level)


# ─── PagerDuty ────────────────────────────────────────────────────────────────

@mcp.tool()
async def pagerduty_get_incidents(
    status: str = "triggered,acknowledged",
    limit: int = 10,
) -> dict[str, Any]:
    """
    List open PagerDuty incidents.
    Returns incident ID, title, urgency, status, service, and assignees.
    Use this to check if an incident has already been created before creating a new one.
    Status options: 'triggered', 'acknowledged', 'resolved' (comma-separated)
    """
    return await get_pagerduty_incidents(status, limit)


@mcp.tool()
async def pagerduty_create_incident(
    title: str,
    urgency: str = "high",
    body: str = "",
) -> dict[str, Any]:
    """
    Create a new PagerDuty incident and page the on-call engineer.
    Use 'high' urgency for P1/P2 incidents that require immediate response.
    Use 'low' urgency for P3/P4 incidents.
    Always include a clear title and detailed body with impact and symptoms.
    """
    return await create_pagerduty_incident(title, urgency, body)  # type: ignore[arg-type]


@mcp.tool()
async def pagerduty_update_incident(
    incident_id: str,
    status: str = "acknowledged",
    note: str = "",
) -> dict[str, Any]:
    """
    Update a PagerDuty incident status and optionally add a timeline note.
    Status: 'acknowledged' (working on it) or 'resolved' (incident closed).
    Always add a note when resolving to document what was done.
    """
    return await update_pagerduty_incident(incident_id, status, note)  # type: ignore[arg-type]


# ─── Slack ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def slack_notify(
    message: str,
    channel: str = "",
    severity: str = "info",
    title: str = "",
) -> dict[str, Any]:
    """
    Send a notification to a Slack channel.
    Severity controls the color and emoji: 'critical', 'warning', 'info', 'resolved'.
    Use 'critical' for P1 incidents, 'warning' for P2/P3, 'resolved' when fixed.
    Always notify the team when an incident is declared AND when it is resolved.
    """
    return await notify_slack(message, channel, severity, title)


# ─── Core Intelligence ────────────────────────────────────────────────────────

@mcp.tool()
async def analyze_incident(
    alerts: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    logs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Correlate alerts, metrics, and logs to diagnose an incident.

    This is the core intelligence tool. Pass in the outputs from:
    - prometheus_get_active_alerts() → alerts
    - prometheus_get_metrics()       → metrics
    - loki_get_logs()                → logs

    Returns:
    - Incident severity (P1-P4)
    - Probable cause with confidence level
    - Affected services and hosts
    - List of recommended actions
    - Incident summary

    Always run this BEFORE generating a runbook.
    """
    return await _analyze_incident(alerts, metrics, logs)


@mcp.tool()
def generate_runbook(
    incident_type: str = "unknown",
    severity: str = "P2",
    affected_services: list[str] | None = None,
    affected_hosts: list[str] | None = None,
    custom_context: str = "",
) -> dict[str, Any]:
    """
    Generate a structured step-by-step incident runbook.

    Supported incident types:
    - memory_leak     : OOM / memory pressure
    - high_cpu        : CPU saturation
    - disk_full       : Disk space exhaustion
    - network_issue   : Connectivity / latency problems
    - database_issue  : DB overload / slow queries / deadlocks
    - service_crash   : Application crash / restart loop
    - deployment_issue: Failed Kubernetes rollout or deployment
    - unknown         : Generic runbook for unclassified incidents

    Returns a 4-phase runbook: Triage → Mitigation → Investigation → Resolution
    Also includes a ready-to-use Slack communication template.
    """
    return _generate_runbook(incident_type, severity, affected_services, affected_hosts, custom_context)


if __name__ == "__main__":
    mcp.run()
