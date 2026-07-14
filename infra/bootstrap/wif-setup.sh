#!/bin/bash

# Copyright 2026 Google LLC
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

set -euo pipefail

# WIF Bootstrap Script for GitHub Actions Terraform Deployment
# This script creates Workload Identity Federation resources to enable GitHub Actions
# to authenticate to a GCP project without long-lived service account keys.
#
# Usage: ./wif-setup.sh <GCP_PROJECT_ID> <GITHUB_REPO_OWNER> <GITHUB_REPO_NAME> <ENVIRONMENT> <BRANCH>
#
# Example:
#   ./wif-setup.sh cf-genaistudi-genai-studio--gv metro-digital-inner-source gcc-creative-studio dev develop

if [[ $# -lt 5 ]]; then
  echo "Usage: $0 <GCP_PROJECT_ID> <GITHUB_REPO_OWNER> <GITHUB_REPO_NAME> <ENVIRONMENT> <BRANCH>"
  echo "Example: $0 cf-genaistudi-genai-studio--gv metro-digital-inner-source gcc-creative-studio dev develop"
  exit 1
fi

GCP_PROJECT_ID="$1"
GITHUB_REPO_OWNER="$2"
GITHUB_REPO_NAME="$3"
ENVIRONMENT="$4"
BRANCH="$5"

GITHUB_REPO_FULL="${GITHUB_REPO_OWNER}/${GITHUB_REPO_NAME}"
WIF_POOL_ID="github-pool"
WIF_POOL_LOCATION="global"
WIF_PROVIDER_ID="github-provider"
TF_SA_NAME="terraform-sa"
TF_SA_EMAIL="${TF_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

echo "=========================================="
echo "WIF Bootstrap for gcc-creative-studio"
echo "=========================================="
echo "Project ID: ${GCP_PROJECT_ID}"
echo "Environment: ${ENVIRONMENT}"
echo "Branch: ${BRANCH}"
echo "GitHub Repo: ${GITHUB_REPO_FULL}"
echo "WIF Pool ID: ${WIF_POOL_ID}"
echo "Terraform SA: ${TF_SA_EMAIL}"
echo "=========================================="

# Step 1: Set the current project
echo "[1/8] Setting current GCP project..."
gcloud config set project "${GCP_PROJECT_ID}"

# Step 2: Create Terraform Service Account
echo "[2/8] Creating Terraform service account..."
if gcloud iam service-accounts describe "${TF_SA_EMAIL}" --project="${GCP_PROJECT_ID}" 2>/dev/null; then
  echo "  ℹ️  Service account already exists"
else
  gcloud iam service-accounts create "${TF_SA_NAME}" \
    --display-name="Terraform GitHub Actions SA (${ENVIRONMENT})" \
    --project="${GCP_PROJECT_ID}"
  echo "  ✓ Service account created"
fi

# Step 3: Grant IAM roles to Terraform SA
echo "[3/8] Granting IAM roles to Terraform SA..."
ROLES=(
  "roles/editor"
  "roles/iam.securityAdmin"
  "roles/run.admin"
  "roles/storage.admin"
  "roles/secretmanager.admin"
  "roles/cloudbuild.builds.editor"
  "roles/firebase.admin"
  "roles/cloudsql.client"
)

for role in "${ROLES[@]}"; do
  echo "  Granting ${role}..."
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${TF_SA_EMAIL}" \
    --role="${role}" \
    --condition=None \
    --quiet 2>/dev/null || true
done
echo "  ✓ IAM roles granted"

# Step 4: Enable required APIs
echo "[4/8] Enabling required APIs..."
gcloud services enable \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  sts.googleapis.com \
  serviceusage.googleapis.com \
  --project="${GCP_PROJECT_ID}"
echo "  ✓ APIs enabled"

# Step 5: Create Workload Identity Pool
echo "[5/8] Creating Workload Identity Pool..."
WIF_POOL_RESOURCE="projects/${GCP_PROJECT_ID}/locations/${WIF_POOL_LOCATION}/workloadIdentityPools/${WIF_POOL_ID}"

if gcloud iam workload-identity-pools describe "${WIF_POOL_ID}" \
  --project="${GCP_PROJECT_ID}" \
  --location="${WIF_POOL_LOCATION}" 2>/dev/null; then
  echo "  ℹ️  WIF Pool already exists"
else
  gcloud iam workload-identity-pools create "${WIF_POOL_ID}" \
    --project="${GCP_PROJECT_ID}" \
    --location="${WIF_POOL_LOCATION}" \
    --display-name="GitHub Actions Pool" \
    --quiet
  echo "  ✓ WIF Pool created"
fi

# Step 6: Create GitHub OIDC Provider
echo "[6/8] Creating GitHub OIDC Provider..."
if gcloud iam workload-identity-pools providers describe-oidc "${WIF_PROVIDER_ID}" \
  --project="${GCP_PROJECT_ID}" \
  --location="${WIF_POOL_LOCATION}" \
  --workload-identity-pool="${WIF_POOL_ID}" 2>/dev/null; then
  echo "  ℹ️  OIDC Provider already exists"
else
  gcloud iam workload-identity-pools providers create-oidc "${WIF_PROVIDER_ID}" \
    --project="${GCP_PROJECT_ID}" \
    --location="${WIF_POOL_LOCATION}" \
    --workload-identity-pool="${WIF_POOL_ID}" \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.aud=assertion.aud,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-condition="assertion.aud == '${GCP_PROJECT_ID}'" \
    --quiet
  echo "  ✓ OIDC Provider created"
fi

# Step 7: Create Workload Identity Binding
echo "[7/8] Creating Workload Identity Binding for ${GITHUB_REPO_FULL}..."

# Remove the legacy branch-conditional binding if it exists.
LEGACY_BINDING_TITLE="${TF_SA_NAME}-${ENVIRONMENT}"
LEGACY_CONDITION="expression=assertion.ref == 'refs/heads/${BRANCH}',title=${LEGACY_BINDING_TITLE}"

gcloud iam service-accounts remove-iam-policy-binding "${TF_SA_EMAIL}" \
  --project="${GCP_PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_RESOURCE}/attribute.repository/${GITHUB_REPO_FULL}" \
  --condition="${LEGACY_CONDITION}" \
  --quiet 2>/dev/null || true

gcloud iam service-accounts add-iam-policy-binding "${TF_SA_EMAIL}" \
  --project="${GCP_PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${WIF_POOL_RESOURCE}/attribute.repository/${GITHUB_REPO_FULL}" \
  --quiet
echo "  ✓ Binding created for repository: ${GITHUB_REPO_FULL}"

# Step 8: Output the configuration
echo "[8/8] Configuration Summary"
echo "=========================================="
echo "Add these values to GitHub Secrets:"
echo ""
echo "TF_WIF_PROVIDER_${ENVIRONMENT^^}:"
echo "  ${WIF_POOL_RESOURCE}/providers/${WIF_PROVIDER_ID}"
echo ""
echo "TF_SA_EMAIL_${ENVIRONMENT^^}:"
echo "  ${TF_SA_EMAIL}"
echo ""
echo "=========================================="
echo "✓ WIF setup complete for ${ENVIRONMENT}!"
echo "=========================================="
