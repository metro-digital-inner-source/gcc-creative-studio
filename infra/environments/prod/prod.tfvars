gcp_project_id = "cf-genaistudi-genai-studio--7u"
gcp_region     = "europe-west3"
environment    = "production"

# --- Service Names ---
backend_service_name  = "cstudio-backend-prod"
frontend_service_name = "cstudio-frontend-prod"
firebase_site_id      = "cstudio-prod-metro"

# --- GitHub Repo Details ---
github_conn_name   = "metro-inner-source-con"
github_repo_owner  = "metro-digital-inner-source"
github_repo_name   = "gcc-creative-studio"
github_branch_name = "main"

# --- Custom Audiences ---
# TODO: Replace with your OAuth Web Client ID and GCP Project Number
backend_custom_audiences  = ["YOUR_OAUTH_WEB_CLIENT_ID_HERE", "cf-genaistudi-genai-studio--7u"]
frontend_custom_audiences = ["YOUR_OAUTH_WEB_CLIENT_ID_HERE", "cf-genaistudi-genai-studio--7u"]

# --- Service-Specific Environment Variables ---
be_env_vars = {
  common = {
    LOG_LEVEL = "WARN"
  }
  production = {
    ENVIRONMENT                     = "production"
    GOOGLE_TOKEN_AUDIENCE          = "YOUR_OAUTH_WEB_CLIENT_ID_HERE"
    IDENTITY_PLATFORM_ALLOWED_ORGS = ""
  }
}

fe_build_substitutions = {
  _ANGULAR_BUILD_COMMAND = "build-prod"
}

backend_secrets = [
  "GOOGLE_TOKEN_AUDIENCE",
]

backend_runtime_secrets = {
  "GOOGLE_TOKEN_AUDIENCE" = "GOOGLE_TOKEN_AUDIENCE"
}

frontend_secrets = [
  "FIREBASE_API_KEY",
  "FIREBASE_AUTH_DOMAIN",
  "FIREBASE_PROJECT_ID",
  "FIREBASE_STORAGE_BUCKET",
  "FIREBASE_MESSAGING_SENDER_ID",
  "FIREBASE_APP_ID",
  "FIREBASE_MEASUREMENT_ID",
  "GOOGLE_CLIENT_ID",
]

be_cpu    = "2"
be_memory = "1Gi"

apis_to_enable = [
  "serviceusage.googleapis.com",
  "iam.googleapis.com",
  "cloudbuild.googleapis.com",
  "artifactregistry.googleapis.com",
  "run.googleapis.com",
  "cloudresourcemanager.googleapis.com",
  "compute.googleapis.com",
  "cloudfunctions.googleapis.com",
  "iamcredentials.googleapis.com",
  "aiplatform.googleapis.com",
  "firestore.googleapis.com",
  "texttospeech.googleapis.com",
  "workflows.googleapis.com",
  "cloudsql.googleapis.com",
  "sqladmin.googleapis.com",
  "secretmanager.googleapis.com",
]
