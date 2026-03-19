output "cloud_run_url" {
  description = "The URL of the Cloud Run service"
  value       = module.cloudrun_runtime.service_url
}

output "artifact_registry_repo" {
  description = "The URL of the Artifact Registry"
  value       = module.artifact_registry.repository_url
}
