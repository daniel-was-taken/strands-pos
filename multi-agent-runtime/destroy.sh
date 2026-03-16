#!/usr/bin/env bash
# destroy.sh — tear down all GCP resources managed by Terraform.
#
# Usage:
#   ./destroy.sh <project-id> [region]

set -euo pipefail

PROJECT_ID="${1:?Usage: ./destroy.sh <project-id> [region]}"
REGION="${2:-us-central1}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Destroying all Terraform-managed resources"
terraform destroy \
  -var="project_id=${PROJECT_ID}" \
  -var="region=${REGION}" \
  -auto-approve

echo "==> All resources destroyed."
