#!/usr/bin/env bash

set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ENVIRONMENT="production"

echo "Destroying Strands POS infrastructure on GCP ($ENVIRONMENT)"

cd infra
terraform destroy \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -var="environment=${ENVIRONMENT}" \
  -var="container_image=us-docker.pkg.dev/cloudrun/container/hello" \
  -auto-approve
cd ..

echo "Destroy complete!"
