#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${2:-us-central1}"
GITHUB_OWNER="${3:-""}"
GITHUB_REPO="${4:-""}"
GITHUB_BRANCH="${5:-main}"
ENABLE_CICD="${ENABLE_CICD:-true}"
ENVIRONMENT="production"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required."
    echo "Usage: ./destroy.sh <project-id> [region] [github_owner] [github_repo] [github_branch]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Destroying Strands POS infrastructure on GCP ($ENVIRONMENT)"

cd "$SCRIPT_DIR/infra"

if terraform output -raw artifact_registry_repo >/dev/null 2>&1; then
    CONTAINER_IMAGE="$(terraform output -raw artifact_registry_repo)/strands-pos:latest"
else
    CONTAINER_IMAGE="us-docker.pkg.dev/cloudrun/container/hello"
fi

terraform destroy \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=${CONTAINER_IMAGE}" \
  -var="github_owner=${GITHUB_OWNER}" \
  -var="github_repo=${GITHUB_REPO}" \
  -var="github_branch=${GITHUB_BRANCH}" \
  -var="enable_cicd=${ENABLE_CICD}" \
  -auto-approve

echo "Destroy complete!"
