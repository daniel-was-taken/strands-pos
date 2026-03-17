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
  description = "The container image to deploy (e.g. us-central1-docker.pkg.dev/project/repo/image:tag). Provide a default placeholder for initial setup."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "invoker_user_email" {
  description = "User email to grant Cloud Run invoker access (leave empty to skip)."
  type        = string
  default     = ""
}
