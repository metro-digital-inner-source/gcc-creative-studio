# Three-Environment Deployment Setup

## Environment Structure ✅

Your repository is now configured for three environments:

| Environment | GCP Project | Git Branch | Purpose |
|------------|-------------|------------|---------|
| **Development** | `cf-genaistudi-genai-studio--gv` | `develop` | Active development and testing |
| **Pre-Production** | `cf-genaistudi-genai-studio--vm` | `test` | Final testing before production |
| **Production** | `cf-genaistudi-genai-studio--7u` | `main` | Live environment for end-users |

## ⚠️ Organization IAM Policy Compliance

Your organization **forbids**:
- ❌ Primitive roles (`roles/owner`, `roles/editor`, `roles/viewer`)
- ❌ Service account keys (must use Workload Identity Federation)
- ❌ Public IAM bindings (`allUsers`, `allAuthenticatedUsers`)
- ❌ Domain-wide role bindings

**All configurations in this repository comply with these policies.**

## Current Status

✅ Git branch structure configured  
✅ Project ID mappings corrected  
✅ Infrastructure compliance fixes applied (Secret Manager, PostgreSQL)  
✅ GitHub Actions workflow configured with WIF (no keys)  
⚠️ **Blocked**: Need service account setup with granular IAM roles

## Next Steps to Deploy

### Step 1: Set Up Terraform Service Accounts

**Option A: Have Your GCP Admin Run the Setup Script**

Send `infra/setup-terraform-service-accounts.sh` to your GCP admin:

```bash
cd /path/to/gcc-creative-studio
./infra/setup-terraform-service-accounts.sh
```

This script will:
- Create `terraform-deployer` service account in each project
- Grant required granular IAM roles (no primitive roles)
- Grant you impersonation rights
- Create Terraform state buckets

**Option B: Request Specific Permissions**

See [DEPLOYMENT_REQUIRED_PERMISSIONS.md](DEPLOYMENT_REQUIRED_PERMISSIONS.md) for the exact roles needed and request template.

### Step 2: Deploy to Development

Once service accounts are set up:

```bash
# Authenticate with impersonation (no keys!)
gcloud auth application-default login \
  --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com'

# Deploy to dev
cd infra/environments/dev
terraform init
terraform plan -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars
```

### Step 3: Run Bootstrap Script

After Terraform creates the base infrastructure, run the bootstrap:

```bash
cd /path/to/gcc-creative-studio
./bootstrap.sh
```

This will:
- Configure Firebase
- Create secrets
- Set up database schema
- Deploy initial services

### Step 4: Deploy to PP and Prod

Once dev is working, repeat for other environments:

**Pre-Production:**
```bash
git checkout test
gcloud auth application-default login \
  --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--vm.iam.gserviceaccount.com'

cd infra/environments/pp
terraform init
terraform plan -var-file=pp.tfvars
terraform apply -var-file=pp.tfvars
```

**Production:**
```bash
git checkout main
gcloud auth application-default login \
  --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--7u.iam.gserviceaccount.com'

cd infra/environments/prod
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

## CI/CD with GitHub Actions (No Keys Required!)

The workflow at `.github/workflows/terraform.yml` is configured to use **Workload Identity Federation**.

### Required GitHub Secrets

Your GCP admin needs to set up WIF and configure these secrets:

**For Dev environment:**
- `TF_WIF_PROVIDER_dev`: Workload Identity Provider resource name
- `TF_SA_EMAIL_dev`: `terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com`

**For PP environment:**
- `TF_WIF_PROVIDER_pp`: Workload Identity Provider resource name
- `TF_SA_EMAIL_pp`: `terraform-deployer@cf-genaistudi-genai-studio--vm.iam.gserviceaccount.com`

**For Prod environment:**
- `TF_WIF_PROVIDER_prod`: Workload Identity Provider resource name
- `TF_SA_EMAIL_prod`: `terraform-deployer@cf-genaistudi-genai-studio--7u.iam.gserviceaccount.com`

### Automated Deployments

- **Push to `develop`** → Auto-deploy to Dev
- **Push to `test`** → Auto-deploy to PP
- **Push to `main`** → Auto-deploy to Production

## Git Branch Protection Setup

Configure in GitHub Settings → Branches:

### For `develop` branch:
- ✅ Require pull request reviews (1 approval)
- ✅ Dismiss stale PR approvals

### For `test` branch (PP):
- ✅ Require pull request reviews (2 approvals)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date

### For `main` branch (Production):
- ✅ Require pull request reviews (2+ approvals)
- ✅ Require status checks to pass
- ✅ Require signed commits (recommended)
- ✅ Include administrators in restrictions
- ✅ Require linear history

## Configuration Fixes Applied ✅

Fixed in your local environment (gitignored):

1. **Project ID Mappings**: Corrected all three environments
2. **Backend Buckets**: Updated to match correct projects
3. **Secret Manager**: Added explicit replication policy (user-managed)
4. **PostgreSQL**: Added backups, password policies, logging flags
5. **GitHub Actions**: Fixed project IDs in workflow

## Verification Commands

After service accounts are set up:

```bash
# Verify impersonation works
gcloud auth application-default login \
  --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com'

# Verify Terraform config
cd infra/environments/dev
terraform init
terraform validate

# Check bucket access
gcloud storage ls --project=cf-genaistudi-genai-studio--gv
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  GitHub Repository                       │
│  (metro-digital-inner-source/gcc-creative-studio)       │
└────────────┬────────────┬────────────┬─────────────────┘
             │            │            │
      develop│     test   │      main  │
             │            │            │
             ▼            ▼            ▼
    ┌────────────┐ ┌─────────┐ ┌──────────┐
    │    Dev     │ │   PP    │ │   Prod   │
    │  Project   │ │ Project │ │ Project  │
    │   (--gv)   │ │  (--vm) │ │  (--7u)  │
    └────────────┘ └─────────┘ └──────────┘
         │              │            │
         └──────────────┴────────────┘
                     │
            Workload Identity
            Federation (No Keys!)
```

## Troubleshooting

**"Permission denied" errors?**
- Verify service account has all required roles
- Check impersonation is working: `gcloud auth list`

**"Bucket does not exist"?**
- Run `setup-terraform-service-accounts.sh` to create state buckets

**GitHub Actions failing?**
- Verify WIF is configured correctly
- Check GitHub secrets are set properly

## Need Help?

- **Setup service accounts**: Share `infra/setup-terraform-service-accounts.sh` with GCP admin
- **IAM permissions**: See [DEPLOYMENT_REQUIRED_PERMISSIONS.md](DEPLOYMENT_REQUIRED_PERMISSIONS.md)
- **Bootstrap issues**: Check `./bootstrap.sh` output logs
- **Terraform errors**: Run `terraform validate` in environment directory
