# rundeck-yc-scheduler

[![Build](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/build.yml/badge.svg)](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/build.yml)
[![E2E Tests](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/e2e.yml/badge.svg)](https://github.com/itruslan/rundeck-yc-scheduler/actions/workflows/e2e.yml)

Custom [Rundeck](https://www.rundeck.com/) Docker image with a built-in plugin for scheduled start/stop of [Yandex Cloud](https://yandex.cloud/) resources. Save money by automatically shutting down non-production environments outside business hours.

## Features

- **Custom Rundeck image** — based on `rundeck/rundeck`, pre-loaded with `yandexcloud` SDK and three built-in plugins: `yc-node-source`, `yc-start`, `yc-stop`
- **Dynamic node discovery** — the plugin queries a YC folder via API and returns resources as Rundeck nodes
- **Scheduled start/stop** — cron-based jobs to stop resources in the evening and start them in the morning
- **Idempotent operations** — scripts check resource status before acting, safe to run multiple times
- **Terraform module** — manage projects, jobs, schedules, and ACL policies as code
- **Per-resource-type control** — independent schedules and execution order for each resource type
- **Exclude by label** — add `no_autoshutdown: "true"` to any resource to skip it

## How It Works

```text
┌───────────────────────────────────────────────────────────┐
│  Rundeck                                                  │
│                                                           │
│   Scheduler (cron)                                        │
│       │                                                   │
│       ▼                                                   │
│   ┌──────────────────────┐     ┌──────────────────────┐   │
│   │  yc-node-source      │     │  yc-stop / yc-start  │   │
│   │  (ResourceModel      │────▶│  (WorkflowNodeStep   │   │
│   │   Source plugin)     │     │   plugins)           │   │
│   │  Discovers resources │     │  Stops/starts each   │   │
│   │  as Rundeck nodes    │     │  node via YC API     │   │
│   └──────────┬───────────┘     └──────────┬───────────┘   │
│              │                            │               │
└──────────────┼────────────────────────────┼───────────────┘
               │                            │
               ▼                            ▼
        ┌──────────────┐            ┌──────────────────┐
        │  Yandex Cloud│            │  Yandex Cloud    │
        │  List API    │            │  Stop/Start API  │
        └──────────────┘            └──────────────────┘
```

1. **yc-node-source** queries a YC folder and returns all supported resources as Rundeck nodes with attributes (`resource_type`, `resource_id`, `status`, labels)
2. **Scheduled Jobs** run against discovered nodes, executing `yc-stop` or `yc-start` plugin per node
3. **Plugins** are idempotent — they check the current status and skip resources already in the desired state

## Supported Resource Types

| Type | Description | Status |
| --- | --- | --- |
| `compute-instance` | Virtual machines | Tested |
| `managed-postgresql` | Managed PostgreSQL clusters | Tested |
| `managed-kubernetes` | Managed Kubernetes clusters | Tested |
| `network-load-balancer` | Network load balancers | Implemented |

## Quick Start

### 1. Build the image

```bash
docker build -t rundeck-yc-scheduler:5.19.0 .
```

### 2. Run Rundeck

See [Docker deployment guide](examples/deployment/docker/) for `docker run` and Docker Compose options.

### 3. Configure projects and jobs

Choose one:

- [Terraform module](examples/configuration/terraform-rundeck-yc-scheduler/) — recommended, manages projects, jobs, schedules and ACL as code
- [Manual setup via Rundeck UI](examples/configuration/manual-rundeck/) — step-by-step guide through the web interface

## Components

| Path | Description |
| --- | --- |
| `Dockerfile` | Custom Rundeck image — base + Python + yandexcloud SDK + plugin |
| `plugin/` | Rundeck ScriptPlugin: `yc-node-source`, `yc-start`, `yc-stop` |
| `examples/deployment/` | Docker and Ansible deployment guides |
| `examples/configuration/` | Terraform module and manual Rundeck setup |

## Authentication

The image uses Yandex Cloud Service Account keys for authentication.

**Prepare a key:**

```bash
yc iam key create --service-account-name <sa-name> --output sa-key.json
base64 -i sa-key.json | tr -d '\n'
```

The service account needs permissions to start/stop the managed resources in the target folder.
See [Yandex Cloud role reference](https://yandex.cloud/en/docs/iam/roles-reference) for details on roles and bindings.

## Development

```bash
# Python (for IDE support and linting)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

# Pre-commit hooks
pre-commit install

# Tests
uv pip install -r requirements-dev.txt
pytest

# Build
docker build -t rundeck-yc-scheduler:5.19.0 .
```
