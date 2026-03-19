resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository_id
  description   = "Docker repository for Strands POS agent images."
  format        = "DOCKER"

  cleanup_policy_dry_run = false

  docker_config {
    immutable_tags = false
  }
}
