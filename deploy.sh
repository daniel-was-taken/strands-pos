#!/usr/bin/env bash
# deploy.sh — Build, push, and deploy the Strands POS application to GCP.
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated (`gcloud auth login`)
#   2. Terraform >= 1.5 installed
#   3. A GCP project with billing enabled
#
# Usage:
#   ./deploy.sh <project-id> [region] [github_owner] [github_repo] [github_branch]
#
# Example:
#   ./deploy.sh my-gcp-project us-central1 my-org my-repo main

set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "")}"
REGION="${2:-us-central1}"
GITHUB_OWNER="${3:-""}"
GITHUB_REPO="${4:-""}"
GITHUB_BRANCH="${5:-"main"}"
ENVIRONMENT="production"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required."
    echo "Usage: ./deploy.sh <project-id> [region]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Deploying Strands POS to GCP ($ENVIRONMENT)"

echo "==> Initializing Terraform"
cd "$SCRIPT_DIR/infra"
terraform init

echo "==> Applying Terraform (infrastructure only — creates registry, secrets, Cloud Run service, Cloud Build trigger)"
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="github_owner=${GITHUB_OWNER}" \
  -var="github_repo=${GITHUB_REPO}" \
  -var="github_branch=${GITHUB_BRANCH}" \
  -auto-approve

echo ""
echo "========================================="
echo " Infrastructure Deployed Successfully!"
echo "========================================="
echo ""
echo "To finish your setup:"
echo "1. Set your Secret Manager values manually via GCP Console or CLI. Example:"
echo "   echo -n 'your_db_url' | gcloud secrets versions add ${ENVIRONMENT}-strands-pos-DATABASE_URL --data-file=-"
echo "2. Push code to your configured GitHub branch (${GITHUB_BRANCH}) to test the CI/CD pipeline."
echo ""
echo "Alternatively, for an immediate local deployment (if CI/CD is skipped), run:"
echo "gcloud builds submit --region ${REGION} --tag \$(terraform output -raw artifact_registry_repo)/strands-pos:latest ."
echo "gcloud run deploy strands-pos-${ENVIRONMENT} --image \$(terraform output -raw artifact_registry_repo)/strands-pos:latest --region ${REGION} --project ${PROJECT_ID} --quiet"
