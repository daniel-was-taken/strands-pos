#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
INVOKER_USER_EMAIL=$(gcloud config get-value account)
REGION="us-central1"
ENVIRONMENT="production"
IMAGE_NAME="strands-pos"

echo "Deploying Strands POS to GCP ($ENVIRONMENT)"

# 1. Init & apply basic infrastructure First to get Artifact Registry
cd infra
terraform init
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="invoker_user_email=${INVOKER_USER_EMAIL}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=us-docker.pkg.dev/cloudrun/container/hello" \
  -auto-approve
cd ..

# 2. Build Docker Image
echo "Building container image with Cloud Build..."
IMAGE_TAG="us-central1-docker.pkg.dev/${PROJECT_ID}/strands-pos-${ENVIRONMENT}/${IMAGE_NAME}:latest"
gcloud builds submit \
  --region "${REGION}" \
  --default-buckets-behavior=regional-user-owned-bucket \
  --tag "${IMAGE_TAG}" \
  .

# 3. Image is already pushed by Cloud Build
echo "Image available in Artifact Registry: ${IMAGE_TAG}"

# 4. Apply infrastructure again to deploy the real image
echo "Deploying Cloud Run application..."
cd infra
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="invoker_user_email=${INVOKER_USER_EMAIL}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=${IMAGE_TAG}" \
  -auto-approve
cd ..

echo "Deploy complete!"

SERVICE_NAME="strands-pos-${ENVIRONMENT}"
LOCAL_PORT="${LOCAL_PORT:-8080}"

echo ""
echo "========================================="
echo " Cloud Run service deployed successfully"
echo "========================================="
echo ""
echo "The service requires authenticated access (org policy blocks allUsers)."
echo "Starting local proxy on http://127.0.0.1:${LOCAL_PORT}/ ..."
echo "Press Ctrl+C to stop the proxy."
echo ""

gcloud run services proxy "${SERVICE_NAME}" \
  --region "${REGION}" \
  --port "${LOCAL_PORT}"
