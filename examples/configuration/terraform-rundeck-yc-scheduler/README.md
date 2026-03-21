# Terraform Module: rundeck-yc-scheduler

Manages Rundeck projects and scheduled stop/start jobs for Yandex Cloud resources.

## What it creates

For each project in `var.projects`:

- **Rundeck project** pointed at a YC folder
- **SA key** uploaded to Key Storage at `keys/project/<name>/yc-sa-key`
- **ACL policy** so the node source plugin can read the key
- **Stop / Start jobs** — one pair per enabled resource type, plus a manual "Stop All / Start All" pair

## Usage

```hcl
module "rundeck" {
  source = "git::https://github.com/itruslan/rundeck-yc-scheduler.git//examples/configuration/terraform-rundeck-yc-scheduler?ref=v1.0.0"

  rundeck_url        = "http://localhost:4440"
  rundeck_auth_token = var.rundeck_auth_token

  projects = [
    {
      name      = "staging"
      folder_id = "b1g0abc123def456"
      yc_sa_key = var.yc_sa_key_staging

      stop_schedule  = "0 0 21 ? * MON-FRI *"
      start_schedule = "0 0 7 ? * MON-FRI *"
      time_zone      = "Europe/Moscow"

      resource_types = {
        "compute-instance" = {
          enabled    = true
          stop_order = 2
        }
        "managed-postgresql" = {
          enabled    = true
          stop_order = 1
        }
        "managed-kubernetes" = {
          enabled           = true
          stop_order        = 3
          operation_timeout = 900
        }
      }
    },
  ]
}
```

## Project parameters

| Parameter | Description | Required | Default |
| --- | --- | :---: | --- |
| `name` | Rundeck project name | ✅ | — |
| `folder_id` | Yandex Cloud folder ID | ✅ | — |
| `yc_sa_key` | Base64-encoded SA authorized key | | — |
| `display_name` | Project label shown in Rundeck UI | | same as `name` |
| `stop_schedule` | Quartz cron for stop jobs (see format below) | | no schedule |
| `start_schedule` | Quartz cron for start jobs | | no schedule |
| `time_zone` | Schedule time zone | | `Europe/Moscow` |
| `resource_types` | Map of resource types to manage (see below) | | `{}` |

## Resource type parameters

Each key in `resource_types` is a resource type string (e.g. `"compute-instance"`).

| Parameter | Description | Default |
| --- | --- | --- |
| `enabled` | Include this type in stop/start jobs | `false` |
| `stop_order` | Execution order across types — lower runs first | `1` |
| `operation_timeout` | Seconds to wait for a YC operation to complete | `300` |
| `stop_schedule_override` | Override the project-level stop schedule for this type | — |
| `start_schedule_override` | Override the project-level start schedule for this type | — |

### Supported resource types

`compute-instance`, `managed-postgresql`, `managed-kubernetes`, `network-load-balancer`,
`managed-kafka`, `application-load-balancer`, `managed-redis`, `managed-clickhouse`,
`managed-mysql`, `managed-mongodb`, `managed-opensearch`, `ydb`

> **Tip:** `managed-kubernetes` and `ydb` clusters take longer than the default 300 s.
> Set `operation_timeout = 900` for them.

## Schedule format

Schedules use [Quartz cron](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html): `sec min hour day month weekday [year]`

| Example | Meaning |
| --- | --- |
| `0 0 21 ? * MON-FRI *` | 21:00 on weekdays |
| `0 0 7 ? * MON-FRI *` | 07:00 on weekdays |
| `0 0 18 ? * * *` | 18:00 every day |

## Module variables

| Name | Description | Default |
| --- | --- | --- |
| `rundeck_url` | Rundeck server URL | `http://localhost:4440` |
| `rundeck_auth_token` | API token — generate via **User Profile → API Tokens** | — |
| `log_level` | Job log level: `DEBUG`, `VERBOSE`, `INFO`, `WARN`, `ERROR` | `INFO` |
| `max_thread_count` | Nodes processed in parallel per job | `10` |
| `continue_next_node_on_error` | Continue to next node if one fails | `true` |
| `nodes_selected_by_default` | Pre-select all matched nodes when running manually | `true` |
| `node_filter_exclude_query` | Global node filter exclusion (e.g. `labels:no_autoshutdown: true`) | `""` |
| `rank_attribute` | Node attribute used to order execution | `stop_order` |
| `rank_order` | Sort direction for `rank_attribute` | `ascending` |
| `command_ordering_strategy` | `node-first` or `step-first` | `node-first` |

## Outputs

| Name | Description |
| --- | --- |
| `project_ui_urls` | Map of project name → Rundeck jobs URL |

## Get the SA key

```bash
# Create a service account and generate a key
yc iam service-account create --name rundeck-scheduler
yc iam key create --service-account-name rundeck-scheduler --output sa-key.json

# Encode it
base64 -i sa-key.json | tr -d '\n'
```

The SA must have the following roles in the YC folder:
`compute.admin`, `mdb.admin`, `alb.admin`, `load-balancer.admin`, `k8s.admin`
