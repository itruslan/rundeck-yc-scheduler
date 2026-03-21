# Example: Configure Rundeck projects and scheduled jobs for Yandex Cloud
#
# This example creates two projects:
#   1. "staging" — stops resources at 21:00, starts at 07:00 (Mon-Fri)
#   2. "dev"     — stops resources at 19:00, starts at 09:00 (Mon-Fri)

module "rundeck_projects" {
  source = "../"

  # Or use Git source:
  # source = "git::https://github.com/itruslan/rundeck-yc-scheduler.git//examples/configuration/terraform-rundeck-yc-scheduler?ref=v1.0.0"

  rundeck_url        = var.rundeck_url
  rundeck_auth_token = var.rundeck_auth_token

  projects = [
    {
      name         = "staging"
      display_name = "Staging Environment"
      folder_id    = "b1g0abc123def456"
      yc_sa_key    = var.yc_sa_key_staging

      # Quartz cron: sec min hour day month weekday [year]
      stop_schedule  = "0 0 21 ? * MON-FRI *"
      start_schedule = "0 0 7 ? * MON-FRI *"
      time_zone      = "Europe/Moscow"

      resource_types = {
        "compute-instance" = {
          enabled    = true
          stop_order = 2 # stop VMs after databases
        }
        "managed-postgresql" = {
          enabled    = true
          stop_order = 1 # stop databases first
        }
        "managed-kubernetes" = {
          enabled           = true
          stop_order        = 3
          operation_timeout = 900 # k8s clusters take longer to stop/start
        }
        "application-load-balancer" = {
          enabled    = true
          stop_order = 4
        }
      }
    },
    {
      name         = "dev"
      display_name = "Dev Environment"
      folder_id    = "b1g0xyz789ghi012"
      yc_sa_key    = var.yc_sa_key_dev

      stop_schedule  = "0 0 19 ? * MON-FRI *"
      start_schedule = "0 0 9 ? * MON-FRI *"
      time_zone      = "Europe/Moscow"

      resource_types = {
        "compute-instance" = { enabled = true }
      }
    },
  ]
}

output "project_urls" {
  value = module.rundeck_projects.project_ui_urls
}
