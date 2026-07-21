gcp_project_id = "cf-genaistudi-genai-studio--vm"
gcp_region     = "europe-west3"
environment    = "pre-production"

# --- Service Names ---
backend_service_name  = "cstudio-backend-pp"
frontend_service_name = "cstudio-frontend-pp"
firebase_site_id      = "cstudio-pp-metro"

# --- GitHub Repo Details ---
github_conn_name   = "metro-inner-source-con"
github_repo_owner  = "metro-digital-inner-source"
github_repo_name   = "gcc-creative-studio"
github_branch_name = "test"

# --- Custom Audiences ---
# TODO: Replace with your OAuth Web Client ID and GCP Project Number
backend_custom_audiences  = ["YOUR_OAUTH_WEB_CLIENT_ID_HERE", "cf-genaistudi-genai-studio--vm"]
frontend_custom_audiences = ["YOUR_OAUTH_WEB_CLIENT_ID_HERE", "cf-genaistudi-genai-studio--vm"]

# --- Service-Specific Environment Variables ---
be_env_vars = {
  common = {
    LOG_LEVEL = "INFO"
  }
  pre-production = {
    ENVIRONMENT                     = "pre-production"
    GOOGLE_TOKEN_AUDIENCE          = "YOUR_OAUTH_WEB_CLIENT_ID_HERE"
    IDENTITY_PLATFORM_ALLOWED_ORGS = ""
    ADMIN_USER_EMAIL                = "joejoseph.george@metro.digital"
  }
}

fe_build_substitutions = {
  _ANGULAR_BUILD_COMMAND = "build-pp"
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

be_cpu    = "1"
be_memory = "512Mi"

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
