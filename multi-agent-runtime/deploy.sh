#!/usr/bin/env bash
# deploy.sh — build, push, and deploy the Strands POS application to GCP.
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated (`gcloud auth login`)
#   2. Terraform >= 1.5 installed
#   3. A GCP project with billing enabled
#   4. A GCS bucket for Terraform state (see backend.tf.example)
#
# Usage:
#   ./deploy.sh <project-id> [region]
#
# Example:
#   ./deploy.sh my-gcp-project us-central1

set -euo pipefail

PROJECT_ID="${1:?Usage: ./deploy.sh <project-id> [region]}"
REGION="${2:-us-central1}"
IMAGE_NAME="strands-pos"
REPO_NAME="strands-pos"
TAG="${TAG:-latest}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Authenticating Docker with Artifact Registry"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Initializing Terraform"
cd "$SCRIPT_DIR"
terraform init

echo "==> Applying Terraform (infrastructure only — creates registry, secrets, Cloud Run service, Cloud Build trigger)"
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -auto-approve

REGISTRY_URL=$(terraform output -raw artifact_registry_url)
FULL_IMAGE="${REGISTRY_URL}/${IMAGE_NAME}:${TAG}"

echo "==> Building Docker image"
cd "$REPO_ROOT"
docker build -t "$FULL_IMAGE" .

echo "==> Pushing image to Artifact Registry"
docker push "$FULL_IMAGE"

echo "==> Deploying new image to Cloud Run"
SERVICE_NAME=$(cd "$SCRIPT_DIR" && terraform output -raw service_name)
gcloud run deploy "$SERVICE_NAME" \
  --image "$FULL_IMAGE" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --quiet

SERVICE_URL=$(cd "$SCRIPT_DIR" && terraform output -raw service_url)
echo ""
echo "==> Deployment complete!"
echo "    Service URL: ${SERVICE_URL}"
