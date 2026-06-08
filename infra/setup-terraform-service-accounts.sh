#!/bin/bash
# Copyright 2025 Google LLC
# 
# Script to create Terraform deployment service accounts
# with organization-compliant IAM roles (no primitive roles)
#
# This script should be run by a GCP admin with sufficient permissions

set -e

# Color definitions
C_RESET='\033[0m'
C_GREEN='\033[1;32m'
C_YELLOW='\033[1;33m'
C_BLUE='\033[1;34m'
C_RED='\033[1;31m'

info() { echo -e "${C_BLUE}ℹ️  $1${C_RESET}"; }
success() { echo -e "${C_GREEN}✅  $1${C_RESET}"; }
warn() { echo -e "${C_YELLOW}⚠️  $1${C_RESET}"; }
error() { echo -e "${C_RED}❌  $1${C_RESET}" >&2; exit 1; }

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    error "gcloud CLI not found. Please install it first."
fi

# Environment configuration
declare -A ENVIRONMENTS=(
    ["dev"]="cf-genaistudi-genai-studio--gv"
    ["pp"]="cf-genaistudi-genai-studio--vm"
    ["prod"]="cf-genaistudi-genai-studio--7u"
)

SERVICE_ACCOUNT_NAME="terraform-deployer"
USER_EMAIL="joejoseph.george@metro.digital"

# IAM roles required for Terraform deployment (no primitive roles)
REQUIRED_ROLES=(
    "roles/resourcemanager.projectIamAdmin"
    "roles/iam.serviceAccountAdmin"
    "roles/iam.securityAdmin"
    "roles/serviceusage.serviceUsageAdmin"
    "roles/storage.admin"
    "roles/secretmanager.admin"
    "roles/run.admin"
    "roles/compute.admin"
    "roles/cloudsql.admin"
    "roles/cloudbuild.builds.editor"
    "roles/artifactregistry.admin"
    "roles/firebase.admin"
    "roles/firebasehosting.admin"
    "roles/aiplatform.admin"
    "roles/workflows.admin"
)

info "This script will create Terraform deployment service accounts"
info "for Dev, PP, and Prod environments with organization-compliant IAM roles."
echo ""
warn "This script requires admin permissions on all three projects."
echo ""
read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    info "Aborted by user."
    exit 0
fi

# Function to create service account and assign roles
setup_environment() {
    local env_name=$1
    local project_id=$2
    
    info "Setting up $env_name environment (Project: $project_id)"
    
    # Check if we have access to the project
    if ! gcloud projects describe "$project_id" &>/dev/null; then
        error "Cannot access project $project_id. Check permissions."
    fi
    
    # Create service account
    info "Creating service account: ${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com"
    if gcloud iam service-accounts describe "${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com" --project="$project_id" &>/dev/null; then
        warn "Service account already exists. Skipping creation."
    else
        gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
            --display-name="Terraform Deployment Service Account (${env_name})" \
            --description="Service account for Terraform infrastructure deployments. No keys - use impersonation." \
            --project="$project_id"
        success "Service account created."
    fi
    
    # Grant required roles
    info "Granting IAM roles..."
    for role in "${REQUIRED_ROLES[@]}"; do
        echo "  - Granting ${role}..."
        gcloud projects add-iam-policy-binding "$project_id" \
            --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com" \
            --role="$role" \
            --condition=None \
            --quiet &>/dev/null || warn "Failed to grant $role (may already exist)"
    done
    success "IAM roles granted."
    
    # Allow user to impersonate the service account
    info "Granting impersonation rights to $USER_EMAIL..."
    gcloud iam service-accounts add-iam-policy-binding \
        "${SERVICE_ACCOUNT_NAME}@${project_id}.iam.gserviceaccount.com" \
        --member="user:$USER_EMAIL" \
        --role="roles/iam.serviceAccountTokenCreator" \
        --project="$project_id" \
        --quiet || warn "Failed to grant impersonation rights"
    
    # Create Terraform state bucket
    info "Creating Terraform state bucket..."
    local bucket_name="${project_id}-tfstate"
    if gsutil ls "gs://${bucket_name}" &>/dev/null; then
        warn "Bucket gs://${bucket_name} already exists. Skipping."
    else
        gcloud storage buckets create "gs://${bucket_name}" \
            --project="$project_id" \
            --location="europe-west3" \
            --uniform-bucket-level-access \
            --public-access-prevention || warn "Failed to create bucket (check permissions)"
        
        # Enable versioning
        gcloud storage buckets update "gs://${bucket_name}" \
            --versioning || warn "Failed to enable versioning"
        
        success "Terraform state bucket created: gs://${bucket_name}"
    fi
    
    success "✅ ${env_name} environment setup complete!\n"
}

# Setup each environment
for env_name in dev pp prod; do
    project_id="${ENVIRONMENTS[$env_name]}"
    setup_environment "$env_name" "$project_id"
done

success "🎉 All environments configured successfully!"
echo ""
info "Next steps:"
echo "  1. Authenticate with impersonation:"
echo "     gcloud auth application-default login \\"
echo "       --impersonate-service-account='terraform-deployer@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com'"
echo ""
echo "  2. Run Terraform:"
echo "     cd infra/environments/dev"
echo "     terraform init"
echo "     terraform plan -var-file=dev.tfvars"
echo "     terraform apply -var-file=dev.tfvars"
echo ""
info "Remember: No service account keys are created (org policy compliance)."
