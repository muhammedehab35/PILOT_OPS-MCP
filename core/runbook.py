"""
Runbook generator.
Produces structured, step-by-step runbooks based on incident type and context.
"""
from __future__ import annotations

from typing import Any


RUNBOOK_TEMPLATES: dict[str, dict[str, Any]] = {
    "memory_leak": {
        "title": "Memory Leak / OOM Incident Runbook",
        "triage_steps": [
            "1. Confirm the alert: check current memory usage with `free -h` or Grafana memory dashboard",
            "2. Identify the top memory consumers: `ps aux --sort=-%mem | head -20`",
            "3. Check for OOM kills in kernel logs: `dmesg | grep -i 'oom'`",
        ],
        "mitigation_steps": [
            "1. Restart the affected service to free memory immediately",
            "2. Enable memory limits if not already set (Kubernetes: resources.limits.memory)",
            "3. Set up swap if not present: `fallocate -l 4G /swapfile && mkswap /swapfile && swapon /swapfile`",
        ],
        "investigation_steps": [
            "1. Collect heap dump if the service supports it (JVM: jmap, Go: pprof)",
            "2. Review recent code changes for unbounded data structures or missing cleanup",
            "3. Check for memory fragmentation or GC issues in application logs",
        ],
        "resolution_steps": [
            "1. Deploy fix or roll back the problematic version",
            "2. Verify memory usage returns to baseline",
            "3. Resolve PagerDuty incident and post-mortem",
        ],
    },
    "high_cpu": {
        "title": "High CPU Utilization Runbook",
        "triage_steps": [
            "1. Confirm CPU spike on affected host using `top` or Grafana CPU dashboard",
            "2. Identify top CPU consumers: `top -bn1 | head -20`",
            "3. Check CPU steal time (VM environments): high steal = noisy neighbor problem",
        ],
        "mitigation_steps": [
            "1. If a single process is consuming all CPU, consider restarting it",
            "2. Scale horizontally: add more instances or pods",
            "3. Rate-limit or throttle incoming traffic if under DDoS",
        ],
        "investigation_steps": [
            "1. Profile the process: `perf top -p <PID>` or language-specific profiler",
            "2. Check for expensive database queries or external API calls",
            "3. Review recent deployments for performance regression",
        ],
        "resolution_steps": [
            "1. Apply fix or roll back if deployment-related",
            "2. Confirm CPU returns to normal baseline",
            "3. Update capacity planning if load is legitimate growth",
        ],
    },
    "disk_full": {
        "title": "Disk Space Exhaustion Runbook",
        "triage_steps": [
            "1. Confirm disk usage: `df -h`",
            "2. Find largest directories: `du -sh /* 2>/dev/null | sort -rh | head -10`",
            "3. Check inodes: `df -i` (disk can be full even with space via inode exhaustion)",
        ],
        "mitigation_steps": [
            "1. Remove old log files: `find /var/log -name '*.log' -mtime +7 -delete`",
            "2. Clear package caches: `apt-get clean` or `yum clean all`",
            "3. Truncate large log files safely: `> /var/log/myservice.log`",
        ],
        "investigation_steps": [
            "1. Identify what is growing fastest (logs, DB, /tmp)",
            "2. Review log rotation configuration",
            "3. Check for runaway processes generating excessive output",
        ],
        "resolution_steps": [
            "1. Set up proper log rotation (logrotate)",
            "2. Expand disk volume or add a separate partition for logs/data",
            "3. Set up disk space alerting at 70%, 85%, 95%",
        ],
    },
    "network_issue": {
        "title": "Network Connectivity Issue Runbook",
        "triage_steps": [
            "1. Ping affected hosts: `ping -c 5 <host>`",
            "2. Check DNS resolution: `nslookup <service-hostname>`",
            "3. Trace the route: `traceroute <host>` or `mtr <host>`",
        ],
        "mitigation_steps": [
            "1. Restart network interfaces if safe: `ip link set eth0 down && ip link set eth0 up`",
            "2. Flush DNS cache: `systemctl restart systemd-resolved`",
            "3. Check and update firewall rules if access is blocked",
        ],
        "investigation_steps": [
            "1. Check for BGP route flaps or upstream ISP issues",
            "2. Review recent infrastructure changes (security groups, VPC, firewall)",
            "3. Analyze packet loss: `iperf3` between affected hosts",
        ],
        "resolution_steps": [
            "1. Restore network path or failover to backup link",
            "2. Update DNS/firewall rules as needed",
            "3. Contact ISP/cloud provider if upstream issue confirmed",
        ],
    },
    "database_issue": {
        "title": "Database Incident Runbook",
        "triage_steps": [
            "1. Check active connections: `SELECT count(*) FROM pg_stat_activity;` (Postgres)",
            "2. Find slow/blocking queries: `SELECT * FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;`",
            "3. Check replication lag on replicas",
        ],
        "mitigation_steps": [
            "1. Kill long-running blocking queries: `SELECT pg_terminate_backend(<pid>);`",
            "2. Increase max_connections if pool is exhausted",
            "3. Switch application to read replicas to reduce primary load",
        ],
        "investigation_steps": [
            "1. Review slow query logs for repeated expensive queries",
            "2. Check for missing indexes on frequently queried columns",
            "3. Analyze table bloat: `SELECT * FROM pg_stat_user_tables ORDER BY n_dead_tup DESC;`",
        ],
        "resolution_steps": [
            "1. Add missing indexes (use CONCURRENTLY to avoid locks)",
            "2. Tune connection pool size (PgBouncer recommended)",
            "3. Schedule VACUUM/ANALYZE during low-traffic window",
        ],
    },
    "service_crash": {
        "title": "Service Crash / Restart Loop Runbook",
        "triage_steps": [
            "1. Check service status: `systemctl status <service>` or `kubectl get pods`",
            "2. View recent logs: `journalctl -u <service> -n 100 --no-pager`",
            "3. Check exit code and crash frequency",
        ],
        "mitigation_steps": [
            "1. Restart the service: `systemctl restart <service>` or `kubectl rollout restart deployment/<name>`",
            "2. If crash loop, roll back to last known good version",
            "3. Isolate the crashing instance from load balancer if needed",
        ],
        "investigation_steps": [
            "1. Analyze core dump if available",
            "2. Check resource limits (OOM, CPU throttle)",
            "3. Review recent commits and deployments",
        ],
        "resolution_steps": [
            "1. Deploy fix or roll back",
            "2. Add crash reporting / Sentry for future visibility",
            "3. Conduct post-mortem and add regression test",
        ],
    },
    "deployment_issue": {
        "title": "Failed Deployment Runbook",
        "triage_steps": [
            "1. Check deployment status: `kubectl rollout status deployment/<name>`",
            "2. Describe failing pods: `kubectl describe pod <pod-name>`",
            "3. View pod logs: `kubectl logs <pod-name> --previous`",
        ],
        "mitigation_steps": [
            "1. Roll back immediately: `kubectl rollout undo deployment/<name>`",
            "2. Pause the rollout if partially deployed: `kubectl rollout pause deployment/<name>`",
            "3. Scale down failed replicas if rollback is not possible",
        ],
        "investigation_steps": [
            "1. Compare the new and old deployment manifests",
            "2. Check image pull errors (wrong tag, private registry auth)",
            "3. Review ConfigMaps and Secrets for missing env vars",
        ],
        "resolution_steps": [
            "1. Fix the root cause (image, config, resource limits)",
            "2. Re-deploy with fix and monitor rollout",
            "3. Add deployment smoke tests to CI/CD pipeline",
        ],
    },
    "unknown": {
        "title": "General Incident Runbook",
        "triage_steps": [
            "1. Review all active alerts in Prometheus/Grafana",
            "2. Collect logs from affected services (last 30 minutes)",
            "3. Identify the timeline of when symptoms started",
        ],
        "mitigation_steps": [
            "1. Assess user impact and communicate status to stakeholders",
            "2. Consider rolling back recent deployments if timing correlates",
            "3. Increase monitoring verbosity / enable debug logging temporarily",
        ],
        "investigation_steps": [
            "1. Correlate metrics, logs, and infrastructure events",
            "2. Review recent changes: deployments, config changes, cron jobs",
            "3. Check dependencies: upstream APIs, databases, message queues",
        ],
        "resolution_steps": [
            "1. Apply fix and verify resolution via metrics",
            "2. Post status update to Slack and stakeholders",
            "3. Schedule post-mortem within 24-48 hours",
        ],
    },
}


