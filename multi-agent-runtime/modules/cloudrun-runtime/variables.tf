variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "container_image" {
  description = "Full container image URI."
  type        = string
}

variable "container_port" {
  description = "Port the container listens on."
  type        = number
  default     = 8000
}

variable "cpu" {
  description = "CPU allocation (e.g. '1')."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation (e.g. '1Gi')."
  type        = string
  default     = "1Gi"
}

variable "min_instance_count" {
  description = "Minimum instances."
  type        = number
  default     = 1
}

variable "max_instance_count" {
  description = "Maximum instances."
  type        = number
  default     = 4
}

# Secret IDs (not the full resource names — just the short IDs)
variable "secret_database_url" {
  description = "Secret Manager secret ID for DATABASE_URL."
  type        = string
}

variable "secret_neon_api_key" {
  description = "Secret Manager secret ID for NEON_API_KEY."
  type        = string
}

variable "secret_neon_project_id" {
  description = "Secret Manager secret ID for NEON_PROJECT_ID."
  type        = string
}

variable "secret_neon_database" {
  description = "Secret Manager secret ID for NEON_DATABASE."
  type        = string
}

variable "secret_neon_branch" {
  description = "Secret Manager secret ID for NEON_BRANCH."
  type        = string
}
