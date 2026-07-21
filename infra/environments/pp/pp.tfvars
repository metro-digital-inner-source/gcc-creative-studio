gcp_project_id = "cf-genaistudi-genai-studio--vm"
gcp_region     = "europe-west3"
environment    = "pp"

# --- Service Names ---
backend_service_name  = "cstudio-backend-pp"
frontend_service_name = "cstudio-frontend-pp" # This is the Cloud Run service name
firebase_site_id      = "cstudio-pp-metro"    # Must be unique across all Firebase projects

# --- GitHub Repo Details ---
# NOTE: github_conn_name must match the Cloud Build (2nd gen) host connection created
#       manually in the --vm project console before running terraform apply.
github_conn_name   = "gcc-creative-studio"
github_repo_owner  = "metro-digital-inner-source"
github_repo_name   = "gcc-creative-studio"
github_branch_name = "test"

# --- Custom Audiences ---
# REPLACE_WITH_PP_OAUTH_WEB_CLIENT_ID = the OAuth 2.0 Web client ID created for preprod.
backend_custom_audiences  = ["487202226087-o4qcki73gegl6jqnb8muu6d5erem1t7h.apps.googleusercontent.com", "cf-genaistudi-genai-studio--vm"]
frontend_custom_audiences = ["487202226087-o4qcki73gegl6jqnb8muu6d5erem1t7h.apps.googleusercontent.com", "cf-genaistudi-genai-studio--vm"]

# --- Service-Specific Environment Variables ---
# IMPORTANT: the platform module merges be_env_vars["common"] with be_env_vars[var.environment].
# Since environment = "pp", there MUST be a "pp" key below or the backend gets no env vars.
be_env_vars = {
  common = {
    LOG_LEVEL = "INFO"
  }
  pp = {
    ENVIRONMENT                    = "pp"
    GOOGLE_TOKEN_AUDIENCE          = "487202226087-o4qcki73gegl6jqnb8muu6d5erem1t7h.apps.googleusercontent.com"
    IDENTITY_PLATFORM_ALLOWED_ORGS = "" # If empty then any org is allowed
    # Mirroring staging: keep open unless explicitly restricted.
    ALLOWED_EMAILS = ""
    # Admin API allowlist (RoleChecker).
    ADMIN_OWNER_EMAILS = "joejoseph.george@metro.digital,manish.singh@metro-gsc.in,abhishek.acharya@metro-gsc.in"
    # Bootstrap first admin user (must exist before login allowlist succeeds).
    ADMIN_USER_EMAIL = "manish.singh@metro-gsc.in"
  }
}

fe_build_substitutions = {
  _ANGULAR_BUILD_COMMAND = "build-dev"
}

frontend_secrets = [
  "FIREBASE_API_KEY",          # Your Firebase Web API Key
  "FIREBASE_AUTH_DOMAIN",      # Your Firebase Auth Domain (e.g., project-id.firebaseapp.com)
  "FIREBASE_PROJECT_ID",       # Your Firebase Project ID
  "FIREBASE_STORAGE_BUCKET",   # Your Firebase Storage Bucket (e.g., project-id.appspot.com)
  "FIREBASE_MESSAGING_SENDER_ID", # Your Firebase Cloud Messaging Sender ID
  "FIREBASE_APP_ID",           # Your Firebase Web App ID
  "FIREBASE_MEASUREMENT_ID",   # Your Google Analytics Measurement ID
  "GOOGLE_CLIENT_ID",          # Your Google OAuth 2.0 Client ID for web
]

backend_secrets = [
  "GOOGLE_TOKEN_AUDIENCE",
]

# Empty: do not mount secrets that overlap plain be_env_vars keys
# (Cloud Run rejects duplicate env names).
backend_runtime_secrets = {}

apis_to_enable = [
  "serviceusage.googleapis.com",     # Required to enable other APIs
  "iam.googleapis.com",              # Required for IAM management
  "cloudbuild.googleapis.com",       # Required for Cloud Build
  "artifactregistry.googleapis.com", # Required for Artifact Registry
  "run.googleapis.com",              # Required for Cloud Run
  "cloudresourcemanager.googleapis.com",
  "compute.googleapis.com",
  "cloudfunctions.googleapis.com",
  "iamcredentials.googleapis.com",
  "aiplatform.googleapis.com",
  "firestore.googleapis.com",
  "texttospeech.googleapis.com",
  "workflows.googleapis.com",
  "sqladmin.googleapis.com",          # Required for Cloud SQL
  "secretmanager.googleapis.com",     # Required for Secret Manager
  "firebase.googleapis.com",          # Required for Firebase project/hosting
  "firebasehosting.googleapis.com",   # Required for Firebase Hosting
]
