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

variable "gcp_project_id" {
  type        = string
  description = "The GCP Project ID."
}

variable "gcp_region" {
  type        = string
  description = "The GCP region for the resources."
}

variable "environment" {
  type        = string
  description = "The deployment environment (e.g., 'dev', 'prod')."
}

variable "service_name" {
  type        = string
  description = "The full name of the Cloud Run service."
}

variable "resource_prefix" {
  type        = string
  description = "A short prefix for resource names."
}

variable "github_branch_name" {
  type        = string
  description = "The branch name to trigger builds from."
}

variable "cloudbuild_yaml_path" {
  type        = string
  description = "The path to the cloudbuild.yaml file."
}

variable "included_files_glob" {
  type        = list(string)
  description = "A list of glob patterns for files that should trigger the build."
}

variable "build_substitutions" {
  type        = map(string)
  description = "A map of substitution variables for the Cloud Build trigger."
  default     = {}
}

variable "source_repository_id" {
  type        = string
  description = "The ID of the Cloud Build V2 source repository."
}

variable "cpu" {
  type    = string
  default = "1000m"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "scaling_min_instances" {
  type    = number
  default = 0
}

variable "scaling_max_instances" {
  type    = number
  default = 10
}

variable "iap_enabled" {
  type        = bool
  description = "Enable Identity-Aware Proxy on this Cloud Run service."
  default     = true
}

variable "iap_access_members" {
  type        = list(string)
  description = "IAM members granted roles/iap.httpsResourceAccessor (e.g. group:team@example.com)."
  default     = []
}

variable "backend_host" {
  type        = string
  description = "Backend Cloud Run hostname used by the frontend /api proxy at runtime."
}
