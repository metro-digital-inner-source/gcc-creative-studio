# Troubleshooting Guide

Common issues and their solutions when deploying or running Creative Studio on GCP.

## Authentication & Access Issues

### Issue: "Could not synchronize user profile with the server"

**Symptoms:**
- User logs in successfully
- App shows error message after few seconds
- User is logged out automatically

**Root Cause:**
Usually database connection failed when creating user's private workspace during login.

**Solution:**
1. Check backend logs:
```bash
gcloud run services logs read cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 \
  --limit=100
```

2. Look for errors like:
- `database connection refused` → Cloud SQL is down or unreachable
- `permission denied` → Cloud SQL IAM misconfigured
- `UPDATE workspace failed` → Workspace auto-creation logic error

3. If `UPDATE workspace failed`:
   - Check backend code: `src/admin/admin_service.py` line 189
   - Verify SQLAlchemy parameterized queries (not raw f-strings)
   - Run backend tests: `pytest tests/admin/`

4. If Cloud SQL is unreachable:
   - Verify VPC Connector status:
   ```bash
   gcloud compute networks vpc-tunnels list \
     --project=cf-genaistudi-genai-studio--gv
   ```
   - Check Cloud Run service has env var: `CLOUDSQL_INSTANCE`
   - Verify service account has role: `cloudsql.client`

### Issue: "Unauthorized" or "403 Forbidden" at login

**Symptoms:**
- Login page appears
- Click "Login with Google" → redirected to Google → redirected back → error

**Root Cause:**
- IAP email domain not in allowed list
- OAuth client ID mismatch
- User using wrong email domain (not @metro.digital or @metro-gsc.in)

**Solution:**

1. Check user email:
   ```bash
   # Should be @metro.digital or @metro-gsc.in
   echo $USER_EMAIL
   ```

2. Verify IAP policy:
   ```bash
   gcloud iap web get-iam-policy \
     --project=cf-genaistudi-genai-studio--gv \
     --resource-names=projects/PROJ_NUMBER/iap_web/services/SERVICE_ID
   ```
   - Should list binding: `roles/iap.httpsResourceAccessor`
   - Should include your email or group

3. Check OAuth client ID in Cloud Console:
   - **APIs & Services → Credentials**
   - Verify `GOOGLE_TOKEN_AUDIENCE` env var matches
   - Verify authorized redirect URIs include your domain

4. Verify domain in backend:
   ```bash
   # Local dev only - check ALLOWED_EMAILS
   echo $ALLOWED_EMAILS
   ```

### Issue: User added to group but workspace not created

**Symptoms:**
- Admin adds user to group via admin dashboard
- User receives success message
- User logs in but doesn't see workspace

**Root Cause:**
Workspace auto-creation failed silently (exception swallowed).

**Solution:**

1. Check backend logs for admin operation:
```bash
gcloud run services logs read cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 \
  --limit=100 | grep "add_user_to_group"
```

2. Look for lines with:
   - `exc_info=True` (indicates exception was logged)
   - Database errors
   - SQLAlchemy constraint violations (e.g., duplicate workspace name)

3. Manual verification in database:
```bash
gcloud sql connect creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv \
  --user=postgres \
  --database=genaistudio

# Check if user exists
SELECT id, email FROM "user" WHERE email = 'test@metro.digital';

# Check if user-group association exists
SELECT * FROM user_group_association WHERE user_id = 'USER_ID';

# Check if workspace was created
SELECT id, name, user_id, group_id FROM workspace WHERE user_id = 'USER_ID';
```

4. If workspace missing:
   - Manually create via psql:
   ```sql
   INSERT INTO workspace (id, name, user_id, group_id, workspace_type, created_at)
   VALUES (
     gen_random_uuid(),
     'test-workspace-name',
     'USER_UUID_HERE',
     'GROUP_UUID_HERE',
     'private',
     NOW()
   );
   ```

## Database Issues

### Issue: "Connection refused" when running migrations

**Symptoms:**
- Deploy fails during `Alembic upgrade`
- Error: `could not connect to server: Connection refused`

**Root Cause:**
- Cloud SQL instance is starting/stopping
- VPC Connector not ready
- Cloud Run service doesn't have correct permissions

**Solution:**

1. Check Cloud SQL instance status:
```bash
gcloud sql instances describe creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv
```
Should show `status: RUNNABLE`

2. Wait for instance to fully start:
```bash
gcloud sql operations wait OPERATION_ID \
  --project=cf-genaistudi-genai-studio--gv
```

3. Verify VPC Connector is ready:
```bash
gcloud compute networks vpc-tunnels describe CONNECTOR_NAME \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3
```
Should show `state: READY`

4. Verify Cloud Run service account has permissions:
```bash
gcloud projects get-iam-policy cf-genaistudi-genai-studio--gv \
  --flatten="bindings[].members" \
  --filter="bindings.members:cstudio-backend-sa@*" \
  --format="table(bindings.role)"
```
Should include: `roles/cloudsql.client`

