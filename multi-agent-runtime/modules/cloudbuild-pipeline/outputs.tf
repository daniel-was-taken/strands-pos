output "trigger_id" {
  description = "Cloud Build trigger ID."
  value       = google_cloudbuild_trigger.deploy.trigger_id
}

output "service_account_email" {
  description = "Cloud Build service account email."
  value       = google_service_account.cloudbuild.email
}
