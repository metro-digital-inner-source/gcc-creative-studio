gcp_project_id = "YOUR_GCP_PROJECT_ID"
gcp_region     = "us-central1"
environment    = "development"

# --- Service Names ---
backend_service_name  = "cstudio-backend-dev"
frontend_service_name = "cstudio-frontend-dev"

# --- GitHub Repo Details ---
github_conn_name   = "gh-repo-owner-con"
github_repo_owner  = "RepoOwnerName"
github_repo_name   = "repo-owner-gcc-creative-studio"
github_branch_name = "develop"

# --- Custom Audiences ---
# Still used by Cloud Run custom_audiences where configured; IAP JWT audience
# is supplied via the IAP_AUDIENCE secret (see backend_runtime_secrets).
backend_custom_audiences  = ["YOUR_IAP_OAUTH_CLIENT_ID_HERE", "YOUR_GCP_PROJECT_ID"]
frontend_custom_audiences = ["YOUR_IAP_OAUTH_CLIENT_ID_HERE", "YOUR_GCP_PROJECT_ID"]

# --- Service-Specific Environment Variables ---
be_env_vars = {
  common = {
    LOG_LEVEL = "INFO"
  }
  development = {
    ENVIRONMENT  = "development"
    IDENTITY_PLATFORM_ALLOWED_ORGS = "" # If empty then any org is allowed
  }
  production = {
    ENVIRONMENT  = "production"
    IDENTITY_PLATFORM_ALLOWED_ORGS = "" # If empty then any org is allowed
  }
}

fe_build_substitutions = {
  _ANGULAR_BUILD_COMMAND = "build-dev"
}

# Who can pass the IAP gate. Prefer a Google Group over individual users.
# Examples: "group:creative-studio-users@metro-gsc.in" or "domain:metro-gsc.in"
iap_enabled = true
iap_access_members = [
  "user:manish.singh@metro-gsc.in",
  # "group:YOUR_GROUP@metro-gsc.in",
]

frontend_secrets = [
  "IAP_CLIENT_ID", # IAP OAuth client ID (SPA logout). Populate via bootstrap / gcloud.
]

backend_secrets = [
  "GOOGLE_TOKEN_AUDIENCE",
]

backend_runtime_secrets = {
  "GOOGLE_TOKEN_AUDIENCE" = "GOOGLE_TOKEN_AUDIENCE"
  # IAP_AUDIENCE is set as a plain env var by the platform module
  # (/projects/NUMBER/locations/REGION/services/FRONTEND_SERVICE).
}

apis_to_enable = [
  "serviceusage.googleapis.com",     # Required to enable other APIs
  "iam.googleapis.com",              # Required for IAM management
  "cloudbuild.googleapis.com",       # Required for Cloud Build
  "artifactregistry.googleapis.com", # Required for Artifact Registry
  "run.googleapis.com",              # Required for Cloud Run
  "cloudresourcemanager.googleapis.com",
  "compute.googleapis.com",
  "iamcredentials.googleapis.com",
  "aiplatform.googleapis.com",
  "texttospeech.googleapis.com",
  "workflows.googleapis.com",
  "iap.googleapis.com",
  "identitytoolkit.googleapis.com",
]
