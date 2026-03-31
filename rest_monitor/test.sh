#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'USAGE'
Usage: ./test.sh <start|stop|restart|status>

Examples:
  ./test.sh start
  ./test.sh restart
USAGE
}

ACTION="${1:-}"

if [[ -z "${ACTION}" ]]; then
    usage
    exit 1
fi

compose_file="${SCRIPT_DIR}/docker-compose.yml"

case "${ACTION}" in
    start)
        docker compose -f "${compose_file}" up -d
        ;;
    stop)
        docker compose -f "${compose_file}" down
        ;;
    restart)
        docker compose -f "${compose_file}" restart
        ;;
    status)
        echo "[status] Prometheus targets (should include loki, node-exporter, cadvisor, prometheus):"
        if command -v jq >/dev/null 2>&1; then
            curl -fsS "http://127.0.0.1:9090/api/v1/targets" | jq '.data.activeTargets'
        else
            curl -fsS "http://127.0.0.1:9090/api/v1/targets"
        fi

        echo "[status] Loki health:"
        curl -fsS "http://127.0.0.1:3100/ready" || echo "Loki not ready"

        echo "[status] Prometheus disk usage:"
        docker exec -it prometheus du -sh /prometheus

        echo "[status] Loki disk usage:"
        docker exec -it loki du -sh /loki

        echo "[status] Prometheus logs (errors):"
        docker logs prometheus 2>&1 | grep -i "error" || true

        echo "[status] Loki logs (errors):"
        docker logs loki 2>&1 | grep -i "error" || true

        echo "[status] OpenTelemetry Collector logs (errors):"
        docker logs otel-collector 2>&1 | grep -i "error" || true
        ;;
    *)
        usage
        exit 1
        ;;
esac

# scp -r * mddbr_dev:/home/rchaves/rest_monitor/