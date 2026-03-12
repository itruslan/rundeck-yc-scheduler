#!/usr/bin/env bash
# Reusable YC CLI helper functions for E2E tests.
# Source this file: source tests/e2e/yc.sh

# _yc_get_cmd <resource-type>
# Prints the "yc ... get" command prefix for the given resource type.
_yc_get_cmd() {
  case "$1" in
    compute-instance)          echo "yc compute instance get" ;;
    managed-postgresql)        echo "yc managed-postgresql cluster get" ;;
    managed-kubernetes)        echo "yc managed-kubernetes cluster get" ;;
    network-load-balancer)     echo "yc load-balancer network-load-balancer get" ;;
    managed-kafka)             echo "yc managed-kafka cluster get" ;;
    application-load-balancer) echo "yc alb load-balancer get" ;;
    managed-redis)             echo "yc managed-redis cluster get" ;;
    managed-clickhouse)        echo "yc managed-clickhouse cluster get" ;;
    managed-mysql)             echo "yc managed-mysql cluster get" ;;
    *) echo "Unknown resource type: $1" >&2; return 1 ;;
  esac
}

# _yc_ready_status <resource-type>
# Prints the status string that means "resource is operational".
_yc_ready_status() {
  case "$1" in
    network-load-balancer|application-load-balancer) echo "ACTIVE" ;;
    *) echo "RUNNING" ;;
  esac
}

# wait_running <resource-type> <id> [max-attempts] [sleep-seconds]
# Polls until the resource reaches its ready status (RUNNING or ACTIVE).
# Defaults: max-attempts=60, sleep-seconds=15
wait_running() {
  local type="$1" id="$2" max="${3:-60}" sleep_s="${4:-15}"
  local cmd ready STATUS
  cmd=$(_yc_get_cmd "$type") || return 1
  ready=$(_yc_ready_status "$type")
  for i in $(seq 1 "$max"); do
    STATUS=$($cmd --id "$id" --format json | jq -r '.status')
    echo "[$i/$max] status: $STATUS"
    if [ "$STATUS" = "$ready" ]; then return 0; fi
    sleep "$sleep_s"
  done
  echo "Timed out waiting for $ready"
  return 1
}

# wait_backup <resource-type> <id> [max-attempts] [sleep-seconds]
# Triggers a manual backup and polls until it reaches status DONE.
# Supported types: managed-postgresql, managed-mysql
# Defaults: max-attempts=30, sleep-seconds=20
wait_backup() {
  local type="$1" id="$2" max="${3:-30}" sleep_s="${4:-20}"
  local backup_cmd list_cmd STATUS
  case "$type" in
    managed-postgresql)
      backup_cmd="yc managed-postgresql cluster backup"
      list_cmd="yc managed-postgresql backup list"
      ;;
    managed-mysql)
      backup_cmd="yc managed-mysql cluster backup"
      list_cmd="yc managed-mysql backup list"
      ;;
    *)
      echo "Backup not supported for resource type: $type" >&2
      return 1
      ;;
  esac
  $backup_cmd --id "$id"
  for i in $(seq 1 "$max"); do
    STATUS=$($list_cmd --format json | jq -r --arg id "$id" \
      '[.[] | select(.source_cluster_id==$id and .status=="DONE")][0].status // "NONE"')
    echo "[$i/$max] backup status: $STATUS"
    if [ "$STATUS" = "DONE" ]; then echo "Backup ready"; return 0; fi
    sleep "$sleep_s"
  done
  echo "Timed out waiting for backup"
  return 1
}

# verify_status <resource-type> <id> <expected> [max-attempts] [sleep-seconds]
# Checks (or polls until) the resource status equals <expected>.
# With max-attempts=1 (default) performs a single immediate check.
# Defaults: max-attempts=1, sleep-seconds=15
verify_status() {
  local type="$1" id="$2" expected="$3" max="${4:-1}" sleep_s="${5:-15}"
  local cmd STATUS
  cmd=$(_yc_get_cmd "$type") || return 1
  for i in $(seq 1 "$max"); do
    STATUS=$($cmd --id "$id" --format json | jq -r '.status')
    echo "[$i/$max] status: $STATUS"
    if [ "$STATUS" = "$expected" ]; then return 0; fi
    [ "$i" -lt "$max" ] && sleep "$sleep_s"
  done
  echo "Expected $expected, got $STATUS"
  return 1
}
