"""
Demo App — Incident Response Autopilot
=======================================
Simule une vraie application de paiements avec:
- Metriques Prometheus (CPU, Memory, HTTP, Latency)
- Logs JSON structures
- Endpoints pour declencher des incidents reels

Endpoints de simulation:
  POST /simulate/cpu-spike      → CPU monte a 95%
  POST /simulate/memory-leak    → Memory monte progressivement
  POST /simulate/high-errors    → 60% des requetes retournent des erreurs
  POST /simulate/slow-response  → Latence monte a 4-5 secondes
  POST /simulate/reset          → Retour a la normale
  GET  /status                  → Etat actuel des simulations
"""
import json
import logging
import math
import random
import sys
import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

# ─── Logging JSON structure (lu par Promtail → Loki) ──────────────────────────
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service": "payments-api",
            "host": "prod-server-01",
            "logger": record.name,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("payments-api")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.propagate = False

# ─── Prometheus Metrics ────────────────────────────────────────────────────────
cpu_gauge        = Gauge("demo_cpu_usage_percent",    "Simulated CPU usage in %")
memory_gauge     = Gauge("demo_memory_usage_percent", "Simulated memory usage in %")
response_gauge   = Gauge("demo_response_time_seconds","Simulated HTTP response time in seconds")
incident_gauge   = Gauge("demo_incident_active",      "1 if an incident is active", ["type"])
http_counter     = Counter("demo_http_requests_total", "HTTP requests", ["method", "endpoint", "status"])

# Init incident gauges to 0
for inc_type in ["cpu_spike", "memory_leak", "high_errors", "slow_response"]:
    incident_gauge.labels(type=inc_type).set(0)

# ─── Simulation State ──────────────────────────────────────────────────────────
state = {
    "cpu_spike":     False,
    "memory_leak":   False,
    "high_errors":   False,
    "slow_response": False,
    "memory_level":  30.0,  # tracks progressive memory growth
}
state_lock = threading.Lock()

# ─── Background metrics updater ───────────────────────────────────────────────
def update_metrics():
    """Continuously updates Prometheus metrics based on simulation state."""
    tick = 0
    while True:
        with state_lock:
            s = dict(state)

        # CPU
        if s["cpu_spike"]:
            cpu = 92 + random.uniform(-3, 5)
            logger.error("CPU saturation detected: %.1f%% — process 'payments-worker' consuming all cores", cpu)
        else:
            cpu = 25 + 10 * math.sin(tick / 30) + random.uniform(-3, 3)

        # Memory
        if s["memory_leak"]:
            with state_lock:
                state["memory_level"] = min(state["memory_level"] + 0.4, 97)
            mem = state["memory_level"] + random.uniform(-1, 1)
            if int(mem) % 5 == 0:
                logger.error(
                    "OOM pressure: memory at %.1f%% — heap growing unchecked in PaymentProcessor",
                    mem,
                )
        else:
            with state_lock:
                state["memory_level"] = max(state["memory_level"] - 0.5, 30.0)
            mem = state["memory_level"] + random.uniform(-2, 2)

        # Response time
        if s["slow_response"]:
            rt = 3.5 + random.uniform(0.5, 2.0)
            logger.warning("Slow DB query detected: %.2fs — SELECT * FROM transactions WHERE ...", rt)
        else:
            rt = 0.15 + random.uniform(0, 0.3)

        # HTTP counters
        if s["high_errors"]:
            for _ in range(random.randint(3, 7)):
                http_counter.labels(method="POST", endpoint="/payments", status="error").inc()
                logger.error(
                    "Payment processing failed: ConnectionError — upstream DB unreachable (attempt %d/3)",
                    random.randint(1, 3),
                )
            for _ in range(random.randint(1, 3)):
                http_counter.labels(method="POST", endpoint="/payments", status="success").inc()
        else:
            for _ in range(random.randint(5, 15)):
                http_counter.labels(method="POST", endpoint="/payments", status="success").inc()
            if random.random() < 0.05:
                http_counter.labels(method="POST", endpoint="/payments", status="error").inc()
                logger.warning("Transient payment error — retrying")

        # Set gauges
        cpu_gauge.set(max(0, min(100, cpu)))
        memory_gauge.set(max(0, min(100, mem)))
        response_gauge.set(max(0, rt))

        # Incident flags
        incident_gauge.labels(type="cpu_spike").set(1 if s["cpu_spike"] else 0)
        incident_gauge.labels(type="memory_leak").set(1 if s["memory_leak"] else 0)
        incident_gauge.labels(type="high_errors").set(1 if s["high_errors"] else 0)
        incident_gauge.labels(type="slow_response").set(1 if s["slow_response"] else 0)

        # Normal heartbeat log
        if tick % 20 == 0:
            logger.info(
                "Health check OK — cpu=%.1f%% memory=%.1f%% latency=%.3fs",
                cpu, mem, rt,
            )

        tick += 1
        time.sleep(2)


threading.Thread(target=update_metrics, daemon=True).start()

# ─── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)  # silence Flask access logs


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "payments-api"})


@app.route("/status")
def status():
    with state_lock:
        active = [k for k, v in state.items() if isinstance(v, bool) and v]
    return jsonify({
        "service": "payments-api",
        "active_incidents": active,
        "incident_count": len(active),
        "status": "DEGRADED" if active else "HEALTHY",
    })


# ─── Simulation Endpoints ──────────────────────────────────────────────────────
@app.route("/simulate/cpu-spike", methods=["POST"])
def sim_cpu():
    with state_lock:
        state["cpu_spike"] = True
    logger.error("INCIDENT TRIGGERED: CPU spike simulation started — payments-worker thread stuck in infinite loop")
    return jsonify({"incident": "cpu_spike", "status": "triggered", "message": "CPU spike active — alerts will fire in ~30s"})


@app.route("/simulate/memory-leak", methods=["POST"])
def sim_memory():
    with state_lock:
        state["memory_leak"] = True
        state["memory_level"] = 50.0
    logger.error("INCIDENT TRIGGERED: Memory leak simulation started — PaymentProcessor cache not releasing objects")
    return jsonify({"incident": "memory_leak", "status": "triggered", "message": "Memory growing progressively — alerts will fire in ~30s"})


@app.route("/simulate/high-errors", methods=["POST"])
def sim_errors():
    with state_lock:
        state["high_errors"] = True
    logger.error("INCIDENT TRIGGERED: High error rate simulation — DB connection pool exhausted")
    return jsonify({"incident": "high_errors", "status": "triggered", "message": "60%% error rate active — alerts will fire in ~30s"})


@app.route("/simulate/slow-response", methods=["POST"])
def sim_slow():
    with state_lock:
        state["slow_response"] = True
    logger.warning("INCIDENT TRIGGERED: Slow response simulation — missing index on transactions table")
    return jsonify({"incident": "slow_response", "status": "triggered", "message": "Response time >3s active — alerts will fire in ~30s"})


@app.route("/simulate/reset", methods=["POST"])
def sim_reset():
    with state_lock:
        state["cpu_spike"]     = False
        state["memory_leak"]   = False
        state["high_errors"]   = False
        state["slow_response"] = False
    logger.info("All incidents resolved — system returning to normal baseline")
    return jsonify({"status": "reset", "message": "All incidents cleared — metrics returning to normal"})


if __name__ == "__main__":
    logger.info("payments-api starting on port 8080 — Incident Response Autopilot Demo")
    app.run(host="0.0.0.0", port=8080)
