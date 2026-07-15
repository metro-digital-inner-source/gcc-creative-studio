# Tooling Role Summary

This note records the role of key platform and delivery tools used in this repository.

## Git

Git is the source-control layer for the project. It is used for cloning, branching, committing, merging, and syncing changes, and the repository follows a branch strategy where `develop`, `test`, and `main` map to different target environments.

## GitHub Actions

GitHub Actions runs repository-side automation. In this project it is responsible for backend quality checks, frontend linting, license checks, and Terraform plan/apply workflows tied to branch and path changes.

## Terraform

Terraform is the infrastructure-as-code layer. It defines and provisions the Google Cloud resources used by each environment, including Cloud Build connections and triggers, Cloud Run services, Firebase Hosting resources, Secret Manager integration, and Cloud SQL.

## Google Cloud

Google Cloud is the runtime platform for the application. The project uses GCP services such as Cloud Run for the backend, Cloud SQL for PostgreSQL, Cloud Build for build and deployment automation, Secret Manager for secrets, and Vertex AI for Gemini, Imagen, and Veo-backed AI features.

## Firebase

Firebase is used mainly for the frontend surface. In this project it provides Hosting for the Angular app and rewrites `/api/**` traffic to the backend Cloud Run service, while also supplying frontend configuration values used by the deployed app.