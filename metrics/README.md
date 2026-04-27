
# Monitoring Stack Overview

This monitoring stack collects **API logs** and **infrastructure metrics** for visualization in Grafana.

## Stack Components (Central)

| Component         | Role                                      | How it's monitored           |
|-------------------|-------------------------------------------|------------------------------|
| OpenTelemetry     | Receives logs from all nodes, forwards to Loki | Metrics via Prometheus   |
| Loki              | Stores and serves logs (all nodes)         | Metrics via Prometheus       |
| Prometheus        | **Central metrics backend** (scrapes central services and receives remote_write from nodes) | Self-scraped |
| Grafana           | Visualizes logs (Loki) and metrics (Prometheus) | -                            |

## Per-Node Components (also run on central)

| Component    | Role                                      |
|--------------|-------------------------------------------|
| REST API (nodes)  | Sends logs to OpenTelemetry Collector      | 
| node-exporter | Host hardware/OS metrics                   |
| cAdvisor     | Container metrics                          |
| Prometheus Agent | Scrapes local exporters, remote_write to central Prometheus |

## Architecture

- The monitoring services run on a dedicated external Docker network named `metrics_network`. The REST API and Apache joins the same network, so it can send logs directly to the OpenTelemetry Collector container by name.

| web_network  | Both           |  metrics_network |
|--------------|----------------|------------------|
| MDDB stack | REST API, Apache | Monitoring stack |

- **API Logs:**  
   The REST API sends logs directly to the shared [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) over the `REST_OTEL_ENDPOINT`, which forwards them to a central [Loki](https://grafana.com/oss/loki/) instance.
- **Infrastructure Metrics:**  
   [Prometheus](https://prometheus.io/) scrapes metrics from:
   - **Loki** (log system health)
   - **node-exporter** (host hardware/OS metrics)
   - **Prometheus itself**
   - **cAdvisor** (container metrics)
- **Visualization:**  
   [Grafana](https://grafana.com/) connects to both Loki (for logs) and Prometheus (for metrics).

```
------------------- Node ----------------------   ------------------ Central ---------------------
                   REST API ──────────────────────► OTel Collector ───► Loki ────────┐
node-exporter (host metrics) ─┐                                                      ├──► Grafana
                              ├─ Prometheus ──────────────────────────► Prometheus ──┘
cAdvisor (container metrics) ─┘ (remote_write)
```

## Setup

### Central Machine (Monitoring Host)

1. **Create the metrics network:**
    ```bash
    docker network create metrics_network 2>/dev/null
    ```
2. **Start the monitoring stack:**
    ```bash
    docker-compose -f central/docker-compose.yml up -d
    ```

### Per-Node Setup

1. **Configure your environment variables**:

| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `OTEL_ENDPOINT` | `http://otel-collector:4318/v1/logs` | REST API logs destination (OTLP/HTTP endpoint) | `http://central-ip:4318/v1/logs` or `https://central-ip:4318/v1/logs` |
| `PROMETHEUS_MODE` | `central` | Prometheus deployment mode (central or node) | `central` or `node` |

2. For nodes modify the `external_labels` in `prometheus-node.yml` to include unique identifiers for each node. This will help differentiate metrics from different nodes in Grafana.

3. **Start the node monitoring stack** on each node:
    ```bash
    docker-compose -f node/docker-compose.yml up -d
    ```
---

## Useful Commands

```bash
# Check Prometheus targets (Loki, node-exporter, cAdvisor, itself):
curl http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets'

# Check Loki health:
curl http://127.0.0.1:3100/ready

# Check Prometheus disk usage:
docker exec -it prometheus du -sh /prometheus

# Check logs for errors:
docker logs prometheus 2>&1 | grep -i "error"
docker logs loki 2>&1 | grep -i "error"
docker logs otel-collector 2>&1 | grep -i "error"
```