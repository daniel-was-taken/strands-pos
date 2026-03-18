# GCP Deployment Troubleshooting Runbook

This document records the errors encountered during the GCP deployment of this repository and the fixes that led to a working Cloud Run deployment.

## Final Working State

- Infrastructure applied successfully with Terraform from `infra/`
- Docker image built and pushed to Artifact Registry
- Cloud Run service deployed and reachable through `gcloud run services proxy`
- CI/CD trigger configured against the active branch instead of `main`
- Secrets stored in Secret Manager with versions populated outside Terraform state

## Standard Deployment Sequence

1. Bootstrap infrastructure with Terraform.
2. Build and push the container image to Artifact Registry.
3. Populate Secret Manager secret versions.
4. Re-apply Terraform so Cloud Run references the real image and existing secrets.
5. Enable CI/CD after GitHub repository mapping is connected in Cloud Build.
6. Verify access using `gcloud run services proxy`.

## Error Log And Fixes

### 1. Cloud Run image not found during initial Terraform apply

Error:

```text
Image 'us-central1-docker.pkg.dev/<gcp-project-id>/strands-pos-production/strands-pos:latest' not found.
```

Cause:

- Terraform attempted to create the Cloud Run service before the first real container image had been built and pushed.

Fix applied:

- Updated Terraform to use a safe placeholder image on first deploy:

```text
us-docker.pkg.dev/cloudrun/container/hello
```

- Built and pushed the real image after the initial infrastructure bootstrap.

Commands used:

```bash
gcloud builds submit \
  --region us-central1 \
  --default-buckets-behavior=regional-user-owned-bucket \
  --tag $(cd infra && terraform output -raw artifact_registry_repo)/strands-pos:latest \
  .
```

Then:

```bash
cd infra
terraform apply \
  -var="project_id=<gcp-project-id>" \
  -var="container_image=$(terraform output -raw artifact_registry_repo)/strands-pos:latest" \
  -auto-approve
```

### 2. Cloud Build failed with resource location policy error

Error:

```text
HTTPError 412: 'us' violates constraint 'constraints/gcp.resourceLocations'
```

Cause:

- Cloud Build defaulted to a multi-region bucket in `us`, but the project org policy only allowed approved single regions.

Fix applied:

- Forced Cloud Build to use a regional user-owned bucket.

Command used:

```bash
gcloud builds submit \
  --region us-central1 \
  --default-buckets-behavior=regional-user-owned-bucket \
  --tag $(cd infra && terraform output -raw artifact_registry_repo)/strands-pos:latest \
  .
```

### 3. Cloud Run failed because Secret Manager versions were missing

Error:

```text
Secret .../versions/latest was not found
```

Cause:

- Terraform created Secret Manager secret resources, but secret versions were intentionally not created by Terraform to avoid storing plaintext in state.

Fix applied:

- Added secret versions manually from local environment values.

Commands used:

```bash
source .env

echo -n "$DATABASE_URL" | gcloud secrets versions add production-strands-pos-DATABASE_URL --data-file=-
echo -n "$NEON_API_KEY" | gcloud secrets versions add production-strands-pos-NEON_API_KEY --data-file=-
echo -n "$NEON_PROJECT_ID" | gcloud secrets versions add production-strands-pos-NEON_PROJECT_ID --data-file=-
echo -n "$NEON_DATABASE" | gcloud secrets versions add production-strands-pos-NEON_DATABASE --data-file=-
echo -n "$NEON_BRANCH" | gcloud secrets versions add production-strands-pos-NEON_BRANCH --data-file=-
```

### 4. Artifact Registry IAM update failed with 403

Error:

```text
Error retrieving IAM policy for artifactregistry repository ... Error 403: The caller does not have permission
```

Causes:

- The operator account lacked permission to manage Artifact Registry IAM.
- The Cloud Build Terraform module was also targeting a hardcoded repository name instead of the real repository ID.

Fixes applied:

- Updated Terraform so the Cloud Build module receives the actual `repository_id` from the Artifact Registry module.
- Granted the operator sufficient Artifact Registry IAM permissions.

Command used:

```bash
gcloud projects add-iam-policy-binding <gcp-project-id> \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/artifactregistry.admin"
```

### 5. Cloud Build trigger creation failed because repository mapping did not exist

Error:

```text
Repository mapping does not exist. Please visit .../cloud-build/triggers.../connect
```

Cause:

- Cloud Build had not yet been connected to the GitHub repository in the target GCP project.

Fix applied:

- Connected the repository manually in the Cloud Build console.
- Made CI/CD creation optional in Terraform until that connection was ready.

Operational rule:

- Apply Terraform with `enable_cicd=false` until the GitHub repo is connected.
- Re-apply with `enable_cicd=true` once repository mapping exists.

### 6. CI/CD branch mismatch

Problem:

- The deployment changes existed on the active feature branch, not on `main`.

Fix applied:

- Pointed the Cloud Build trigger at the active branch instead of `main`.

Terraform apply used:

```bash
cd infra
terraform apply \
  -var="project_id=<gcp-project-id>" \
  -var="container_image=$(terraform output -raw artifact_registry_repo)/strands-pos:latest" \
  -var="github_owner=<github-owner>" \
  -var="github_repo=<github-repo>" \
  -var="github_branch=<deployment-branch>" \
  -var="enable_cicd=true" \
  -auto-approve
```

### 7. Terraform local state lock after interrupting apply with Ctrl+Z

Errors observed:

```text
Error acquiring the state lock
```

and:

```text
Local state cannot be unlocked by another process
```

Cause:

- Terraform was suspended, not terminated. The stopped `terraform` process and provider process still held the local lock.

Fix applied:

- Identified stopped Terraform processes.
- Killed them with `kill -9`.
- Removed the stale local lock file.

Commands used:

```bash
ps aux | grep '[t]erraform'
kill -9 <terraform_pid> <provider_pid>
rm -f .terraform.tfstate.lock.info
```

If needed, reinitialize afterwards:

```bash
terraform init -reconfigure
```

### 8. Local Cloud Run proxy failed because port 8080 was already in use

Error:

```text
listen tcp 127.0.0.1:8080: bind: address already in use
```

Cause:

- A previous `gcloud run services proxy` process was already listening on port `8080`.

Fix applied:

- Located the process and either reused it, killed it, or chose another port.

Commands used:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
kill <proxy_pid>
```

Or start on another port:

```bash
gcloud run services proxy strands-pos-production --region us-central1 --port 8081
```

## Commands For Current Working Deployment

### Describe the deployed Cloud Run URL

```bash
gcloud run services describe strands-pos-production \
  --region us-central1 \
  --format='value(status.url)'
```

### Start local authenticated proxy

```bash
gcloud run services proxy strands-pos-production --region us-central1 --port 8080
```

### Test locally

```bash
curl http://127.0.0.1:8080
```

### Stop the local proxy

Find the process:

```bash
lsof -nP -iTCP:8080 -sTCP:LISTEN
```

Kill it:

```bash
kill <pid>
```

If it does not stop cleanly:

```bash
kill -9 <pid>
```

## Shareability Notes

- `http://127.0.0.1:8080` is local-only and cannot be shared.
- The real Cloud Run URL can be shared only with users who have `roles/run.invoker` and are authenticated.

## Recommended Next Steps

1. Push the active branch and confirm the Cloud Build trigger fires.
2. Grant `roles/run.invoker` to any teammate who needs access.
3. Merge the deployment branch into `main` when ready so the trigger can follow the production branch.