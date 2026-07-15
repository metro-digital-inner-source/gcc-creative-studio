# Additional IAM Roles Needed for genaistudio.genai-studio-dev-manager

## Current Roles (Already Assigned)
✅ `organizations/1049006825317/roles/CF_Project_Manager`  
✅ `organizations/1049006825317/roles/CF_Project_Billing_Viewer`  
✅ `roles/browser`  
✅ `roles/cloudsupport.techSupportEditor`

## Additional Roles Required for Deployment

### Core Infrastructure & State Management
```
roles/storage.admin
```
**Why:** Create and manage Terraform state buckets (gs://...-tfstate)  
**Permissions:** storage.buckets.create, storage.buckets.update, storage.objects.*

### Service Account & IAM Management
```
roles/iam.serviceAccountAdmin
roles/iam.securityAdmin
```
**Why:** Create terraform-deployer service accounts and manage IAM policies  
**Permissions:** iam.serviceAccounts.create, iam.serviceAccounts.setIamPolicy, resourcemanager.projects.setIamPolicy

### Database Management
```
roles/cloudsql.admin
```
**Why:** Deploy and configure Cloud SQL PostgreSQL instances  
**Permissions:** cloudsql.instances.*, cloudsql.databases.*, cloudsql.users.*

### Application Services
```
roles/run.admin
```
**Why:** Deploy backend Cloud Run services  
**Permissions:** run.services.*, run.routes.*, run.configurations.*

```
roles/artifactregistry.admin
```
**Why:** Create and manage container registries for Docker images  
**Permissions:** artifactregistry.repositories.*, artifactregistry.dockerimages.*

### Firebase & Hosting
```
roles/firebase.admin
roles/firebasehosting.admin
```
**Why:** Configure Firebase project and deploy frontend to Firebase Hosting  
**Permissions:** firebase.projects.*, firebasehosting.sites.*

### AI/ML Platform
```
roles/aiplatform.admin
```
**Why:** Use Vertex AI for image/video generation and multimodal features  
**Permissions:** aiplatform.endpoints.*, aiplatform.models.*

### Workflows & Orchestration
```
roles/workflows.admin
```
**Why:** Deploy and manage Workflow definitions  
**Permissions:** workflows.workflows.*, workflows.executions.*

### Secrets Management
```
roles/secretmanager.admin
```
**Why:** Create and manage API keys and credentials in Secret Manager  
**Permissions:** secretmanager.secrets.*, secretmanager.versions.*

### API Enablement
```
roles/serviceusage.serviceUsageAdmin
```
**Why:** Enable required GCP APIs programmatically  
**Permissions:** serviceusage.services.enable, serviceusage.services.disable

### Build & CI/CD
```
roles/cloudbuild.builds.editor
```
**Why:** Trigger Cloud Build for container builds  
**Permissions:** cloudbuild.builds.create, cloudbuild.builds.get

### Networking (if using VPC)
```
roles/compute.networkAdmin
```
**Why:** Manage VPC networks, subnets, and firewall rules  
**Permissions:** compute.networks.*, compute.firewalls.*, compute.subnetworks.*

---

## Summary: Copy-Paste Request for Support Ticket

**To:** Cloud Foundation Team  
**Subject:** Grant Additional Roles to genaistudio.genai-studio-dev-manager

**Request:**

Please grant the following roles to `genaistudio.genai-studio-dev-manager@cloudfoundation.metro.digital` in these projects:

**Projects:**
- `cf-genaistudi-genai-studio--gv` (Dev)
- `cf-genaistudi-genai-studio--vm` (PP)
- `cf-genaistudi-genai-studio--7u` (Prod)

**Additional Roles (Granular, No Primitive Roles):**
```
roles/storage.admin
roles/iam.serviceAccountAdmin
roles/iam.securityAdmin
roles/serviceusage.serviceUsageAdmin
roles/cloudsql.admin
roles/run.admin
roles/artifactregistry.admin
roles/firebase.admin
roles/firebasehosting.admin
roles/aiplatform.admin
roles/workflows.admin
roles/secretmanager.admin
roles/cloudbuild.builds.editor
roles/compute.networkAdmin
```

**Purpose:** Deploy GenAI Studio infrastructure using Terraform

**Compliance:** All roles are granular (no primitive roles: editor/owner/viewer)

**Ticket Reference:** Related to SDCAMPUSDE-93888 (but using keyless approach)

---

## Alternative: Minimum Viable Permissions

If full admin roles are too broad, here are the minimum specific permissions needed:

### For Initial Setup Only:
- `storage.buckets.create`
- `storage.buckets.update`
- `storage.buckets.get`
- `iam.serviceAccounts.create`
- `iam.serviceAccounts.setIamPolicy`
- `resourcemanager.projects.setIamPolicy`

### For Terraform Deployment:
- All resources: `*.create`, `*.update`, `*.get`, `*.delete`
- For: cloudsql, run, secretmanager, firebase, aiplatform, workflows, artifactregistry

---

## Testing After Permissions Are Granted

Once roles are added, verify with:

```bash
# Test bucket creation
gcloud storage buckets create gs://cf-genaistudi-genai-studio--gv-tfstate \
  --project=cf-genaistudi-genai-studio--gv \
  --location=europe-west3 \
  --uniform-bucket-level-access

# Test service account creation
gcloud iam service-accounts create test-sa \
  --display-name="Test SA" \
  --project=cf-genaistudi-genai-studio--gv

# If successful, proceed with deployment
cd infra/environments/dev
terraform init
terraform plan -var-file=dev.tfvars
```
