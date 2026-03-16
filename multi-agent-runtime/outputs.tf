output "service_url" {
  description = "Public URL of the Cloud Run service."
  value       = module.cloudrun_runtime.service_url
}

output "service_name" {
  description = "Name of the Cloud Run service."
  value       = module.cloudrun_runtime.service_name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL for Docker images."
  value       = module.artifact_registry.repository_url
}

output "cloud_build_trigger_id" {
  description = "Cloud Build trigger ID."
  value       = module.cloudbuild_pipeline.trigger_id
}
