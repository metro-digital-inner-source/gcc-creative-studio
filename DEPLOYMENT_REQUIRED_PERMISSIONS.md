# Required IAM Permissions for Deployment

## ⚠️ Organization Policy Compliance

Your organization **forbids primitive roles** (`roles/owner`, `roles/editor`, `roles/viewer`). The bootstrap and deployment process requires specific granular roles.

## Required Roles for Bootstrap and Deployment

The person running the bootstrap script needs these **specific IAM roles** on all three GCP projects:

### Core Infrastructure Roles
- `roles/resourcemanager.projectIamAdmin` - Manage IAM policies
- `roles/iam.serviceAccountAdmin` - Create and manage service accounts
- `roles/iam.securityAdmin` - Manage security-related resources
- `roles/serviceusage.serviceUsageAdmin` - Enable/disable APIs

### Storage & Secrets
- `roles/storage.admin` - Create and manage GCS buckets (for Terraform state)
- `roles/secretmanager.admin` - Create and manage secrets

### Compute & Networking
- `roles/run.admin` - Deploy Cloud Run services
- `roles/compute.admin` - Manage compute resources
- `roles/cloudsql.admin` - Manage Cloud SQL instances

### Build & Deployment
- `roles/cloudbuild.builds.editor` - Manage Cloud Build
- `roles/artifactregistry.admin` - Manage Artifact Registry

### Firebase
- `roles/firebase.admin` - Manage Firebase resources
- `roles/firebasehosting.admin` - Manage Firebase Hosting

### Vertex AI
- `roles/aiplatform.admin` - Manage Vertex AI resources

### Workflows
- `roles/workflows.admin` - Manage Workflows

## Service Account for Terraform

Instead of using your user account, create a **dedicated service account** for Terraform deployments:

```bash
# Run this with appropriate permissions (or ask your GCP admin)
export PROJECT_ID="cf-genaistudi-genai-studio--gv"

# Create Terraform service account
gcloud iam service-accounts create terraform-deployer \
  --display-name="Terraform Deployment Service Account" \
  --project=$PROJECT_ID

# Grant required roles
for role in \
  "roles/resourcemanager.projectIamAdmin" \
  "roles/iam.serviceAccountAdmin" \
  "roles/iam.securityAdmin" \
  "roles/serviceusage.serviceUsageAdmin" \
  "roles/storage.admin" \
  "roles/secretmanager.admin" \
  "roles/run.admin" \
  "roles/compute.admin" \
  "roles/cloudsql.admin" \
  "roles/cloudbuild.builds.editor" \
  "roles/artifactregistry.admin" \
  "roles/firebase.admin" \
  "roles/firebasehosting.admin" \
  "roles/aiplatform.admin" \
  "roles/workflows.admin"; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$role"
done

# Allow your user to impersonate this service account
gcloud iam service-accounts add-iam-policy-binding \
  terraform-deployer@${PROJECT_ID}.iam.gserviceaccount.com \
  --member="user:joejoseph.george@metro.digital" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=$PROJECT_ID
```

## Keyless Authentication (Organization Requirement)

Your organization **forbids service account keys**. Use these alternatives:

### For Local Development

Use service account impersonation:

```bash
# Authenticate with impersonation
gcloud auth application-default login \
  --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com'

# Then run Terraform
cd infra/environments/dev
terraform init
terraform plan -var-file=dev.tfvars
```

### For GitHub Actions (CI/CD)

Use **Workload Identity Federation** (no keys required). Your `project-cfg` module should set this up automatically.

The workflow is already prepared at `.github/workflows/terraform.yml`.

## Request Template for GCP Admin

Send this to your GCP admin:

---

**Subject**: Request: Terraform Deployment Service Account Setup

Hi [Admin Name],

I need to deploy the Creative Studio infrastructure to our three GCP projects. Per our organization's IAM policies (no primitive roles, no SA keys), I need a Terraform service account with specific granular roles.

**Projects**:
- Dev: `cf-genaistudi-genai-studio--gv`
- PP: `cf-genaistudi-genai-studio--vm`
- Prod: `cf-genaistudi-genai-studio--7u`

**Required Actions**:
1. Create service account `terraform-deployer` in each project
2. Grant the roles listed in `DEPLOYMENT_REQUIRED_PERMISSIONS.md`
3. Allow me (`joejoseph.george@metro.digital`) to impersonate these service accounts

See attached file for the exact commands.

Thanks!

---

## Alternative: Admin Runs Bootstrap

If setting up service accounts is complex, your GCP admin can run the bootstrap script directly:

```bash
# Admin with appropriate permissions runs:
cd /path/to/gcc-creative-studio
./bootstrap.sh

# Follow prompts for each environment (dev, pp, prod)
```

## Verification

Once permissions are granted, verify with:

```bash
# Test impersonation
gcloud auth application-default login \
  --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com'

# Test Terraform
cd infra/environments/dev
terraform init
terraform validate
```

## Important: No Service Account Keys

❌ **Never create or use service account keys** - this violates org policy  
✅ **Always use impersonation** for local development  
✅ **Always use Workload Identity Federation** for GitHub Actions
