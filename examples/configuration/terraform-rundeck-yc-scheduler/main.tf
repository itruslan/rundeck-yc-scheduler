locals {
  projects_map = { for p in var.projects : p.name => p }

  # Stop All / Start All — manual only, covers all managed resource types
  all_jobs = flatten([
    for p in var.projects : [
      for op in ["stop", "start"] : {
        key              = "${p.name}/all/${op}"
        project_name     = p.name
        op               = op
        display_name     = op == "stop" ? "Stop All" : "Start All"
        group_name       = null
        node_filter      = "resource_type: .*"
        schedule         = null
        schedule_enabled = false
        time_zone        = null
        stop_order       = null
      }
    ]
  ])

  # One stop/start job per resource type per project.
  # Schedule: use the type-level override if set, otherwise inherit from the project default.
  rt_jobs = flatten([
    for p in var.projects : [
      for rt_name, rt in p.resource_types : [
        for op in ["stop", "start"] : {
          key              = "${p.name}/${rt_name}/${op}"
          project_name     = p.name
          op               = op
          display_name     = op == "stop" ? "Stop" : "Start"
          group_name       = "${p.name}/${rt_name}"
          node_filter      = "resource_type: ${rt_name}"
          schedule         = op == "stop" ? (rt.stop_schedule_override != null ? rt.stop_schedule_override : p.stop_schedule) : (rt.start_schedule_override != null ? rt.start_schedule_override : p.start_schedule)
          schedule_enabled = op == "stop" ? (rt.stop_schedule_override != null ? rt.stop_schedule_override : p.stop_schedule) != null : (rt.start_schedule_override != null ? rt.start_schedule_override : p.start_schedule) != null
          time_zone        = p.time_zone
          stop_order       = rt.stop_order
        } if rt.enabled
      ]
    ]
  ])

  jobs_map = { for j in concat(local.all_jobs, local.rt_jobs) : j.key => j }
}

resource "rundeck_password" "yc_sa_key" {
  for_each = { for p in var.projects : p.name => p if nonsensitive(p.yc_sa_key != null) }
  path     = "project/${each.key}/yc-sa-key"
  password = each.value.yc_sa_key
}

resource "rundeck_project" "this" {
  for_each    = local.projects_map
  name        = each.key
  description = "folder_id: ${each.value.folder_id}"
  extra_config = {
    "project.label" = coalesce(each.value.display_name, each.key)
  }

  resource_model_source {
    type = "yc-node-source"
    config = {
      folder_id = each.value.folder_id
      yc_sa_key = each.value.yc_sa_key != null ? "keys/project/${each.key}/yc-sa-key" : ""
    }
  }
}

resource "rundeck_acl_policy" "project_storage" {
  for_each = { for p in var.projects : p.name => p if nonsensitive(p.yc_sa_key != null) }
  name     = "${each.key}-storage.aclpolicy"
  policy   = <<-EOT
    description: Allow ${each.key} project to read Key Storage for yc-scheduler plugins.
    context:
      application: rundeck
    for:
      storage:
        - match:
            path: 'keys/project/${each.key}/.*'
          allow: [read]
    by:
      urn: 'project:${each.key}'
    EOT
}

resource "rundeck_job" "this" {
  for_each = local.jobs_map

  project_name                = rundeck_project.this[each.value.project_name].name
  name                        = each.value.display_name
  group_name                  = each.value.group_name
  description                 = each.value.schedule_enabled ? "(Scheduled)" : "(Manual)"
  log_level                   = var.log_level
  node_filter_query           = each.value.node_filter
  node_filter_exclude_query   = var.node_filter_exclude_query
  nodes_selected_by_default   = var.nodes_selected_by_default
  max_thread_count            = var.max_thread_count
  continue_next_node_on_error = var.continue_next_node_on_error
  rank_order                  = var.rank_order
  rank_attribute              = var.rank_attribute
  command_ordering_strategy   = var.command_ordering_strategy
  schedule                    = each.value.schedule
  schedule_enabled            = each.value.schedule_enabled
  time_zone                   = each.value.time_zone

  command {
    node_step_plugin {
      type = "yc-${each.value.op}"
      config = {
        yc_sa_key = "keys/project/${each.value.project_name}/yc-sa-key"
      }
    }
  }
}
