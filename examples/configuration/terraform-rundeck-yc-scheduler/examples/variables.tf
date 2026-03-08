variable "rundeck_url" {
  description = "Rundeck server URL"
  type        = string
  default     = "http://localhost:4440"
}

variable "rundeck_auth_token" {
  description = "Rundeck API token (generate via User Profile → API Tokens)"
  type        = string
  sensitive   = true
}

variable "yc_sa_key_production" {
  description = "Base64-encoded Yandex Cloud Service Account key for production folder"
  type        = string
  sensitive   = true
  default     = ""
}

variable "yc_sa_key_staging" {
  description = "Base64-encoded Yandex Cloud Service Account key for staging folder"
  type        = string
  sensitive   = true
  default     = ""
}
