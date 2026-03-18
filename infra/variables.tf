variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources to"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "container_image" {
  description = "The container image to deploy. Provide a default placeholder for initial setup."
  type        = string
  default     = ""
}

variable "invoker_user_email" {
  description = "User email to grant Cloud Run invoker access (leave empty to skip)."
  type        = string
  default     = ""
}

variable "github_owner" {
  description = "GitHub repository owner (user or org)."
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name."
  type        = string
  default     = ""
}

variable "github_branch" {
  description = "Branch that triggers Cloud Build."
  type        = string
  default     = "main"
}
