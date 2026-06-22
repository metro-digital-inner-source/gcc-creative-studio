# GenAI Studio Deployment Status

Date: 2026-06-21  
Environment: Development (`cf-genaistudi-genai-studio--gv`)  
Scope: Documentation snapshot for current deployment path

## Current Baseline

- Backend stack is provisioned and routable in dev.
- Frontend login regression from the latest deployment has been fixed in code:
  - Auth token injection remains scoped to backend API requests only.
  - The login flow no longer gets torn down by a forced logout during pre-login/background requests.
  - Backend allowlist lookup now uses proper FastAPI dependency injection.
- **Allowlist enforcement is now hardened and fail-closed:**
  - DB-only allowlist enforces access control even when env-var restrictions are empty.
  - Authorization fails safely (503) if DB checks fail without env fallback.
  - Case-insensitive email/domain/org comparisons prevent bypass via case variation.
  - Comprehensive unit tests validate DB-only, env fallback, and fail-closed paths.
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

## Verification Note

- After redeploying the fixed code, validate that login succeeds from a fresh browser session and that authenticated API calls no longer trigger the `User session is not valid or has expired. 2` error.

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
