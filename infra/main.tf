# ---------------------------------------------------------
# APIs
# ---------------------------------------------------------
resource "google_project_service" "vertex_ai" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "strands-pos-${var.environment}"
  description   = "Docker repository for Strands POS API"
  format        = "DOCKER"
}

# ---------------------------------------------------------
# Secrets
# ---------------------------------------------------------
resource "google_secret_manager_secret" "neon_secrets" {
  for_each = toset([
    "DATABASE_URL",
    "NEON_API_KEY",
    "NEON_PROJECT_ID",
    "NEON_DATABASE",
    "NEON_BRANCH"
  ])

  secret_id = "${var.environment}-strands-pos-${each.key}"
  replication {
    auto { }
  }
}

resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.environment}-strands-cr-sa"
  display_name = "Cloud Run Service Account for ${var.environment}"
}

# Grant the Cloud Run service account access to the secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = google_secret_manager_secret.neon_secrets
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# Grant the Cloud Run service account access to Vertex AI
resource "google_project_iam_member" "vertexai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"

  depends_on = [google_project_service.vertex_ai]
}

# ---------------------------------------------------------
# Cloud Run Service (Replaces ECS & ALB)
# ---------------------------------------------------------
resource "google_cloud_run_v2_service" "api_service" {
  name     = "strands-pos-${var.environment}"
  location = var.region
  ingress              = "INGRESS_TRAFFIC_ALL"
  invoker_iam_disabled = true

  template {
    service_account = google_service_account.cloudrun_sa.email
    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1024Mi"
        }
      }

      ports {
        container_port = 8000
      }

      # Vertex AI / Gemini configuration
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }

      # Mount secrets as environment variables
      dynamic "env" {
        for_each = google_secret_manager_secret.neon_secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = "latest"
            }
          }
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 4
    }
  }

  depends_on = [
    google_project_service.vertex_ai,
    google_secret_manager_secret_iam_member.secret_access,
  ]
}

# Allow full unauthenticated access similar to ALB ingress rules.
# The org policy (domain restricted sharing) blocks granting allUsers via IAM,
# so we disable the Cloud Run Invoker IAM check instead (invoker_iam_disabled
# on the service resource above).  This is Google's recommended approach for
# public services in restricted orgs.
# See: https://cloud.google.com/run/docs/authenticating/public

resource "google_cloud_run_v2_service_iam_member" "user_access" {
  count    = var.invoker_user_email == "" ? 0 : 1
  name     = google_cloud_run_v2_service.api_service.name
  location = google_cloud_run_v2_service.api_service.location
  role     = "roles/run.invoker"
  member   = "user:${var.invoker_user_email}"
}