### Issue: "ProgrammingError: column does not exist"

**Symptoms:**
- Deploy succeeds but backend crashes on request
- Error: `ProgrammingError: column "user_deleted_at" does not exist`

**Root Cause:**
Database migration didn't run or is out of sync with application code.

**Solution:**

1. Check migration status:
```bash
gcloud sql connect creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv \
  --user=postgres \
  --database=genaistudio -c "SELECT * FROM alembic_version;"
```

2. Check latest migration file:
```bash
ls -la backend/alembic/versions/ | tail -5
```

3. Manually run migration:
```bash
# From your local machine (with gcloud SDK)
gcloud sql connect creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv \
  --user=postgres \
  --database=genaistudio

# Inside psql, run migration script
\i backend/alembic/versions/LATEST_MIGRATION.py
```

4. Or, trigger bootstrap again:
```bash
./bootstrap.sh
# Select environment: dev
```

### Issue: "Unique constraint violation" on workspace creation

**Symptoms:**
- User added to group → error in backend logs
- Error: `duplicate key value violates unique constraint "ix_workspace_user_id_group_id"`

**Root Cause:**
User already has workspace in that group (duplicate add attempt).

**Solution:**

1. Check existing workspaces:
```bash
gcloud sql connect creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv \
  --user=postgres \
  --database=genaistudio

SELECT id, name, user_id, group_id FROM workspace 
WHERE user_id = 'USER_ID' AND group_id = 'GROUP_ID';
```

2. If duplicate exists, this is expected (user already in group)
   - No action needed
   - Admin dashboard should show user already in group

3. Check admin dashboard:
   - Navigate to `/admin`
   - Select group → check if user is already listed

## Cloud Run Issues

### Issue: Cloud Run service times out (504 Gateway Timeout)

**Symptoms:**
- Backend requests hang for 60+ seconds
- Browser shows "504 Gateway Timeout"
- Cloud Run logs show request never completes

**Root Cause:**
- Cloud Run memory/CPU too low
- Database query is very slow
- Cloud SQL has too many connections

**Solution:**

1. Check Cloud Run service configuration:
```bash
gcloud run services describe cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3
```
Look for: `memory: 512Mi` or `cpu: 1`

2. Increase memory/CPU (via Terraform):
```hcl
# infra/modules/cloud_run.tf
resource "google_cloud_run_service" "backend" {
  template {
    spec {
      containers {
        memory = "1Gi"  # Increase from 512Mi
        cpu    = "2"    # Increase from 1
      }
    }
  }
}
```

3. Check slow queries in database:
```bash
gcloud sql connect creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv \
  --user=postgres \
  --database=genaistudio

# Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 second
SELECT pg_reload_conf();

# Check logs
SELECT query, duration FROM pg_stat_statements ORDER BY duration DESC LIMIT 10;
```

4. Check database connection pool:
```bash
# From backend service logs
gcloud run services logs read cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 | grep -i "pool\|connection"
```
If many "waiting for connection" messages:
- Increase `SQLALCHEMY_POOL_SIZE` env var (default 5)
- Or increase Cloud SQL connection slots

### Issue: Cloud Run service repeatedly crashing (CrashLoopBackOff)

**Symptoms:**
- Service shows "Unavailable" in Cloud Run dashboard
- New revisions keep starting and stopping
- Logs show rapid crashes

**Root Cause:**
- Database migration failed (blocking startup)
- Missing required environment variables
- Invalid configuration

**Solution:**

1. Check Cloud Run logs:
```bash
gcloud run services logs read cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 \
  --limit=50
```

2. Look for startup errors:
   - `ModuleNotFoundError` → missing dependency (rebuild container)
   - `KeyError: ENVIRONMENT` → missing env var (update service)
   - `Alembic upgrade failed` → database migration issue (see above)

3. Rollback to previous revision:
```bash
gcloud run services update-traffic cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 \
  --to-revisions=PREVIOUS_REVISION_ID=100
```

4. Check environment variables:
```bash
gcloud run services describe cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 | grep -A 20 "env:"
```
Verify all required vars are present.

## Load Balancer & IAP Issues

### Issue: "Forwarding rule does not exist"

**Symptoms:**
- Domain doesn't resolve
- Browser can't connect to `cstudio-dev.metro.digital`

**Root Cause:**
- Terraform apply failed to create load balancer
- DNS record not pointing to load balancer IP

**Solution:**

1. Check load balancer:
```bash
gcloud compute forwarding-rules list \
  --project=cf-genaistudi-genai-studio--gv \
  --global
```
Should show forwarding rule for cstudio-dev

2. Check DNS records:
```bash
gcloud dns record-sets list \
  --project=cf-genaistudi-genai-studio--gv \
  --zone=metro-digital
```
Should show CNAME or A record pointing to load balancer IP

