terraform {
  required_providers {
    rundeck = {
      source  = "rundeck/rundeck"
      version = "~> 1.1"
    }
  }
}

provider "rundeck" {
  url        = var.rundeck_url
  auth_token = var.rundeck_auth_token
}
