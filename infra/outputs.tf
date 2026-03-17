output "cloud_run_url" {
  description = "The public URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.api_service.uri
}

output "artifact_registry_repo" {
  description = "The URL of the Artifact Registry"
  value       = google_artifact_registry_repository.repo.id
}
