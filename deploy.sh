#!/usr/bin/env bash

set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ENVIRONMENT="production"
IMAGE_NAME="strands-pos"

echo "Deploying Strands POS to GCP ($ENVIRONMENT)"

# 1. Init & apply basic infrastructure First to get Artifact Registry
cd infra
terraform init
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=us-docker.pkg.dev/cloudrun/container/hello" \
  -auto-approve
cd ..

# 2. Build Docker Image
echo "Building docker image..."
IMAGE_TAG="us-central1-docker.pkg.dev/${PROJECT_ID}/strands-pos-${ENVIRONMENT}/${IMAGE_NAME}:latest"
docker tag strands-pos:latest ${IMAGE_TAG} 2>/dev/null || docker build -t ${IMAGE_TAG} .

# 3. Push Image to Artifact Registry
echo "Pushing image to Artifact Registry..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
docker push ${IMAGE_TAG}

# 4. Apply infrastructure again to deploy the real image
echo "Deploying Cloud Run application..."
cd infra
terraform apply \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=${IMAGE_TAG}" \
  -auto-approve
cd ..

echo "Deploy complete!"
