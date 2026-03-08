output "project_ui_urls" {
  description = "Rundeck project UI URLs"
  value = {
    for name in keys(rundeck_project.this) :
    name => "${var.rundeck_url}/project/${name}/jobs"
  }
}
