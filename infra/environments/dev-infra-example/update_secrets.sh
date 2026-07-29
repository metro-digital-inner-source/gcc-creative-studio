#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# A script to securely update secrets in Google Secret Manager
# based on the terraform outputs in the current environment directory.
#
# USAGE:
# 1. cd into the environment you want to update (e.g., `cd environments/dev`)
# 2. Run this script from that directory (`../../update_secrets.sh`)

set -e
set -o pipefail

# --- Color Definitions ---
C_RESET='\033[0m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[0;33m'
C_CYAN='\033[0;36m'

# --- Helper Functions ---
info() {
  echo -e "${C_CYAN}> $1${C_RESET}"
}

success() {
  echo -e "${C_GREEN}✅  $1${C_RESET}"
}

warn() {
  echo -e "${C_YELLOW}⚠️  $1${C_RESET}"
}

fail() {
  echo -e "${C_RED}❌  $1${C_RESET}" >&2
  exit 1
}

# --- Dependency Check ---
info "Checking for required tools (gcloud, jq, terraform)..."
command -v gcloud >/dev/null || fail "gcloud CLI not found. Please install it."
command -v jq >/dev/null || fail "jq is not installed. Please install it (e.g., 'brew install jq')."
command -v terraform >/dev/null || fail "Terraform not found. Please install it."
info "All tools found."

# --- Main Script ---

# 1. Find the .tfvars file in the current directory
TFVARS_FILE=$(find . -maxdepth 1 -name "*.tfvars" ! -name "terraform.tfvars.dist" | head -n 1)

if [ -z "$TFVARS_FILE" ]; then
  fail "No .tfvars file found in the current directory. Cannot proceed."
fi
info "Using variables from: ${C_YELLOW}${TFVARS_FILE}${C_RESET}"

# 2. Fetch outputs from the Terraform state in the current directory
info "Fetching secrets from Terraform state..."
TERRAFORM_OUTPUTS=$(terraform output -json)

# 2. Parse the outputs using jq
PROJECT_ID=$(echo "$TERRAFORM_OUTPUTS" | jq -r .gcp_project_id.value)
FRONTEND_SECRETS=$(echo "$TERRAFORM_OUTPUTS" | jq -r .frontend_secrets.value[])
BACKEND_SECRETS=$(echo "$TERRAFORM_OUTPUTS" | jq -r .backend_secrets.value[])

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "null" ]; then
  fail "Could not find 'gcp_project_id' in Terraform outputs. Did you run 'terraform apply'?"
fi

# Combine, de-duplicate, and sort the secret lists
ALL_SECRETS=$(echo "${FRONTEND_SECRETS} ${BACKEND_SECRETS}" | tr ' ' '\n' | sort -u | grep .)

if [ -z "$ALL_SECRETS" ]; then
  success "No secrets listed in 'frontend_secrets' or 'backend_secrets' outputs. Nothing to do."
  exit 0
fi

info "Project: ${C_YELLOW}${PROJECT_ID}${C_RESET}"
warn "The following secrets will be updated:"
echo -e "${C_YELLOW}$ALL_SECRETS${C_RESET}"

# 3. Confirmation
read -p "Continue? (y/n): " -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  fail "Operation cancelled."
fi

# 4. Attempt to auto-discover IAP OAuth client ID (IAP_CLIENT_ID / logout)
#    and Cloud Run IAP JWT audience (IAP_AUDIENCE).
info "Checking for IAP OAuth Client ID and Cloud Run IAP audience..."
AUTO_OAUTH_CLIENT_ID=""
AUTO_IAP_AUDIENCE=""

# Prefer value already set in .tfvars audiences / env vars
AUTO_OAUTH_CLIENT_ID=$(grep -oE '[0-9]+-[a-zA-Z0-9]+\.apps\.googleusercontent\.com' "$TFVARS_FILE" | head -n 1 || true)

if [ -z "$AUTO_OAUTH_CLIENT_ID" ]; then
  AUTO_OAUTH_CLIENT_ID=$(gcloud iap oauth-clients list "$PROJECT_ID" --format="json" 2>/dev/null | jq -r '.[0].clientId // .[0].name // empty' | awk -F'/' '{print $NF}')
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)' 2>/dev/null || true)
REGION=$(grep -E '^\s*gcp_region\s*=' "$TFVARS_FILE" | head -1 | sed -E 's/.*=\s*"([^"]+)".*/\1/' || true)
FE_SERVICE=$(grep -E '^\s*frontend_service_name\s*=' "$TFVARS_FILE" | head -1 | sed -E 's/.*=\s*"([^"]+)".*/\1/' || true)
REGION=${REGION:-europe-west3}
FE_SERVICE=${FE_SERVICE:-cstudio-frontend-dev}
if [ -n "$PROJECT_NUMBER" ]; then
  AUTO_IAP_AUDIENCE="/projects/${PROJECT_NUMBER}/locations/${REGION}/services/${FE_SERVICE}"
