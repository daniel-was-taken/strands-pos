# AWS to GCP Migration Report

## Side-by-side Summary

| Component | AWS-era Pattern | GCP Production-Ready Pattern |
| --------- | --------------- | ---------------------------- |
| **Infra Structure** | Non-modular CloudFormation / generic TF | Modular Terraform (`artifact-registry`, `cloudrun-runtime`, `cloudbuild-pipeline`) |
| **Container Registry** | Amazon ECR | Artifact Registry |
| **Compute** | ECS Fargate & ALB | Cloud Run (Authenticated invoker access) |
| **CI/CD** | AWS CodeBuild / manual | Cloud Build triggered by GitHub. Modular build/push/deploy pattern |
| **Runtime Config**| Implicit boto3 AWS configs | Explicit GCP `GOOGLE_CLOUD_PROJECT` & `GOOGLE_CLOUD_LOCATION` configuring Vertex AI SDK & Gemini API |
| **Secret Management** | AWS Secrets Manager (plaintext in TF) | GCP Secret Manager (Secrets NOT embedded in TF state. Dynamic injections at runtime for security) |

## Risks & Mitigations

1. **Risk:** Unauthenticated invocations exposing the API publicly.
   * **Mitigation:** Cloud Run requires authenticated invoker access by default (no `allUsers`). Handled by assigning `roles/run.invoker` explicitly by user email or via `gcloud run services proxy` locally.

2. **Risk:** Plaintext secret values leaking in Terraform state files.
   * **Mitigation:** Replaced `google_secret_manager_secret_version` blocks with out-of-band secret bootstrapping. Infrastructure creates the empty secret resource containers cleanly, protecting state files.
   
3. **Risk:** Inferred API region mismatches for Gemini.
   * **Mitigation:** Vertex AI strictly scoped using `GOOGLE_CLOUD_LOCATION` overriding ambient fallbacks guaranteeing predictable inference execution.

## Cost & Scaling Comparison

* **Min Instances:** In ECS Fargate, scaling down generally involved fixed minimal baselines or ALB fixed costs. Here, `min_instance_count` defaults to `0` resulting in **zero cost** while idle. Set higher (e.g. `1`) only if cold starts affect critical warm capacity, justifying the additional baseline cost.
* **Network & Ingress:** AWS ALB ingress drives constant baseline monthly costs. GCP Cloud Run routing includes baseline HTTP(S) load balancing natively requiring zero standing instance fees. 

## Final Recommendation
Adopt the current combined GCP topology permanently. It leverages true Serverless patterns (scale to zero), secures secrets appropriately, establishes seamless CI/CD bridging with Cloud Build natively, and explicitly conforms to GCP Vertex AI integrations.

## Rollback Plan
1. Retrieve prior AWS credentials.
2. If reverting completely, re-establish ECS cluster via the original `infra/ecs-stack.yml` (from commit `7679020`).
3. Point `.env` / runtime targets back to `strands-agents` via Gemini AI Studio (no vertexAI bindings).
4. Remove the remaining infrastructure by executing `./destroy.sh` pointing to the GCP Terraform outputs.