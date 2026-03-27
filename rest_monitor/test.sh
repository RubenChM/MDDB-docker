#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'USAGE'
Usage: ./test.sh <central|c|node|n> <start|stop|restart|status>

Examples:
  ./test.sh central start
  ./test.sh c restart
  ./test.sh node stop
USAGE
}

MODE="${1:-}"
ACTION="${2:-}"

if [[ -z "${MODE}" || -z "${ACTION}" ]]; then
    usage
    exit 1
fi

if [[ "${MODE}" == "central" || "${MODE}" == "c" || "${MODE}" == "node" || "${MODE}" == "n" ]]; then
    DIR="central"
    [[ "${MODE}" == "node" || "${MODE}" == "n" ]] && DIR="node"
    compose_file="${SCRIPT_DIR}/${DIR}/docker-compose.yml"

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
            if [[ "${DIR}" == "central" ]]; then
                PROM_HOST_PORT="9090"
                PROM_CONTAINER="prometheus-central"
            else
                PROM_HOST_PORT="9091"
                PROM_CONTAINER="prometheus-node"
            fi

            echo "[status] Active targets from localhost:${PROM_HOST_PORT}"
            if command -v jq >/dev/null 2>&1; then
                curl -fsS "http://127.0.0.1:${PROM_HOST_PORT}/api/v1/targets" | jq '.data.activeTargets'
            else
                curl -fsS "http://127.0.0.1:${PROM_HOST_PORT}/api/v1/targets"
            fi

            echo "[status] Prometheus disk usage (${PROM_CONTAINER})"
            docker exec -it "${PROM_CONTAINER}" du -sh /prometheus

            echo "[status] Prometheus logs filtered by remote/error/write (${PROM_CONTAINER})"
            docker logs "${PROM_CONTAINER}" 2>&1 | grep -i "remote\|error\|write" || true
            ;;
        *)
            usage
            exit 1
            ;;
    esac
else
    usage
    exit 1
fi
