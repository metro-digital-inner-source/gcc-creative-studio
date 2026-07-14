# Feedback Deploy Checklist (Develop)

This checklist covers Terraform/GitHub Actions deployment and post-deploy verification for feedback auth/group/workspace fixes.

## 1. Preconditions

- Branch target: `develop`
- Terraform workflow file: `.github/workflows/terraform.yml`
- Expected environment mapping: `develop -> dev -> cf-genaistudi-genai-studio--gv`

## 2. GitHub Actions Secret Verification

The Terraform workflow runs with environment `dev` on `develop`.
Ensure these secrets exist in GitHub Actions environment `dev` (or repository scope fallback):

- `TF_WIF_PROVIDER_DEV` (or `TF_WIF_PROVIDER_dev`)
- `TF_SA_EMAIL_DEV` (or `TF_SA_EMAIL_dev`)

Recommended standardization: set uppercase names.

### 2.1 Expected value format

- `TF_WIF_PROVIDER_DEV`: `projects/<project-number>/locations/global/workloadIdentityPools/<pool-id>/providers/<provider-id>`
- `TF_SA_EMAIL_DEV`: `terraform-sa@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com` (or your chosen deployer SA)

## 3. Re-run Terraform on develop

Preferred (push-path rerun):

1. Re-run latest failed push run on `develop` for `terraform.yml`
2. Confirm `Terraform Apply` starts and reaches `Resolve auth inputs`

Manual dispatch note:

- Workflow now allows `workflow_dispatch` to execute `Terraform Apply` as well.

## 4. If Terraform Fails

## 4.1 Missing secrets

If failure is:

- `Missing Terraform WIF secrets for environment 'dev'.`

Then add/fix the two dev secrets above in GitHub Actions.

## 4.2 WIF not provisioned

If provider cannot be found or auth fails after secret setup, verify in GCP dev project:

- Workload Identity Pool exists
- GitHub OIDC provider exists
- Service account exists and has required roles
- Workload identity binding permits `refs/heads/develop`

If creating WIF fails with `iam.workloadIdentityPools.create`, request IAM grant:

- `roles/iam.workloadIdentityPoolAdmin` (or equivalent custom role containing `iam.workloadIdentityPools.create` and provider permissions)

## 5. Post-Deploy Functional Verification

Validate in deployed dev app:

1. Admin User Management:
- Add User flow uses group-assignment flow only (no invite-based path)
- Admin can open group assignment dialog and add member

2. Workspace visibility:
- Admin sees workspace switcher/dropdown
- Admin can switch workspaces
- Brand Guidelines area appears and is usable where expected

3. Added user access:
- Added user can log in successfully
- Added user can access group-linked workspace content

## 6. Troubleshooting Matrix

- `401` during login/API auth:
- Check Identity Platform/OAuth token audience config (`GOOGLE_TOKEN_AUDIENCE`, allowed org/email gates)
- Check GitHub deploy env vars/secrets used by backend service

- `403` after successful login:
- Check group membership insert path
- Check workspace membership insertion/propagation for group shared workspace
- Check role/permission guards for target endpoint

- Email mismatch edge case:
- Verify email normalization (trim/lowercase) across auth token handling, user provisioning, and membership lookups

## 7. Evidence to Capture

- Terraform run URL and final status
- Screenshot or short recording of Add User -> group assignment path
- Screenshot of workspace dropdown + Brand Guidelines visibility for admin
- Successful login + workspace access proof for added user
- Any 401/403 response payloads from browser network tab for triage
