# Service account for Cloud Run workloads
resource "google_service_account" "cloudrun" {
  project      = var.project_id
  account_id   = "strands-pos-cloudrun"
  display_name = "Strands POS Cloud Run"
}

# Grant the Cloud Run SA access to Secret Manager secrets
resource "google_secret_manager_secret_iam_member" "database_url" {
  project   = var.project_id
  secret_id = var.secret_database_url
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "neon_api_key" {
  project   = var.project_id
  secret_id = var.secret_neon_api_key
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "neon_project_id" {
  project   = var.project_id
  secret_id = var.secret_neon_project_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "neon_database" {
  project   = var.project_id
  secret_id = var.secret_neon_database
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

resource "google_secret_manager_secret_iam_member" "neon_branch" {
  project   = var.project_id
  secret_id = var.secret_neon_branch
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Grant the Cloud Run SA access to Vertex AI for model inference
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  name     = "${var.environment}-strands-pos"
  location = var.region

  template {
    service_account = google_service_account.cloudrun.email

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

      startup_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        period_seconds = 15
      }

      # Secrets from GCP Secret Manager
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = var.secret_database_url
            version = "latest"
          }
        }
      }

      env {
        name = "NEON_API_KEY"
        value_source {
          secret_key_ref {
            secret  = var.secret_neon_api_key
            version = "latest"
          }
        }
      }

      env {
        name = "NEON_PROJECT_ID"
        value_source {
          secret_key_ref {
            secret  = var.secret_neon_project_id
            version = "latest"
          }
        }
      }

      env {
        name = "NEON_DATABASE"
        value_source {
          secret_key_ref {
            secret  = var.secret_neon_database
            version = "latest"
          }
        }
      }

      env {
        name = "NEON_BRANCH"
        value_source {
          secret_key_ref {
            secret  = var.secret_neon_branch
            version = "latest"
          }
        }
      }

      # GCP project and region for Vertex AI SDK
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_REGION"
        value = var.region
      }
    }

    timeout = "30s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public HTTP endpoint)
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  name     = google_cloud_run_v2_service.app.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
