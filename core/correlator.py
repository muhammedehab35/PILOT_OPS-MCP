"""
Incident correlation engine.
Combines alerts, metrics, and logs to diagnose the root cause of an incident.
"""
from __future__ import annotations

from typing import Any


# Known incident patterns: maps symptom keywords to probable causes and actions
INCIDENT_PATTERNS: list[dict[str, Any]] = [
    {
        "name": "memory_leak",
        "keywords": ["out of memory", "oom", "memory pressure", "heap", "gc overhead"],
        "probable_cause": "Memory leak or insufficient memory allocation",
        "recommended_actions": [
            "Restart the affected service to free memory",
            "Increase memory limits in Kubernetes or VM config",
            "Check for heap dumps and analyze with a profiler",
            "Review recent deployments for memory regression",
        ],
    },
    {
        "name": "high_cpu",
        "keywords": ["cpu", "throttle", "load average", "cpu usage", "iowait"],
        "probable_cause": "CPU saturation - possible runaway process or heavy computation",
        "recommended_actions": [
            "Identify top CPU-consuming processes (top/htop)",
            "Check for infinite loops or expensive queries",
            "Scale horizontally if load is legitimate",
            "Review recent deployments",
        ],
    },
    {
        "name": "disk_full",
        "keywords": ["disk", "no space", "filesystem", "inode", "storage"],
        "probable_cause": "Disk space exhaustion",
        "recommended_actions": [
            "Identify and remove large/stale log files",
            "Rotate logs and archive old data",
            "Expand disk volume or add storage",
            "Check for runaway log generation",
        ],
    },
    {
        "name": "network_issue",
        "keywords": ["timeout", "connection refused", "network", "latency", "packet loss", "unreachable"],
        "probable_cause": "Network connectivity or latency issue",
        "recommended_actions": [
            "Check network connectivity between services",
            "Verify DNS resolution",
            "Inspect firewall rules and security groups",
            "Check for network partition or upstream outage",
        ],
    },
    {
        "name": "database_issue",
        "keywords": ["database", "sql", "connection pool", "deadlock", "query timeout", "db"],
        "probable_cause": "Database overload or connectivity issue",
        "recommended_actions": [
            "Check active connections and slow queries",
            "Kill long-running or blocking queries",
            "Check database replication lag",
            "Review connection pool settings",
        ],
    },
    {
        "name": "service_crash",
        "keywords": ["segfault", "panic", "core dump", "killed", "exit code", "crash"],
        "probable_cause": "Application crash or fatal error",
        "recommended_actions": [
            "Restart the service immediately",
            "Collect and analyze core dumps or crash logs",
            "Check for recent deployments that could have introduced the bug",
            "Roll back if crash started after a deployment",
        ],
    },
    {
        "name": "deployment_issue",
        "keywords": ["deploy", "rollout", "image", "container", "pod crashloop", "imagepull"],
        "probable_cause": "Failed or broken deployment",
        "recommended_actions": [
            "Roll back to the previous stable version",
            "Check pod events: kubectl describe pod",
            "Verify the container image exists and is pullable",
            "Review deployment configuration changes",
        ],
    },
]


def _severity_from_alerts(alerts: list[dict]) -> str:
    severities = [a.get("severity", "").lower() for a in alerts]
    if "critical" in severities:
        return "P1"
    if "high" in severities or "error" in severities:
        return "P2"
    if "warning" in severities or "warn" in severities:
        return "P3"
    return "P4"


def _match_patterns(text: str) -> list[dict]:
    text_lower = text.lower()
    matched = []
    for pattern in INCIDENT_PATTERNS:
        score = sum(1 for kw in pattern["keywords"] if kw in text_lower)
        if score > 0:
            matched.append({**pattern, "match_score": score})
    return sorted(matched, key=lambda x: x["match_score"], reverse=True)


async def analyze_incident(
    alerts: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    logs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Correlate alerts, metrics, and logs to produce a structured incident diagnosis.

    Args:
        alerts: Output from get_active_alerts()
        metrics: Output from get_metrics()
        logs: Output from get_logs()

    Returns a diagnosis with probable cause, severity, impact, and recommended actions.
    """
    # Build combined text corpus for pattern matching
    corpus_parts = []

    alert_list = alerts.get("alerts", []) if alerts else []
    for a in alert_list:
        corpus_parts.append(a.get("name", ""))
        corpus_parts.append(a.get("annotations", {}).get("description", ""))
        corpus_parts.append(a.get("annotations", {}).get("summary", ""))
        corpus_parts.extend(str(v) for v in a.get("labels", {}).values())

    if logs:
        error_entries = [
            e["message"] for e in logs.get("entries", [])
            if any(kw in e["message"].lower() for kw in ["error", "exception", "fatal", "panic"])
        ][:20]
        corpus_parts.extend(error_entries)

    corpus = " ".join(corpus_parts)
    matched_patterns = _match_patterns(corpus)
    severity = _severity_from_alerts(alert_list)

    # Top pattern
    top_pattern = matched_patterns[0] if matched_patterns else None

    # Affected services
    affected_services = list({
        a.get("labels", {}).get("service", a.get("labels", {}).get("job", "unknown"))
        for a in alert_list
    })

    # Affected hosts
    affected_hosts = list({
        a.get("labels", {}).get("instance", a.get("labels", {}).get("host", "unknown"))
        for a in alert_list
    })

    diagnosis = {
        "severity": severity,
        "total_alerts": len(alert_list),
        "affected_services": affected_services,
        "affected_hosts": affected_hosts,
        "probable_cause": top_pattern["probable_cause"] if top_pattern else "Unknown - manual investigation required",
        "incident_type": top_pattern["name"] if top_pattern else "unknown",
        "confidence": "high" if (top_pattern and top_pattern["match_score"] >= 2) else "medium" if top_pattern else "low",
        "recommended_actions": top_pattern["recommended_actions"] if top_pattern else ["Manually investigate alerts and logs"],
        "alternative_causes": [p["probable_cause"] for p in matched_patterns[1:3]],
        "log_error_count": logs.get("error_lines", 0) if logs else 0,
        "summary": (
            f"[{severity}] {len(alert_list)} alert(s) detected. "
            f"Probable cause: {top_pattern['probable_cause'] if top_pattern else 'unknown'}. "
            f"Affected: {', '.join(affected_services[:3]) or 'unknown'}."
        ),
    }

    return diagnosis
