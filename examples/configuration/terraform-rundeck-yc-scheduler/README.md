# Rundeck YC Scheduler — Terraform Module

Terraform module for managing Rundeck projects with scheduled start/stop jobs for Yandex Cloud resources.

## Features

- Creates Rundeck projects with [yc-node-source](../../../plugin/) plugin pre-configured
- Uploads SA keys to Rundeck Key Storage and creates ACL policies automatically
- Generates stop/start jobs for all resource types at once and per resource type
- Supports per-type schedule overrides and execution ordering
- Excludes resources by label (e.g., `no_autoshutdown: true`)

## Project Definition

Each project maps to one Yandex Cloud folder and requires:

- **name** — Rundeck project name (must be unique)
- **folder_id** — Yandex Cloud folder ID containing the resources
- **yc_sa_key** — base64-encoded Service Account authorized key (stored in Rundeck Key Storage)

Optional settings:

- **stop_schedule** / **start_schedule** — Quartz cron expressions (e.g., `0 0 21 ? * MON-FRI *`)
- **time_zone** — schedule time zone (default: `Europe/Moscow`)
- **resource_types** — map of resource types to manage (default: `compute-instance` only)

### Supported Resource Types

| Type | Description |
| --- | --- |
| `compute-instance` | Virtual machines |
| `managed-postgresql` | Managed PostgreSQL clusters |
| `managed-kubernetes` | Managed Kubernetes clusters |
| `network-load-balancer` | Network load balancers |

### Resource Type Options

Each resource type accepts optional parameters:

| Parameter | Description | Default |
| --- | --- | --- |
| `enabled` | Enable/disable this resource type | `true` |
| `stop_order` | Execution order (lower = earlier) | `1` |
| `stop_schedule_override` | Override project-level stop schedule | `null` |
| `start_schedule_override` | Override project-level start schedule | `null` |

### Schedule Format

Schedules use [Quartz cron expressions](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html):

```text
sec min hour day month weekday [year]
```

Examples:

- `0 0 21 ? * MON-FRI *` — 21:00 on weekdays
- `0 30 7 ? * MON-FRI *` — 07:30 on weekdays
- `0 0 18 ? * * *` — 18:00 every day

## Usage

```hcl
module "rundeck_projects" {
  source = "git::https://github.com/<owner>/rundeck-yc-scheduler.git//examples/configuration/terraform-rundeck-yc-scheduler?ref=v1.0.0"

  rundeck_url        = "http://localhost:4440"
  rundeck_auth_token = var.rundeck_auth_token

  projects = [
    {
      name           = "production"
      folder_id      = "b1g0abc123def456"
      yc_sa_key      = var.yc_sa_key_production
      stop_schedule  = "0 0 21 ? * MON-FRI *"
      start_schedule = "0 0 7 ? * MON-FRI *"
      time_zone      = "Europe/Moscow"

      resource_types = {
        "compute-instance"   = { stop_order = 2 }
        "managed-postgresql" = { stop_order = 1 }
      }
    },
    {
      name      = "staging"
      folder_id = "b1g0xyz789ghi012"
      yc_sa_key = var.yc_sa_key_staging

      resource_types = {
        "compute-instance" = {}
      }
    },
  ]
}
```

## Configure Access

```bash
export RUNDECK_URL="http://localhost:4440"
export RUNDECK_AUTH_TOKEN="your-api-token"
```

Generate an API token: **Rundeck UI → User Profile → API Tokens → Generate New Token**.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_rundeck"></a> [rundeck](#requirement\_rundeck) | ~> 1.1 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_rundeck"></a> [rundeck](#provider\_rundeck) | ~> 1.1 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [rundeck_acl_policy.project_storage](https://registry.terraform.io/providers/rundeck/rundeck/latest/docs/resources/acl_policy) | resource |
| [rundeck_job.this](https://registry.terraform.io/providers/rundeck/rundeck/latest/docs/resources/job) | resource |
| [rundeck_password.yc_sa_key](https://registry.terraform.io/providers/rundeck/rundeck/latest/docs/resources/password) | resource |
| [rundeck_project.this](https://registry.terraform.io/providers/rundeck/rundeck/latest/docs/resources/project) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_projects"></a> [projects](#input\_projects) | List of Rundeck projects (one per YC folder) | <pre>list(object({<br>    name           = string<br>    display_name   = optional(string)<br>    folder_id      = string<br>    yc_sa_key      = optional(string)<br>    stop_schedule  = optional(string)<br>    start_schedule = optional(string)<br>    time_zone      = optional(string, "Europe/Moscow")<br>    resource_types = optional(map(object({<br>      enabled                 = optional(bool, true)<br>      stop_schedule_override  = optional(string)<br>      start_schedule_override = optional(string)<br>      stop_order              = optional(number, 1)<br>    })), { "compute-instance" = {} })<br>  }))</pre> | n/a | yes |
| <a name="input_rundeck_auth_token"></a> [rundeck\_auth\_token](#input\_rundeck\_auth\_token) | Rundeck API token (User Profile → API Tokens) | `string` | n/a | yes |
| <a name="input_command_ordering_strategy"></a> [command\_ordering\_strategy](#input\_command\_ordering\_strategy) | Execution strategy: node-first (all steps on one node, then next) or step-first | `string` | `"node-first"` | no |
| <a name="input_continue_next_node_on_error"></a> [continue\_next\_node\_on\_error](#input\_continue\_next\_node\_on\_error) | Continue processing remaining nodes if one node fails | `bool` | `true` | no |
| <a name="input_log_level"></a> [log\_level](#input\_log\_level) | Job log level: DEBUG, VERBOSE, INFO, WARN, ERROR | `string` | `"INFO"` | no |
| <a name="input_max_thread_count"></a> [max\_thread\_count](#input\_max\_thread\_count) | Maximum number of nodes processed in parallel per job | `number` | `10` | no |
| <a name="input_node_filter_exclude_query"></a> [node\_filter\_exclude\_query](#input\_node\_filter\_exclude\_query) | Node filter expression to exclude nodes from all jobs (e.g., "labels:no\_autoshutdown: true") | `string` | `""` | no |
| <a name="input_nodes_selected_by_default"></a> [nodes\_selected\_by\_default](#input\_nodes\_selected\_by\_default) | Whether all matched nodes are selected by default when running a job manually | `bool` | `true` | no |
| <a name="input_rank_attribute"></a> [rank\_attribute](#input\_rank\_attribute) | Node attribute used to sort execution order within a job | `string` | `"stop_order"` | no |
| <a name="input_rank_order"></a> [rank\_order](#input\_rank\_order) | Sort direction for rank\_attribute: ascending or descending | `string` | `"ascending"` | no |
| <a name="input_rundeck_url"></a> [rundeck\_url](#input\_rundeck\_url) | Rundeck URL | `string` | `"http://localhost:4440"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_project_ui_urls"></a> [project\_ui\_urls](#output\_project\_ui\_urls) | Rundeck project UI URLs |
<!-- END_TF_DOCS -->
