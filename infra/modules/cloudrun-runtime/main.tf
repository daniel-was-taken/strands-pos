# Service account for Cloud Run workloads
resource "google_service_account" "cloudrun_sa" {
  project      = var.project_id
  account_id   = "${var.environment}-strands-cr-sa"
  display_name = "Cloud Run Service Account for ${var.environment}"
}

# Grant the Cloud Run SA access to Secret Manager secrets dynamically
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = var.secrets
  project   = var.project_id
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant the Cloud Run SA access to Vertex AI for model inference
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "api_service" {
  project  = var.project_id
  name     = "strands-pos-${var.environment}"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloudrun_sa.email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    containers {
      image = var.container_image

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      # Secrets from GCP Secret Manager
      dynamic "env" {
        for_each = var.secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      # GCP project and region for Vertex AI SDK explicit config
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
    }

    timeout = "30s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_secret_manager_secret_iam_member.secret_access,
    google_project_iam_member.vertex_ai_user,
  ]
}

# Explicit invoker access constraint
resource "google_cloud_run_v2_service_iam_member" "user_access" {
  count    = var.invoker_user_email == "" ? 0 : 1
  project  = var.project_id
  name     = google_cloud_run_v2_service.api_service.name
  location = google_cloud_run_v2_service.api_service.location
  role     = "roles/run.invoker"
  member   = "user:${var.invoker_user_email}"
}
