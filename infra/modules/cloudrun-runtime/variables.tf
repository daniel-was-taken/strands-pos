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
  description = "CPU allocation (e.g. \"1\")."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation."
  type        = string
  default     = "1024Mi"
}

variable "min_instance_count" {
  description = "Minimum instances."
  type        = number
  default     = 0
}

variable "max_instance_count" {
  description = "Maximum instances."
  type        = number
  default     = 4
}

variable "secrets" {
  description = "Map of environment variable names to Secret Manager secret resource IDs."
  type        = map(string)
}

variable "invoker_user_email" {
  description = "Email of the user to grant Cloud Run invoker access to."
  type        = string
  default     = ""
}
