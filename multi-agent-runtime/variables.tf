variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region for all resources."
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (e.g. production, staging)."
  type        = string
  default     = "production"
}

variable "container_image" {
  description = "Full Artifact Registry image URI (e.g. us-central1-docker.pkg.dev/PROJECT/strands-pos/strands-pos:latest)."
  type        = string
  default     = ""
}

variable "min_instance_count" {
  description = "Minimum number of Cloud Run instances."
  type        = number
  default     = 1
}

variable "max_instance_count" {
  description = "Maximum number of Cloud Run instances."
  type        = number
  default     = 4
}

variable "cpu" {
  description = "CPU allocation per Cloud Run instance (e.g. '1' or '2')."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation per Cloud Run instance (e.g. '512Mi', '1Gi')."
  type        = string
  default     = "1Gi"
}

variable "container_port" {
  description = "Port the container listens on."
  type        = number
  default     = 8000
}

# -- Secrets (initial values stored in GCP Secret Manager) --

variable "database_url" {
  description = "Neon PostgreSQL connection string."
  type        = string
  sensitive   = true
  default     = ""
}

variable "neon_api_key" {
  description = "Neon API key."
  type        = string
  sensitive   = true
  default     = ""
}

variable "neon_project_id" {
  description = "Neon project ID."
  type        = string
  default     = ""
}

variable "neon_database" {
  description = "Neon database name."
  type        = string
  default     = ""
}

variable "neon_branch" {
  description = "Neon branch name."
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
