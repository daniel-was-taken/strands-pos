output "service_url" {
  description = "URL of the Cloud Run service."
  value       = google_cloud_run_v2_service.api_service.uri
}

output "service_name" {
  description = "Cloud Run service name."
  value       = google_cloud_run_v2_service.api_service.name
}

output "service_account_email" {
  description = "Cloud Run service account email."
  value       = google_service_account.cloudrun_sa.email
}
