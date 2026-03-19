#!/usr/bin/env bash
# deploy.sh — Build, push, and deploy the Strands POS application to GCP.
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated (`gcloud auth login`)
#   2. Terraform >= 1.5 installed
#   3. A GCP project with billing enabled
#   4. Local .env file populated with runtime secrets to publish
#
# Usage:
#   ./deploy.sh <project-id> [region] [github_owner] [github_repo] [github_branch] [enable_cicd] [invoker_user_email]
#
# Example:
#   ./deploy.sh my-gcp-project us-central1 my-org my-repo main true you@example.com

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${2:-us-central1}"
GITHUB_OWNER="${3:-""}"
GITHUB_REPO="${4:-""}"
GITHUB_BRANCH="${5:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")}"
ENABLE_CICD="${6:-false}"
INVOKER_USER_EMAIL="${7:-$(gcloud config get-value account 2>/dev/null || echo "")}"
ENVIRONMENT="${ENVIRONMENT:-production}"
ENV_FILE="${ENV_FILE:-.env}"
IMAGE_NAME="strands-pos"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: PROJECT_ID is required."
  echo "Usage: ./deploy.sh <project-id> [region] [github_owner] [github_repo] [github_branch] [enable_cicd] [invoker_user_email]"
  exit 1
fi

normalize_bool() {
  case "${1:-false}" in
    true|TRUE|True|1|yes|YES|y|Y)
      echo "true"
      ;;
    false|FALSE|False|0|no|NO|n|N|"")
      echo "false"
      ;;
    *)
      echo "Error: boolean value expected, got '$1'." >&2
      exit 1
      ;;
  esac
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' is not installed." >&2
    exit 1
  fi
}

read_env_value() {
  local key="$1"
  local env_path="$2"
  local line

  line="$(grep -E "^${key}=" "$env_path" | tail -n 1 || true)"
  if [ -z "$line" ]; then
    echo ""
    return 1
  fi

  line="${line#*=}"
  line="${line%$'\r'}"

  if [[ "$line" == \"*\" ]]; then
    line="${line#\"}"
    line="${line%\"}"
  elif [[ "$line" == \'*\' ]]; then
    line="${line#\'}"
    line="${line%\'}"
  fi

  printf '%s' "$line"
}

sync_secret_versions() {
  local env_path="$1"
  local secret_name
  local secret_value
  local key

  for key in DATABASE_URL NEON_API_KEY NEON_PROJECT_ID NEON_DATABASE NEON_BRANCH_ID; do
    if ! secret_value="$(read_env_value "$key" "$env_path")"; then
      echo "Error: missing required key '$key' in $env_path." >&2
      exit 1
    fi

    secret_name="${ENVIRONMENT}-strands-pos-${key}"
    echo "==> Updating Secret Manager version for ${secret_name}"
    printf '%s' "$secret_value" | gcloud secrets versions add "$secret_name" \
      --project "$PROJECT_ID" \
      --data-file=- >/dev/null
  done
}

ENABLE_CICD="$(normalize_bool "$ENABLE_CICD")"

if [ "$ENABLE_CICD" = "true" ] && { [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ]; }; then
  echo "Error: github_owner and github_repo are required when enable_cicd=true." >&2
  exit 1
fi

require_command gcloud
require_command terraform

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
INFRA_DIR="$REPO_ROOT/infra"

echo "==> Deploying Strands POS to GCP (${ENVIRONMENT})"

cd "$INFRA_DIR"
echo "==> Initializing Terraform"
terraform init

echo "==> Bootstrapping required APIs and Secret Manager secrets (without Cloud Run)"
terraform apply \
  -target=google_project_service.required_apis \
  -target=google_secret_manager_secret.neon_secrets \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -auto-approve

if [ ! -f "$REPO_ROOT/$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found at repo root; cannot publish required secret versions." >&2
  echo "Create $ENV_FILE with DATABASE_URL, NEON_API_KEY, NEON_PROJECT_ID, NEON_DATABASE, and NEON_BRANCH_ID." >&2
  exit 1
fi

echo "==> Syncing local secrets from $ENV_FILE"
sync_secret_versions "$REPO_ROOT/$ENV_FILE"

echo "==> Applying full Terraform infrastructure"
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="invoker_user_email=${INVOKER_USER_EMAIL}" \
  -var="github_owner=${GITHUB_OWNER}" \
  -var="github_repo=${GITHUB_REPO}" \
  -var="github_branch=${GITHUB_BRANCH}" \
  -var="enable_cicd=${ENABLE_CICD}" \
  -auto-approve

ARTIFACT_REPO="$(terraform output -raw artifact_registry_repo)"
IMAGE_URI="${ARTIFACT_REPO}/${IMAGE_NAME}:latest"

echo "==> Building and pushing container image ${IMAGE_URI}"
cd "$REPO_ROOT"
gcloud builds submit \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --default-buckets-behavior=regional-user-owned-bucket \
  --tag "$IMAGE_URI" \
  .

echo "==> Updating Cloud Run to use the real application image"
cd "$INFRA_DIR"
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=${IMAGE_URI}" \
  -var="invoker_user_email=${INVOKER_USER_EMAIL}" \
  -var="github_owner=${GITHUB_OWNER}" \
  -var="github_repo=${GITHUB_REPO}" \
  -var="github_branch=${GITHUB_BRANCH}" \
  -var="enable_cicd=${ENABLE_CICD}" \
  -auto-approve

CLOUD_RUN_URL="$(terraform output -raw cloud_run_url)"

echo ""
echo "========================================="
echo " Deployment Completed Successfully!"
echo "========================================="
echo ""
echo "Cloud Run URL: ${CLOUD_RUN_URL}"
echo "Container image: ${IMAGE_URI}"
if [ "$ENABLE_CICD" = "true" ]; then
  echo "CI/CD trigger target branch: ${GITHUB_BRANCH}"
fi
