# GitHub Actions & Terraform CI/CD Setup — Implementation Guide

## Overview

This document walks through the infrastructure-as-code and GitHub Actions setup for the `gcc-creative-studio` repository. The setup enables:

- **Terraform-driven infrastructure** for dev, pre-prod, and production GCP projects
- **GitHub Actions workflows** for quality gates and Terraform plan/apply with WIF (Workload Identity Federation) authentication
- **Automated Cloud Build trigger creation** via Terraform modules
- **Branch protection rules** with required status checks

## What Was Created

### 1. WIF Bootstrap Script
**File**: `infra/bootstrap/wif-setup.sh`

Sets up Workload Identity Federation for one GCP project. Automates:
- Terraform Service Account creation
- IAM role assignments
- WIF Pool and GitHub OIDC Provider creation
- Workload Identity bindings per branch

**Usage**:
```bash
cd infra/bootstrap
chmod +x wif-setup.sh
./wif-setup.sh <GCP_PROJECT_ID> <GITHUB_REPO_OWNER> <GITHUB_REPO_NAME> <ENVIRONMENT> <BRANCH>

# Example:
./wif-setup.sh cf-genaistudi-genai-studio--vm metro-digital-inner-source gcc-creative-studio dev develop
./wif-setup.sh cf-genaistudi-genai-studio--7u metro-digital-inner-source gcc-creative-studio pp test
./wif-setup.sh cf-genaistudi-genai-studio--gv metro-digital-inner-source gcc-creative-studio prod main
```

### 2. Terraform Environment Configurations

**Three new environment directories created**:

- **`infra/environments/dev/`** — Development (branch: `develop`, project: `cf-genaistudi-genai-studio--vm`)
  - GCS state bucket: `cf-genaistudi-genai-studio--vm-tfstate`
  - Backend/Frontend service names: `cstudio-backend-dev`, `cstudio-frontend-dev`
  - Firebase site: `cstudio-dev-metro`

- **`infra/environments/pp/`** — Pre-production (branch: `test`, project: `cf-genaistudi-genai-studio--7u`)
  - GCS state bucket: `cf-genaistudi-genai-studio--7u-tfstate`
  - Backend/Frontend service names: `cstudio-backend-pp`, `cstudio-frontend-pp`
  - Firebase site: `cstudio-pp-metro`

- **`infra/environments/prod/`** — Production (branch: `main`, project: `cf-genaistudi-genai-studio--gv`)
  - GCS state bucket: `cf-genaistudi-genai-studio--gv-tfstate`
  - Backend/Frontend service names: `cstudio-backend-prod`, `cstudio-frontend-prod`
  - Firebase site: `cstudio-prod-metro`
  - Higher resource allocation: `be_cpu=2`, `be_memory=1Gi` (vs dev `be_cpu=1`, `be_memory=512Mi`)

Each environment directory contains:
- `main.tf` — Provider setup and platform module call
- `variables.tf` — Variable definitions
- `backend.tf` — GCS backend configuration
- `outputs.tf` — Output values
- `{env}.tfvars` — Environment-specific values

### 3. GitHub Actions Workflow
**File**: `.github/workflows/terraform.yml`

Automated Terraform CI/CD workflow:
- **Trigger**: PRs and pushes to `main`, `develop`, `test` touching `infra/**`
- **Jobs**:
  - `detect-env` — Maps branch to environment (develop→dev, test→pp, main→prod)
  - `terraform-plan` — Runs on PR, posts plan output as PR comment
  - `terraform-apply` — Runs on push, authenticates via WIF, applies Terraform

---

## Phase 1: Bootstrap Prerequisites *(Manual steps — One-time)*

### Step 1: Create GCS State Buckets

Create three Google Cloud Storage buckets for Terraform state (one per GCP project):

```bash
# Development
gsutil mb -p cf-genaistudi-genai-studio--vm gs://cf-genaistudi-genai-studio--vm-tfstate
gsutil versioning set on gs://cf-genaistudi-genai-studio--vm-tfstate

# Pre-production
gsutil mb -p cf-genaistudi-genai-studio--7u gs://cf-genaistudi-genai-studio--7u-tfstate
gsutil versioning set on gs://cf-genaistudi-genai-studio--7u-tfstate

# Production
gsutil mb -p cf-genaistudi-genai-studio--gv gs://cf-genaistudi-genai-studio--gv-tfstate
gsutil versioning set on gs://cf-genaistudi-genai-studio--gv-tfstate
```

