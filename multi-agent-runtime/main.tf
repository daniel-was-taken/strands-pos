# ---------- Enable required GCP APIs ----------

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
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
  repository_id = "strands-pos"

  depends_on = [google_project_service.required_apis]
}

# ---------- Secrets ----------

resource "google_secret_manager_secret" "database_url" {
  project   = var.project_id
  secret_id = "${var.environment}-strands-pos-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = var.database_url
}

resource "google_secret_manager_secret" "neon_api_key" {
  project   = var.project_id
  secret_id = "${var.environment}-strands-pos-neon-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "neon_api_key" {
  secret      = google_secret_manager_secret.neon_api_key.id
  secret_data = var.neon_api_key
}

resource "google_secret_manager_secret" "neon_project_id" {
  project   = var.project_id
  secret_id = "${var.environment}-strands-pos-neon-project-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "neon_project_id" {
  secret      = google_secret_manager_secret.neon_project_id.id
  secret_data = var.neon_project_id
}

resource "google_secret_manager_secret" "neon_database" {
  project   = var.project_id
  secret_id = "${var.environment}-strands-pos-neon-database"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "neon_database" {
  secret      = google_secret_manager_secret.neon_database.id
  secret_data = var.neon_database
}

resource "google_secret_manager_secret" "neon_branch" {
  project   = var.project_id
  secret_id = "${var.environment}-strands-pos-neon-branch"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "neon_branch" {
  secret      = google_secret_manager_secret.neon_branch.id
  secret_data = var.neon_branch
}

# ---------- Cloud Run ----------

module "cloudrun_runtime" {
  source = "./modules/cloudrun-runtime"

  project_id         = var.project_id
  region             = var.region
  environment        = var.environment
  container_image    = var.container_image != "" ? var.container_image : "${module.artifact_registry.repository_url}/strands-pos:latest"
  container_port     = var.container_port
  cpu                = var.cpu
  memory             = var.memory
  min_instance_count = var.min_instance_count
  max_instance_count = var.max_instance_count

  secret_database_url    = google_secret_manager_secret.database_url.secret_id
  secret_neon_api_key    = google_secret_manager_secret.neon_api_key.secret_id
  secret_neon_project_id = google_secret_manager_secret.neon_project_id.secret_id
  secret_neon_database   = google_secret_manager_secret.neon_database.secret_id
  secret_neon_branch     = google_secret_manager_secret.neon_branch.secret_id

  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_version.database_url,
    google_secret_manager_secret_version.neon_api_key,
    google_secret_manager_secret_version.neon_project_id,
    google_secret_manager_secret_version.neon_database,
    google_secret_manager_secret_version.neon_branch,
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

  depends_on = [google_project_service.required_apis]
}
