# rundeck-yc-scheduler

[![Build](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/build.yml/badge.svg)](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/build.yml)
[![E2E Tests](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/e2e.yml/badge.svg)](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/e2e.yml)

Scheduled start/stop of [Yandex Cloud](https://yandex.cloud/) resources via [Rundeck](https://www.rundeck.com/). Cut costs on non-production environments without changing your infrastructure.

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
                     └───────────┼────────────────────┼─────────┘
                                 │                    │
                                 ▼                    ▼
                            YC List API       YC Stop/Start API
```

Resources in a YC folder are discovered via `yc-node-source` and exposed as Rundeck nodes. You then create scheduled jobs using `yc-stop` / `yc-start` that target:

- a single resource
- a group of resources filtered by type or YC label
- an entire YC folder

All operations are idempotent — resources already in the target state are skipped. Each job executes per node, with optional parallelism configured at the job level. Label-based node filters let you exclude specific resources from a job without changing infrastructure (e.g. tag a resource `no_shutdown: "true"` and filter it out).

## Supported resource types

| Type | Status | Since |
| --- | --- | --- |
| `compute-instance` | ✅ done | 0.1.0 |
| `managed-postgresql` | ✅ done | 0.1.0 |
| `managed-kubernetes` | ✅ done | 0.1.0 |
| `network-load-balancer` | ✅ done | 0.1.0 |
| `application-load-balancer` | 🔜 planned | — |
| `managed-valkey` | 🔜 planned | — |
| `managed-kafka` | 🔜 planned | — |
| `managed-mysql` | 🔜 planned | — |
| `managed-opensearch` | 🔜 planned | — |

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

## Ideas & future work

- **OAuth for Rundeck** — bundle [rundeck-oauth](https://github.com/geraldhansen/rundeck-oauth) into the image as a ready-to-use example with Yandex ID / corporate SSO
- **More resource types** — application-load-balancer, managed-valkey, managed-kafka, managed-mysql, managed-opensearch (see table above)
- **Notification step plugin** — post to Slack / Telegram when a scheduled job stops or starts a resource
- **Dry-run mode** — log what would be stopped/started without actually calling the API, useful for auditing schedules
- **Configurable operation timeout** — expose `operation_timeout` as a Rundeck job option so users can tune wait time per job without rebuilding the image
- **Kubernetes deployment example** — add `examples/deployment/kubernetes/` with Deployment, Service, ConfigMap, Secret, and PVC manifests alongside the existing Docker and Ansible examples

## Development

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
pre-commit install

pytest          # unit tests
docker build .  # build image
```