### Step 2: Create Cloud Build GitHub Connections

In each GCP project, create a 2nd-gen Cloud Build GitHub connection:

1. **GCP Console** → Cloud Build → Repositories → **Create GitHub Connection**
2. Name: `metro-inner-source-con`
3. Authenticate with GitHub
4. Authorize for repo: `metro-digital-inner-source/gcc-creative-studio`
5. Click **Create**

*(This must be done in the Console — cannot be automated. Do this for all 3 projects.)*

### Step 3: Run WIF Bootstrap Script

For each GCP project, authenticate and run the WIF setup script:

```bash
# Set your GitHub personal access token for gcloud authentication
gcloud auth login

# Development
./infra/bootstrap/wif-setup.sh cf-genaistudi-genai-studio--vm metro-digital-inner-source gcc-creative-studio dev develop

# Pre-production
./infra/bootstrap/wif-setup.sh cf-genaistudi-genai-studio--7u metro-digital-inner-source gcc-creative-studio pp test

# Production
./infra/bootstrap/wif-setup.sh cf-genaistudi-genai-studio--gv metro-digital-inner-source gcc-creative-studio prod main
```

**Output**: The script prints GitHub Secrets that need to be configured (see Step 4).

### Step 4: Configure GitHub Secrets

In your GitHub repository settings (`Settings` → `Secrets and variables` → `Actions`), add the following secrets based on WIF bootstrap output:

**From `dev` WIF bootstrap**:
- `TF_WIF_PROVIDER_DEV` — WIF provider resource path (e.g., `projects/12345/locations/global/workloadIdentityPools/github-pool/providers/github-provider`)
- `TF_SA_EMAIL_DEV` — Terraform SA email (e.g., `terraform-sa@cf-genaistudi-genai-studio--vm.iam.gserviceaccount.com`)

**From `pp` WIF bootstrap**:
- `TF_WIF_PROVIDER_PP`
- `TF_SA_EMAIL_PP`

**From `prod` WIF bootstrap**:
- `TF_WIF_PROVIDER_PROD`
- `TF_SA_EMAIL_PROD`

**For Gemini Review workflow** (already exists):
- `GEMINI_API_KEY` — Your Gemini API key from Google AI Studio

### Step 5: Load Secrets into Secret Manager

For each GCP project, pre-load the Firebase and OAuth secrets that the build process needs:

```bash
# Example for development project — adjust for each environment/project
gcloud secrets create FIREBASE_API_KEY \
  --data-file=- \
  --project=cf-genaistudi-genai-studio--vm <<< "YOUR_FIREBASE_API_KEY"

gcloud secrets create FIREBASE_AUTH_DOMAIN \
  --data-file=- \
  --project=cf-genaistudi-genai-studio--vm <<< "creative-studio-dev.firebaseapp.com"

# ... (repeat for all frontend_secrets and backend_secrets listed in tfvars)
```

Or automate this using the `update_secrets.sh` script in each environment directory.

---

## Phase 2: Customize Terraform Configurations

Each `{env}.tfvars` file has placeholder values that must be customized:

### `infra/environments/dev/dev.tfvars`
```hcl
# TODO: Replace placeholders
backend_custom_audiences  = ["YOUR_OAUTH_WEB_CLIENT_ID_HERE", "cf-genaistudi-genai-studio--vm"]
frontend_custom_audiences = ["YOUR_OAUTH_WEB_CLIENT_ID_HERE", "cf-genaistudi-genai-studio--vm"]
# ... (GOOGLE_TOKEN_AUDIENCE, IDENTITY_PLATFORM_ALLOWED_ORGS, Firebase credentials)
```

Do the same for `pp/pp.tfvars` and `prod/prod.tfvars`, substituting:
- Project IDs
- OAuth Client IDs
- Firebase credentials
- Identity Platform org restrictions

---

## Phase 3: Set up GitHub Environments & Branch Protection

### Create GitHub Environments