3. Recreate via Terraform:
```bash
cd infra/environments/dev
terraform plan -var-file=dev.tfvars | grep -i "load_balancer"
terraform apply -var-file=dev.tfvars
```

### Issue: IAP shows "External Identities (OAuth 2.0)" error

**Symptoms:**
- After login, IAP shows confusing OAuth consent screen
- Then redirects back to login loop

**Root Cause:**
- OAuth client ID not configured correctly
- Redirect URIs don't match actual domain

**Solution:**

1. Go to **Google Cloud Console → APIs & Services → Credentials**

2. Find the OAuth 2.0 Web Client ID for this environment

3. Verify **Authorized Redirect URIs** include:
   - `https://cstudio-dev.metro.digital`
   - `https://cstudio-dev.metro.digital/`
   - `https://cstudio-dev.metro.digital/login` (if applicable)

4. Update if needed, then redeploy

5. Clear browser cookies for cstudio-dev.metro.digital and retry login

## Deployment Issues

### Issue: "Terraform state is locked"

**Symptoms:**
- Terraform apply hangs or fails
- Error: `Error acquiring the state lock`

**Root Cause:**
- Previous terraform operation was interrupted
- Lock file is stale

**Solution:**

1. List current locks:
```bash
cd infra/environments/dev
terraform state list
```

2. Force unlock (use carefully!):
```bash
terraform force-unlock LOCK_ID
```

3. If that doesn't work, manually remove state lock from GCS:
```bash
# Find state bucket
gcloud storage buckets list \
  --project=cf-genaistudi-genai-studio--gv \
  | grep terraform

# Remove lock file
gcloud storage rm gs://terraform-state-bucket/.terraform.lock.hcl
```

### Issue: GitHub Actions workflow fails with "WIF authentication failed"

**Symptoms:**
- Terraform deploy fails in CI/CD
- Error: `Error retrieving credentials`

**Root Cause:**
- Workload Identity Pool not configured
- Service account doesn't have impersonation rights

**Solution:**

1. Check workflow logs in GitHub:
   - **Actions → [workflow name] → failed run**
   - Look for line: `Generating credentials for...`

2. Verify WIF setup:
```bash
gcloud iam workload-identity-pools describe github-pool \
  --project=cf-genaistudi-genai-studio--gv \
  --location=global
```

3. Verify service account has impersonation rights:
```bash
gcloud iam service-accounts get-iam-policy \
  terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com
```
Should show: `roles/iam.workloadIdentityUser` for GitHub

4. Check GitHub Actions secrets:
   - **Repository → Settings → Secrets → Actions**
   - Verify: `GOOGLE_PROJECT_ID`, `WORKLOAD_IDENTITY_PROVIDER`, `SERVICE_ACCOUNT_EMAIL` are set

5. Rerun workflow after fixing

## General Debugging Commands

### Check all services are healthy:

```bash
# Backend health
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://cstudio-backend-dev-HASH-europe-west3.a.run.app/health

# Frontend health
curl https://cstudio-frontend-dev-HASH-europe-west3.a.run.app/

# Database connectivity
gcloud sql connect creative-studio-db-HASH \
  --project=cf-genaistudi-genai-studio--gv \
  --user=postgres \
  --database=genaistudio -c "SELECT 1;"
```

### View recent logs (all services):

```bash
# Backend logs (last 50 lines)
gcloud run services logs read cstudio-backend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 \
  --limit=50 \
  --format="table(timestamp, severity, text_payload)"

# Frontend logs
gcloud run services logs read cstudio-frontend-dev \
  --project=cf-genaistudi-genai-studio--gv \
  --region=europe-west3 \
  --limit=50

# Cloud Build logs (deployments)
gcloud builds log \
  --project=cf-genaistudi-genai-studio--gv \
  --limit=50 \
  --stream=false
```

### Run pytest locally to validate backend logic:

```bash
cd backend
pytest tests/ -v  # All tests
pytest tests/admin/ -v  # Admin tests only
pytest tests/admin/test_admin_service.py::test_add_user_to_group -v  # Single test
```

## When to Escalate

If you've tried the above and still stuck:

1. **Collect information:**
   - Error message (full text)
   - Logs (gcloud commands output)
   - Recent changes (git diff)
   - Environment (dev/pp/prod)

2. **Contact escalation:**
   - Backend issue → Backend team (check logs/code)
   - Database issue → Cloud SQL/DevOps team
   - Deployment issue → Infrastructure/DevOps team
   - Authentication issue → Identity & Access team

3. **Create incident:**
   - Title: `[Environment] Issue: Brief description`
   - Description: Include commands run, logs, what you tried
   - Attach: Screenshots, error messages

## Further Reading

- [CLOUD_SETUP.md](../CLOUD_SETUP.md) — Deployment procedures
- [DEVELOPMENT.md](../DEVELOPMENT.md) — Local development debugging
- Backend code: `src/` directory structure
- Database schema: `backend/alembic/versions/`
