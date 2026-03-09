# rundeck-yc-scheduler

[![Build](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/build.yml/badge.svg)](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/build.yml)
[![E2E Tests](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/e2e.yml/badge.svg)](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/e2e.yml)

Scheduled start/stop of Yandex Cloud resources via [Rundeck](https://www.rundeck.com/). Cut costs on non-production environments without changing your infrastructure.

## Supported resource types

- `compute-instance`
- `managed-postgresql`
- `managed-kubernetes`
- `network-load-balancer`

## Planned

- `application-load-balancer`
- `managed-valkey`
- `managed-kafka`
- `managed-mysql`
- `managed-opensearch`

## Quick start

### 1. Pull or build the image

```bash
docker pull ghcr.io/itruslan/rundeck-yc-scheduler:latest
# or build locally
docker build -t rundeck-yc-scheduler .
```

### 2. Run Rundeck

See [Docker deployment guide](examples/deployment/docker/) or [Ansible role](examples/deployment/ansible/).

### 3. Configure projects and jobs

- [Terraform module](examples/configuration/terraform-rundeck-yc-scheduler/) — recommended
- [Manual setup via UI](examples/configuration/manual-rundeck/) — step-by-step guide

## How it works

```text
                     ┌──────────────────────────────────────────┐
                     │  Rundeck                                 │
                     │                                          │
                     │  cron schedule                           │
                     │       │                                  │
                     │       ▼                                  │
                     │  yc-node-source          yc-stop/start   │
                     │  ┌─────────────────┐    ┌─────────────┐  │
                     │  │ lists resources │───▶│ calls YC API│  │
                     │  │ as Rundeck nodes│    │ per node    │  │
                     │  └────────┬────────┘    └──────┬──────┘  │
                     └───────────┼───────────────────┼──────────┘
                                 │                   │
                                 ▼                   ▼
                          YC List API         YC Stop/Start API
```

Rundeck discovers resources in a YC folder via `yc-node-source`, then `yc-stop` / `yc-start` execute against each node on a cron schedule. All operations are idempotent — resources already in the target state are skipped. Per-resource-type schedules are managed via the Terraform module.

## Development

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
pre-commit install

pytest          # unit tests
docker build .  # build image
```
