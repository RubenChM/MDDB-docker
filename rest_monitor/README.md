
This monitoring stack can be mounted in two common ways:

1. Central Pull (Scraping): a central Prometheus scrapes metrics directly from all nodes.
2. Federated Push (Remote Write): each node runs local scraping and pushes metrics to a central Prometheus.

| Feature | Central Pull (Scraping) | Federated Push (Remote Write) |
| --- | --- | --- |
| Best For | Small clusters, same network. | Large scale, multi-region, hybrid cloud. |
| Firewall Rule | Inbound to Nodes (Riskier) | Outbound from Nodes (Safer) |
| Data Integrity | Lost during network outages. | Buffered during network outages. |
| Setup Speed | Very Fast (One config). | Slower (Multiple configs). |
| Scalability | Vertical (Bigger central server). | Horizontal (Add more nodes). |
| Replicas | Works best when each replica is scraped directly; **scraping one load-balanced URL can mix/reset counters**. | Local Prometheus can scrape all replicas and remote_write per-replica series to central Prometheus. |

# Federated Push (Remote Write)

Monitoring architecture:
```
Node 1  [node-exporter → prometheus] ─── remote_write ──┐
Node 2  [node-exporter → prometheus] ─── remote_write ──┼──► Central Prometheus ──► Grafana
Node N  [node-exporter → prometheus] ─── remote_write ──┘
```

## Central Prometheus

Deploy this on a central monitoring server. It runs a single container:

- **prometheus**: receives metrics from all node Prometheus instances via `remote_write` and stores them in its time-series database. Grafana will query this Prometheus for all metrics.

## Node Prometheus

Deploy this on every monitored node. It runs two containers:

- [**node-exporter**](https://github.com/prometheus/node_exporter): exposes hardware and OS metrics (CPU, memory, disk, network) from the host machine.
- **prometheus**: scrapes node-exporter and metrics from the **swagger-stats** API endpoint every 5 minutes and forwards all metrics to the central Prometheus via `remote_write`.

```
[host machine] → node-exporter :9100 ──► prometheus :9091 ── remote_write ──► central Prometheus
               API /metrics endpoint ──► prometheus :9091 ─┘
```

Each node tags its metrics with a unique `node` label (set in `prometheus.yml` under `external_labels`), so all nodes can be distinguished in Grafana.

### Setup

1. Edit `prometheus.yml`:
   - Set `external_labels.node` to a unique name for this machine (e.g. `node1`).
   - Set the `remote_write` URL to the central Prometheus IP.

2. Start:
   ```bash
   docker network create web_network 2>/dev/null
   docker-compose up -d
   ```

# Useful commands

```bash
# Check Prometheus is running and scraping targets:
curl http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets'

# Check disk usage:
docker exec -it prometheus-node du -sh /prometheus

# Check prometheus logs for remote_write errors
docker logs prometheus-node 2>&1 | grep -i "remote\|error\|write"

# Check cardinality of metrics:
curl -s http://localhost:9090/api/v1/status/tsdb | jq '.data'

# Check volume usage:
docker volume ls | grep prometheus
docker volume inspect central_prometheus_data | jq '.[0].Mountpoint' | xargs du -sh
```
