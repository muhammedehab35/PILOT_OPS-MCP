# PilotOps MCP ✈️

> **AI-powered Incident Response Autopilot for DevOps & SRE teams**

PilotOps is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that connects Claude AI to your monitoring stack — enabling automated incident detection, diagnosis, and response in natural language.

---

## What it does

When an incident fires, instead of manually jumping between Prometheus, Grafana, Loki, PagerDuty and Slack — you just tell Claude:

> *"There's an alert on prod, investigate and generate a runbook"*

Claude will automatically:
1. Fetch active alerts from **Prometheus**
2. Query relevant **metrics** (CPU, memory, latency, error rate)
3. Pull **logs** from Loki
4. **Correlate** all signals to diagnose the root cause
5. Generate a **step-by-step runbook**
6. Create a **PagerDuty incident** and page the on-call engineer
7. Post a **Slack notification** with communication template
8. Create a **Grafana annotation** for post-mortem analysis

---

## Architecture

```
Claude (AI) ←──→ PilotOps MCP Server ←──→ Prometheus / Grafana / Loki
                                      ←──→ PagerDuty / Slack
```

---

## Tools (12 MCP tools)

| Tool | Description |
|------|-------------|
| `prometheus_get_active_alerts` | Fetch all firing alerts |
| `prometheus_get_metrics` | Query PromQL metrics |
| `prometheus_silence_alert` | Silence an alert |
| `grafana_get_dashboards` | List dashboards |
| `grafana_create_annotation` | Mark incident on timeline |
| `loki_get_logs` | Fetch logs via LogQL |
| `pagerduty_get_incidents` | List open incidents |
| `pagerduty_create_incident` | Page on-call engineer |
| `pagerduty_update_incident` | Acknowledge or resolve |
| `slack_notify` | Notify the team |
| `analyze_incident` | AI correlation engine |
| `generate_runbook` | Auto-generate runbook |

---

## Supported Incident Types

- `memory_leak` — OOM / memory pressure
- `high_cpu` — CPU saturation
- `disk_full` — Disk space exhaustion
- `network_issue` — Connectivity / latency
- `database_issue` — Slow queries / deadlocks
- `service_crash` — Application crash / restart loop
- `deployment_issue` — Failed Kubernetes rollout

---

## Stack

- **Python 3.11+**
- **MCP SDK** (FastMCP)
- **Prometheus** — metrics & alerting
- **Grafana** — dashboards & annotations
- **Loki** — log aggregation
- **PagerDuty** — incident management
- **Slack** — team notifications

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/pilotops-mcp.git
cd pilotops-mcp
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

```env
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=your_grafana_api_key
LOKI_URL=http://localhost:3100
PAGERDUTY_API_KEY=your_pagerduty_key
SLACK_BOT_TOKEN=xoxb-your-slack-token
```

### 3. Start the demo stack (Docker)

```bash
cd docker
docker-compose up -d
```

Services:
| Service | URL |
|---------|-----|
| Demo App | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin123) |
| Loki | http://localhost:3100 |
| Alertmanager | http://localhost:9093 |

### 4. Simulate an incident

```bash
# Trigger a CPU spike
curl -X POST http://localhost:8080/simulate/cpu-spike

# Trigger a memory leak
curl -X POST http://localhost:8080/simulate/memory-leak

# Trigger high error rate
curl -X POST http://localhost:8080/simulate/high-errors

# Reset everything
curl -X POST http://localhost:8080/simulate/reset
```

### 5. Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pilotops": {
      "command": "python",
      "args": ["/path/to/pilotops-mcp/server.py"],
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

Restart Claude Desktop → look for the 🔨 hammer icon.

### 6. Ask Claude

> *"There's an active alert on prod, investigate and generate a runbook"*

---

## Project Structure

```
pilotops-mcp/
├── server.py              # MCP server entry point
├── config.py              # Environment configuration
├── requirements.txt
├── .env.example
├── tools/
│   ├── prometheus.py      # Alerts, metrics, silences
│   ├── grafana.py         # Dashboards, annotations
│   ├── loki.py            # Log queries
│   ├── pagerduty.py       # Incident management
│   └── slack.py           # Notifications
├── core/
│   ├── correlator.py      # Incident correlation engine
│   └── runbook.py         # Runbook generator
└── docker/
    ├── docker-compose.yml
    ├── demo-app/          # Simulated app with incident endpoints
    ├── prometheus/
    ├── grafana/
    ├── loki/
    ├── promtail/
    └── alertmanager/
```

---

## License

MIT
