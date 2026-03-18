# ---------- Enable required GCP APIs ----------

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "aiplatform.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# ---------- Artifact Registry ----------

module "artifact_registry" {
  source = "./modules/artifact-registry"

  project_id    = var.project_id
  region        = var.region
  repository_id = "strands-pos-${var.environment}"

  depends_on = [google_project_service.required_apis]
}

# ---------- Secrets ----------
# Secrets are explicitly declared but NOT populated through TF vars to prevent state leaks.
# Values should be injected via secure CI or manual Secret Manager interaction.

resource "google_secret_manager_secret" "neon_secrets" {
  for_each = toset([
    "DATABASE_URL",
    "NEON_API_KEY",
    "NEON_PROJECT_ID",
    "NEON_DATABASE",
    "NEON_BRANCH"
  ])

  project   = var.project_id
  secret_id = "${var.environment}-strands-pos-${each.key}"
  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

# ---------- Cloud Run ----------

module "cloudrun_runtime" {
  source = "./modules/cloudrun-runtime"

  project_id         = var.project_id
  region             = var.region
  environment        = var.environment
  container_image    = var.container_image != "" ? var.container_image : "${module.artifact_registry.repository_url}/strands-pos:latest"
  container_port     = 8000
  cpu                = "1"
  memory             = "1024Mi"
  min_instance_count = 0
  max_instance_count = 4

  secrets            = { for k, v in google_secret_manager_secret.neon_secrets : k => v.secret_id }
  invoker_user_email = var.invoker_user_email

  depends_on = [
    google_project_service.required_apis,
    module.artifact_registry
  ]
}

# ---------- Cloud Build CI/CD ----------

module "cloudbuild_pipeline" {
  source = "./modules/cloudbuild-pipeline"

  project_id     = var.project_id
  region         = var.region
  repository_url = module.artifact_registry.repository_url
  image_name     = "strands-pos"
  service_name   = module.cloudrun_runtime.service_name
  github_owner   = var.github_owner
  github_repo    = var.github_repo
  github_branch  = var.github_branch

  depends_on = [
    google_project_service.required_apis,
    module.artifact_registry,
    module.cloudrun_runtime
  ]
}