fi

if [ -n "$AUTO_OAUTH_CLIENT_ID" ] && [ "$AUTO_OAUTH_CLIENT_ID" != "null" ]; then
  success "Found IAP OAuth Client ID (for IAP_CLIENT_ID)."
else
  warn "Could not automatically find an IAP OAuth Client ID for project '$PROJECT_ID'."
  AUTO_OAUTH_CLIENT_ID=""
fi
if [ -n "$AUTO_IAP_AUDIENCE" ]; then
  success "Cloud Run IAP audience: ${AUTO_IAP_AUDIENCE}"
fi

# 5. Loop, Prompt, and Write
for SECRET_NAME in $ALL_SECRETS; do
  info "Updating secret: ${C_YELLOW}${SECRET_NAME}${C_RESET}"
  SECRET_VALUE=""
  AUTO_DISCOVERED=false

  # Check if we have an auto-discovered value for the current secret
  case $SECRET_NAME in
    "IAP_CLIENT_ID")           SECRET_VALUE=$AUTO_OAUTH_CLIENT_ID; AUTO_DISCOVERED=true ;;
    "IAP_AUDIENCE")            SECRET_VALUE=$AUTO_IAP_AUDIENCE; AUTO_DISCOVERED=true ;;
    "GOOGLE_TOKEN_AUDIENCE")   SECRET_VALUE=$AUTO_OAUTH_CLIENT_ID; AUTO_DISCOVERED=true ;;
    "GOOGLE_CLIENT_ID")        SECRET_VALUE=$AUTO_OAUTH_CLIENT_ID; AUTO_DISCOVERED=true ;;
  esac

  if [ "$AUTO_DISCOVERED" = true ] && [ -n "$SECRET_VALUE" ] && [ "$SECRET_VALUE" != "null" ]; then
    info "  Auto-populating ${SECRET_NAME}."
  elif [ "$SECRET_NAME" == "IAP_CLIENT_ID" ] || [ "$SECRET_NAME" == "GOOGLE_TOKEN_AUDIENCE" ] || [ "$SECRET_NAME" == "GOOGLE_CLIENT_ID" ]; then
    warn "  Could not auto-discover IAP OAuth Client ID."
    info "  Please perform the following manual steps:"
    echo "  1. Open this URL in your browser: ${C_YELLOW}https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}${C_RESET}"
    echo "  2. Find the OAuth 2.0 Client ID of type 'Web application' used by IAP."
    read -s -p "  Enter the IAP OAuth Client ID: " SECRET_VALUE
    echo
    # Reuse for subsequent IAP secrets in this run
    AUTO_OAUTH_CLIENT_ID="$SECRET_VALUE"
  elif [ "$SECRET_NAME" == "IAP_AUDIENCE" ]; then
    warn "  Could not build Cloud Run IAP audience automatically."
    echo "  Expected format: /projects/PROJECT_NUMBER/locations/REGION/services/FRONTEND_SERVICE"
    read -s -p "  Enter IAP_AUDIENCE: " SECRET_VALUE
    echo
  else
    # Add reassurance for the user
    echo -e "${C_CYAN}  It is safe to paste your secret. The value is read securely, not displayed, and not stored in disk or history.${C_RESET}"

    # Securely prompt for the secret value (the -s flag hides the input)
    read -s -p "  Enter new value: " SECRET_VALUE
    echo # Add a newline after the prompt
  fi

  if [ -z "$SECRET_VALUE" ]; then
    warn "  No value provided. Skipping ${SECRET_NAME}."
    continue
  fi

  # Check if the secret already exists and has the same value
  LATEST_VERSION=$(gcloud secrets versions access latest --secret="$SECRET_NAME" --project="$PROJECT_ID" 2>/dev/null || echo "")
  if [ "$LATEST_VERSION" == "$SECRET_VALUE" ]; then
    success "  Secret ${SECRET_NAME} is already up-to-date. Skipping."
  else
    # Write the secret value from the variable directly to gcloud stdin
    # This avoids saving it to disk or command history.
    echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" \
      --data-file="-" \
      --project="$PROJECT_ID" \
      --quiet

    if [ $? -eq 0 ]; then
      success "  Successfully added new version for ${SECRET_NAME}."
    else
      fail "  Failed to update secret ${SECRET_NAME}."
    fi
  fi

done
success "All secrets updated."