1. **Settings** → **Environments** → **New environment**
2. Create three: `dev`, `pp`, `prod`
3. For `prod` environment:
   - Add required reviewers (e.g., METRO maintainers)
   - Check "Prevent forking workflows from approving deployments"

### Enable Branch Protection Rules

1. **Settings** → **Branches** → **Add rule**

**For `main` branch**:
- Require pull request reviews before merging (≥ 1)
- Require status checks to pass:
  - `Backend Quality` (if backend touched)
  - `Frontend Quality` (if frontend touched)
  - `License Header Check`
  - `terraform-plan` (if infra touched)
  - `Terraform CI/CD / terraform-plan`
- Dismiss stale pull request approvals
- Require branches to be up to date

**For `develop` branch**:
- Same as `main`

**For `test` branch**:
- Same as `main`

---

## Phase 4: First Terraform Run (Manual)

Before GitHub Actions can apply Terraform, you must run it once locally to initialize state:

```bash
cd infra/environments/dev
terraform init
terraform plan -var-file=dev.tfvars
# Review plan output
terraform apply -var-file=dev.tfvars
```

After this first successful run:
- State file is stored in GCS
- Cloud Build triggers are created by the platform module
- Cloud Run services are provisioned
- GitHub Actions can take over for future changes

---

## Workflow Usage

### Creating a Terraform Change

1. Create a branch from `develop` (for dev changes)
2. Modify `infra/environments/dev/{main,variables}.tf` or `dev.tfvars`
3. Push and open a PR to `develop`
4. **GitHub Actions will**:
   - Run `terraform plan` for dev environment
   - Post the plan output as a PR comment
   - Run all quality checks (backend, frontend, license)
5. After review and approval, merge to `develop`
6. **GitHub Actions will**:
   - Run `terraform apply` for dev environment
   - Create/update Cloud Run services, Cloud SQL, storage, etc.
   - Cloud Build triggers fire and deploy the latest main/develop branches

### Promoting Changes to Production

1. When ready, merge `develop` → `test` (triggers pp environment)
2. Test in pre-prod environment
3. When confident, merge `test` → `main` (triggers prod environment)
4. **Production apply requires manual approval** from environment reviewers (configured in GitHub Environments)

---

## Troubleshooting

### `terraform plan` fails with "Error acquiring the state lock"
The GCS bucket doesn't have versioning enabled. Run:
```bash
gsutil versioning set on gs://cf-genaistudi-genai-studio--vm-tfstate
```

### `terraform apply` fails with "Insufficient permissions"
Ensure the Terraform SA has all required roles. Re-run the WIF bootstrap script to verify role assignments.

### GitHub Actions can't authenticate to GCP
Check that:
1. `TF_WIF_PROVIDER_*` and `TF_SA_EMAIL_*` secrets are correctly set
2. The WIF pool and provider exist in the GCP project
3. The branch matches the workload identity binding (e.g., `refs/heads/develop` for dev)

### Terraform state bucket not found
Ensure GCS buckets exist and are named exactly as in `backend.tf` (e.g., `cf-genaistudi-genai-studio--vm-tfstate`).

---

## Next Steps

1. ✅ Complete all Phase 1 manual bootstrap steps (above)
2. ✅ Customize tfvars files with your OAuth credentials
3. ✅ Run first `terraform apply` manually to initialize state
4. ✅ Verify GitHub Actions workflow succeeds on a test PR
5. Set up monitoring and alerting (Datadog, GCP Cloud Monitoring)
6. Enable continuous deployment to staging environments
7. Document your architecture in Confluence per METRO standards

---

## Files Reference

| File | Purpose |
|---|---|
| `infra/bootstrap/wif-setup.sh` | WIF SA + pool creation |
| `infra/environments/dev/main.tf` | Dev environment provider & platform module |
| `infra/environments/dev/dev.tfvars` | Dev environment variable values (customize!) |
| `infra/environments/pp/main.tf` | Pre-prod environment |
| `infra/environments/pp/pp.tfvars` | Pre-prod values |
| `infra/environments/prod/main.tf` | Production environment |
| `infra/environments/prod/prod.tfvars` | Production values |
| `.github/workflows/terraform.yml` | GitHub Actions Terraform workflow |

---

**Status**: Implementation complete. Awaiting Phase 1 manual bootstrap completion.
