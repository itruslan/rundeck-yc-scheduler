variable "rundeck_url" {
  description = "Rundeck URL"
  type        = string
  default     = "http://localhost:4440"
}

variable "rundeck_auth_token" {
  description = "Rundeck API token (User Profile → API Tokens)"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Job defaults
# ---------------------------------------------------------------------------

variable "log_level" {
  description = "Job log level: DEBUG, VERBOSE, INFO, WARN, ERROR"
  default     = "INFO"
}

variable "node_filter_exclude_query" {
  description = "Node filter expression to exclude nodes from all jobs (e.g., \"labels:no_autoshutdown: true\")"
  default     = ""
}

variable "nodes_selected_by_default" {
  description = "Whether all matched nodes are selected by default when running a job manually"
  default     = true
}

variable "max_thread_count" {
  description = "Maximum number of nodes processed in parallel per job"
  default     = 10
}

variable "continue_next_node_on_error" {
  description = "Continue processing remaining nodes if one node fails"
  default     = true
}

variable "rank_attribute" {
  description = "Node attribute used to sort execution order within a job"
  default     = "stop_order"
}

variable "rank_order" {
  description = "Sort direction for rank_attribute: ascending or descending"
  default     = "ascending"
}

variable "command_ordering_strategy" {
  description = "Execution strategy: node-first (all steps on one node, then next) or step-first"
  default     = "node-first"
}

# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

variable "projects" {
  description = "List of Rundeck projects (one per YC folder)"
  type = list(object({
    name           = string
    display_name   = optional(string)
    folder_id      = string
    yc_sa_key      = optional(string)
    stop_schedule  = optional(string)
    start_schedule = optional(string)
    time_zone      = optional(string, "Europe/Moscow")
    resource_types = optional(map(object({
      enabled                 = optional(bool, true)
      stop_schedule_override  = optional(string)
      start_schedule_override = optional(string)
      stop_order              = optional(number, 1)
    })), { "compute-instance" = {} })
  }))
}
