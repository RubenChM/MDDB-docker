
# Monitoring Stack Overview

This monitoring stack collects **API logs** and **infrastructure metrics** for visualization in Grafana.

## Stack Components

| Component         | Role                                      | How it’s monitored           |
|-------------------|-------------------------------------------|------------------------------|
| REST API          | Sends logs to OpenTelemetry Collector      | Logs in Loki                 |
| OpenTelemetry     | Receives logs, forwards to Loki            | Metrics via Prometheus       |
| Loki              | Stores and serves logs                     | Metrics via Prometheus       |
| node-exporter     | Host hardware/OS metrics                   | Scraped by Prometheus        |
| cAdvisor          | Container metrics                          | Scraped by Prometheus        |
| Prometheus        | Scrapes metrics, serves to Grafana         | Self-scraped                 |
| Grafana           | Visualizes logs (Loki) and metrics         | -                            |

## Architecture

- The monitoring services run on a dedicated external Docker network named `metrics_network`.
- The REST API joins the same network, so it can send logs directly to the OpenTelemetry Collector container by name.

- **API Logs:**  
   The REST API sends logs directly to the shared [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) over the `metrics_network`, which forwards them to a local [Loki](https://grafana.com/oss/loki/) instance. (Future: also forward to a central Loki.)
- **Infrastructure Metrics:**  
   [Prometheus](https://prometheus.io/) scrapes metrics from:
   - **Loki** (log system health)
   - **node-exporter** (host hardware/OS metrics)
   - **Prometheus itself**
   - **cAdvisor** (container metrics)
- **Visualization:**  
   [Grafana](https://grafana.com/) connects to both Loki (for logs) and Prometheus (for metrics).

```
REST API ──► OpenTelemetry Collector ──► Loki ──► Grafana
                                                     ▲
                 node-exporter (host metrics) ─┐     │
                 cAdvisor (container metrics) ─┼► Prometheus
            Loki/Prometheus (service metrics) ─┘ 
```

## Key Features

- **API logs** are structured and searchable in Grafana via Loki.
- **Metrics** (CPU, memory, disk, etc.) are available in Grafana via Prometheus.
- **No Prometheus scraping of API logs**: all API request logs flow through OpenTelemetry → Loki.
- **Future-proof**: OpenTelemetry Collector can be configured to forward logs to a central Loki for multi-node setups.

---

## Setup

1. **Edit configuration files as needed:**
    - `otel.yaml`: Set the node name under the `resource` processor, e.g. `value: "IRB-DEV"`.
    - `prometheus.yml`: Set `external_labels.node` to a unique name for this machine, e.g. `node: 'IRB-DEV'`.

2. **Start the stack:**
    ```bash
   docker network create metrics_network 2>/dev/null
   docker compose up -d
    ```

3. **Configure your API** to join `metrics_network` and send logs to the OpenTelemetry Collector endpoint (`http://otel-collector:4318/v1/logs`).

4. **If the API is deployed from the main MDDB compose file**, make sure that compose file also declares and joins the same `metrics_network`.

---

## Useful Commands

```bash
# Check Prometheus targets (Loki, node-exporter, cAdvisor, itself):
curl http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets'

# Check Loki health:
curl http://127.0.0.1:3100/ready

# Check Prometheus disk usage:
docker exec -it prometheus du -sh /prometheus

# Check Loki disk usage:
docker exec -it loki du -sh /loki

# Check logs for errors:
docker logs prometheus 2>&1 | grep -i "error"
docker logs loki 2>&1 | grep -i "error"
docker logs otel-collector 2>&1 | grep -i "error"
```
