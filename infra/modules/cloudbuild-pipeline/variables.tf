variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "repository_url" {
  description = "Artifact Registry repository URL (e.g. us-central1-docker.pkg.dev/PROJECT/REPO)."
  type        = string
}

variable "image_name" {
  description = "Docker image name within the repository."
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name to deploy to."
  type        = string
}

variable "github_owner" {
  description = "GitHub repository owner (user or org)."
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name."
  type        = string
}

variable "github_branch" {
  description = "Branch that triggers builds."
  type        = string
  default     = "main"
}