def generate_runbook(
    incident_type: str = "unknown",
    severity: str = "P2",
    affected_services: list[str] | None = None,
    affected_hosts: list[str] | None = None,
    custom_context: str = "",
) -> dict[str, Any]:
    """
    Generate a structured incident runbook.

    Args:
        incident_type: Type of incident (e.g. 'memory_leak', 'high_cpu', 'database_issue')
        severity: Incident severity: 'P1', 'P2', 'P3', 'P4'
        affected_services: List of affected service names
        affected_hosts: List of affected host/instance names
        custom_context: Additional context to include in the runbook

    Returns a structured runbook dict with triage, mitigation, investigation, and resolution steps.
    """
    template = RUNBOOK_TEMPLATES.get(incident_type, RUNBOOK_TEMPLATES["unknown"])
    services_str = ", ".join(affected_services or []) or "Unknown"
    hosts_str = ", ".join(affected_hosts or []) or "Unknown"

    sla_map = {"P1": "15 minutes", "P2": "1 hour", "P3": "4 hours", "P4": "Next business day"}
    sla = sla_map.get(severity, "1 hour")

    runbook = {
        "title": template["title"],
        "metadata": {
            "severity": severity,
            "sla_response_time": sla,
            "incident_type": incident_type,
            "affected_services": affected_services or [],
            "affected_hosts": affected_hosts or [],
        },
        "context_summary": (
            f"Severity: {severity} | SLA: {sla} | "
            f"Services: {services_str} | Hosts: {hosts_str}"
            + (f" | {custom_context}" if custom_context else "")
        ),
        "phases": {
            "1_triage": {
                "goal": "Confirm the incident and understand its scope",
                "steps": template["triage_steps"],
            },
            "2_mitigation": {
                "goal": "Reduce user impact as fast as possible",
                "steps": template["mitigation_steps"],
            },
            "3_investigation": {
                "goal": "Find the root cause",
                "steps": template["investigation_steps"],
            },
            "4_resolution": {
                "goal": "Fix and close the incident",
                "steps": template["resolution_steps"],
            },
        },
        "communication_template": (
            f"*[{severity} INCIDENT]* {template['title']}\n"
            f"• *Affected:* {services_str}\n"
            f"• *Hosts:* {hosts_str}\n"
            f"• *Status:* Investigating\n"
            f"• *SLA:* Resolve within {sla}\n"
            f"• *Next update:* In 15 minutes"
        ),
        "available_incident_types": list(RUNBOOK_TEMPLATES.keys()),
    }

    return runbook
