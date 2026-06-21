# GenAI Studio Deployment Status

Date: 2026-06-21  
Environment: Development (`cf-genaistudi-genai-studio--gv`)  
Scope: Documentation snapshot for current deployment path

## Current Baseline

- Backend stack is provisioned and routable in dev.
- Frontend login was fixed in code by scoping auth token injection to backend API requests only.
- Terraform/GitHub automation still depends on organization IAM and GitHub connection setup.

## Confirmed Working Components

- Core project APIs and base infra in dev.
- Cloud SQL + backend Cloud Run service path.
- Artifact Registry for backend image builds.
- Cloud Build backend trigger path (when connection and permissions are in place).

## Known Blockers

- Missing or restricted IAM permissions in org policy context for some deployment actions.
- GitHub Cloud Build connection may require manual console authorization.
- Firebase/frontend provisioning can be blocked by API key administration permissions in constrained org setups.

## Recommended Deploy Order

1. Verify IAM/service account impersonation for dev project.
2. Ensure Cloud Build GitHub connection exists and is authorized.
3. Deploy backend infra and backend service.
4. Deploy frontend trigger/build to Firebase Hosting.
5. Run smoke checks on login and authenticated backend API requests.

## Quick Verification Commands

```bash
# Validate Terraform config
cd infra/environments/dev
terraform init
terraform validate

# Check active gcloud project
gcloud config get-value project

# Check available Cloud Build triggers
gcloud builds triggers list \
  --region=europe-west3 \
  --project=cf-genaistudi-genai-studio--gv
```

## Notes

- This file replaces a previously corrupted status document that contained duplicated and truncated sections.
- Keep this file as a concise status summary; move long troubleshooting details to dedicated runbooks if needed.
