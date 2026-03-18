# Service account for Cloud Build
resource "google_service_account" "cloudbuild" {
  project      = var.project_id
  account_id   = "strands-pos-cloudbuild"
  display_name = "Strands POS Cloud Build"
}

# Grant Cloud Build SA permission to push to Artifact Registry
resource "google_artifact_registry_repository_iam_member" "cloudbuild_writer" {
  project    = var.project_id
  location   = var.region
  repository = "strands-pos"
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# Grant Cloud Build SA permission to deploy to Cloud Run
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# Grant Cloud Build SA permission to act as the Cloud Run service account
resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# Grant Cloud Build SA permission to write logs
resource "google_project_iam_member" "cloudbuild_logs_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudbuild.email}"
}

# Cloud Build trigger — builds on push to the configured branch
resource "google_cloudbuild_trigger" "deploy" {
  project  = var.project_id
  name     = "strands-pos-deploy"
  location = var.region

  github {
    owner = var.github_owner
    name  = var.github_repo

    push {
      branch = "^${var.github_branch}$"
    }
  }

  service_account = google_service_account.cloudbuild.id

  build {
    # Step 1: Build the Docker image
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t", "${var.repository_url}/${var.image_name}:$COMMIT_SHA",
        "-t", "${var.repository_url}/${var.image_name}:latest",
        ".",
      ]
    }

    # Step 2: Push the image to Artifact Registry
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "--all-tags",
        "${var.repository_url}/${var.image_name}",
      ]
    }

    # Step 3: Deploy to Cloud Run
    step {
      name = "gcr.io/google.com/cloudsdktool/cloud-sdk"
      args = [
        "gcloud", "run", "deploy", var.service_name,
        "--image", "${var.repository_url}/${var.image_name}:$COMMIT_SHA",
        "--region", var.region,
        "--quiet",
      ]
    }

    options {
      logging = "CLOUD_LOGGING_ONLY"
    }

    images = [
      "${var.repository_url}/${var.image_name}:$COMMIT_SHA",
      "${var.repository_url}/${var.image_name}:latest",
    ]
  }
}
