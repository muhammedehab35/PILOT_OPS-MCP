<div align="center">

# ✈️ PilotOps MCP

### AI-powered Incident Response Autopilot for DevOps & SRE teams

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-blueviolet?style=for-the-badge)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Claude](https://img.shields.io/badge/Powered%20by-Claude%20AI-orange?style=for-the-badge)](https://anthropic.com)

[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=flat&logo=prometheus&logoColor=white)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)](https://grafana.com)
[![Loki](https://img.shields.io/badge/Loki-F5A623?style=flat&logo=grafana&logoColor=white)](https://grafana.com/oss/loki)
[![PagerDuty](https://img.shields.io/badge/PagerDuty-06AC38?style=flat&logo=pagerduty&logoColor=white)](https://pagerduty.com)
[![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white)](https://slack.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)

> Connect Claude AI to your entire monitoring stack and respond to incidents in natural language — no more jumping between 5 different tools at 3am.

</div>

---

## The Problem

When an incident fires at 3am, an SRE must manually:

| Step | Tool | Time |
|------|------|------|
| Check alerts | Prometheus | 2 min |
| Analyze metrics | Grafana | 5 min |
| Search logs | Loki / ELK | 10 min |
| Diagnose root cause | Brain | 15 min |
| Write runbook | Notion / Confluence | 10 min |
| Page on-call | PagerDuty | 2 min |
| Notify team | Slack | 2 min |
| **Total** | **7 tools** | **~46 min** |

## The Solution

With **PilotOps MCP**, you just tell Claude:

> *"There's an alert on prod, investigate and generate a runbook"*

And Claude handles everything in **under 2 minutes**.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                        You (Claude Desktop)                  │
│  "Investigate the active alert on prod-server-01"           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PilotOps MCP Server                       │
│                                                              │
│  1. prometheus_get_active_alerts()                          │
│     → CPU 95% on prod-server-01 since 10min                 │
│                                                              │
│  2. prometheus_get_metrics("node_cpu...")                    │
│     → Spike started at 22:15, still climbing                │
│                                                              │
│  3. loki_get_logs('{host="prod-server-01"}')                │
│     → 847 errors: "OOM Killer activated"                    │
│                                                              │
│  4. analyze_incident(alerts, metrics, logs)                  │
│     → P1 | Memory leak in payments-api | Confidence: HIGH   │
│                                                              │
│  5. generate_runbook("memory_leak", "P1")                   │
│     → 4-phase runbook generated                             │
│                                                              │
│  6. pagerduty_create_incident("P1: Memory leak")            │
│     → On-call engineer paged                                │
│                                                              │
│  7. slack_notify("#incidents", severity="critical")          │
│     → Team notified with communication template             │
│                                                              │
│  8. grafana_create_annotation("[P1 START] 22:15")           │
│     → Incident marked on all dashboards                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

- **12 MCP Tools** across 5 integrations
- **AI Correlation Engine** — matches alerts + metrics + logs against 7 incident patterns
- **Auto Runbook Generator** — produces 4-phase runbooks (Triage → Mitigation → Investigation → Resolution)
- **Slack Communication Templates** — ready-to-send status updates
- **Full Docker Demo Stack** — simulate real incidents locally with 1 command
- **Zero vendor lock-in** — works with any Prometheus-compatible stack

---

## Tools Reference

### Prometheus
| Tool | Description |
|------|-------------|
| `prometheus_get_active_alerts` | Fetch all firing alerts with severity, labels, and annotations |
| `prometheus_get_metrics` | Query any PromQL expression with time range |
| `prometheus_silence_alert` | Silence an alert for a specified duration |

### Grafana
| Tool | Description |
|------|-------------|
| `grafana_get_dashboards` | List and search available dashboards |
| `grafana_create_annotation` | Mark incident start/end on dashboards for post-mortem |

### Loki
| Tool | Description |
|------|-------------|
| `loki_get_logs` | Query logs via LogQL with level filtering and error detection |

### PagerDuty
| Tool | Description |
|------|-------------|
| `pagerduty_get_incidents` | List open incidents by status |
| `pagerduty_create_incident` | Create P1-P4 incident and page on-call |
| `pagerduty_update_incident` | Acknowledge or resolve with timeline note |

### Slack
| Tool | Description |
|------|-------------|
| `slack_notify` | Send color-coded alert with severity emoji |

### AI Core
| Tool | Description |
|------|-------------|
| `analyze_incident` | Correlates alerts + metrics + logs → root cause + confidence |
| `generate_runbook` | Generates structured 4-phase runbook with Slack template |

---

## Supported Incident Types

| Type | Trigger | Pattern |
|------|---------|---------|
| `memory_leak` | OOM kills, heap growth | Memory > 85% + OOM logs |
| `high_cpu` | CPU saturation | CPU > 80% sustained |
| `disk_full` | Disk space exhaustion | No space left errors |
| `network_issue` | Connectivity problems | Timeouts + packet loss |
| `database_issue` | DB overload / deadlocks | Slow queries + connection pool |
| `service_crash` | App crash / restart loop | Segfault + panic logs |
| `deployment_issue` | Failed K8s rollout | CrashLoopBackOff + ImagePull |

---

## Tech Stack

```
Language    : Python 3.11+
MCP Server  : FastMCP (official Anthropic SDK)
Metrics     : Prometheus + Alertmanager
Dashboards  : Grafana
Logs        : Loki + Promtail
Incidents   : PagerDuty
Alerts      : Slack
Containers  : Docker + Docker Compose
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Claude Desktop

### 1. Clone & install

```bash
git clone https://github.com/muhammedehab35/PILOT_OPS-MCP.git
cd PILOT_OPS-MCP
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

```env
# Minimum required for local demo
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=your_grafana_api_key
LOKI_URL=http://localhost:3100

# Optional: for full incident workflow
PAGERDUTY_API_KEY=your_pagerduty_key
PAGERDUTY_SERVICE_ID=PXXXXXX
SLACK_BOT_TOKEN=xoxb-your-slack-token
SLACK_DEFAULT_CHANNEL=#incidents
```

### 3. Launch the full demo stack

```bash
cd docker
docker-compose up -d
```

| Service | URL | Credentials |
|---------|-----|-------------|
| Demo App | http://localhost:8080 | — |
| Prometheus | http://localhost:9090 | — |
| Alertmanager | http://localhost:9093 | — |
| Grafana | http://localhost:3000 | admin / admin123 |
| Loki | http://localhost:3100 | — |

### 4. Trigger a real incident

```bash
# CPU spike → fires HighCPUUsage alert after 30s
curl -X POST http://localhost:8080/simulate/cpu-spike

# Memory leak → fires HighMemoryUsage alert after 30s
curl -X POST http://localhost:8080/simulate/memory-leak

# High error rate → fires HighErrorRate alert after 30s
curl -X POST http://localhost:8080/simulate/high-errors

# Slow responses → fires SlowResponseTime alert after 30s
curl -X POST http://localhost:8080/simulate/slow-response

# Reset all incidents
curl -X POST http://localhost:8080/simulate/reset
```

### 5. Connect to Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac):

```json
{
  "mcpServers": {
    "pilotops": {
      "command": "python",
      "args": ["/full/path/to/PILOT_OPS-MCP/server.py"],
      "env": {
        "PROMETHEUS_URL": "http://localhost:9090",
        "GRAFANA_URL": "http://localhost:3000",
        "GRAFANA_API_KEY": "your_key",
        "LOKI_URL": "http://localhost:3100",
        "PAGERDUTY_API_KEY": "your_key",
        "SLACK_BOT_TOKEN": "your_token"
      }
    }
  }
}
```

Restart Claude Desktop → look for the **🔨 hammer icon** in the chat bar.

### 6. Run your first incident response

```
You:     "There's an active alert on prod, investigate and generate a runbook"

Claude:  → Fetching active alerts from Prometheus...
         → Querying CPU and memory metrics...
         → Pulling last 15 minutes of error logs from Loki...
         → Analyzing correlation...
         → [P1] Memory leak detected in payments-api (confidence: HIGH)
         → Generating runbook...
         → Creating PagerDuty incident #42...
         → Notifying #incidents on Slack...
         ✅ Full incident response completed in 45 seconds.
```

---

## Project Structure

```
PILOT_OPS-MCP/
├── server.py                    # FastMCP server — registers all 12 tools
├── config.py                    # Pydantic settings — loads from .env
├── requirements.txt
├── .env.example
│
├── tools/                       # One file per integration
│   ├── prometheus.py            # get_alerts, get_metrics, silence
│   ├── grafana.py               # dashboards, annotations
│   ├── loki.py                  # log queries via LogQL
│   ├── pagerduty.py             # create / update incidents
│   └── slack.py                 # team notifications
│
├── core/                        # AI intelligence layer
│   ├── correlator.py            # Pattern-matching correlation engine
│   └── runbook.py               # 4-phase runbook generator (7 types)
│
└── docker/                      # Full local demo environment
    ├── docker-compose.yml
    ├── demo-app/                # Flask app — simulates real incidents
    │   ├── app.py               # /simulate/* endpoints + Prometheus metrics
    │   ├── Dockerfile
    │   └── requirements.txt
    ├── prometheus/
    │   ├── prometheus.yml       # Scrape config
    │   └── alerts.yml           # 5 alert rules
    ├── grafana/
    │   ├── provisioning/        # Auto-configured datasources
    │   └── dashboards/          # Pre-built infrastructure dashboard
    ├── loki/loki-config.yml
    ├── promtail/promtail-config.yml
    └── alertmanager/alertmanager.yml
```

---

## Example Runbook Output

```
📋 RUNBOOK: Memory Leak / OOM Incident
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Severity : P1  |  SLA: 15 minutes
Services : payments-api
Hosts    : prod-server-01

PHASE 1 — TRIAGE
  1. Confirm memory usage: free -h or Grafana memory dashboard
  2. Identify top memory consumers: ps aux --sort=-%mem | head -20
  3. Check OOM kills: dmesg | grep -i 'oom'

PHASE 2 — MITIGATION
  1. Restart the affected service to free memory immediately
  2. Enable memory limits (K8s: resources.limits.memory)
  3. Set up swap if not present

PHASE 3 — INVESTIGATION
  1. Collect heap dump (JVM: jmap, Go: pprof)
  2. Review recent code changes for memory regressions
  3. Check GC logs for anomalies

PHASE 4 — RESOLUTION
  1. Deploy fix or roll back the problematic version
  2. Verify memory returns to baseline
  3. Resolve PagerDuty + post-mortem

💬 SLACK TEMPLATE:
  [P1 INCIDENT] Memory Leak / OOM
  • Affected: payments-api
  • Hosts: prod-server-01
  • Status: Investigating
  • SLA: Resolve within 15 minutes
  • Next update: In 15 minutes
```

---

## Contributing

Contributions are welcome! Ideas for new integrations:

- [ ] OpsGenie support
- [ ] Datadog metrics
- [ ] Kubernetes events via kubectl
- [ ] Jira ticket creation
- [ ] Email notifications

---

## Author

**Ehab Muhammed** — DevOps Engineer
GitHub: [@muhammedehab35](https://github.com/muhammedehab35)

---

## License

MIT © 2024 Ehab Muhammed
