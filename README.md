# 🚀 METRO Digital Cloud Creative Studio

![Angular](https://img.shields.io/badge/angular-%23DD0031.svg?style=for-the-badge&logo=angular&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)
![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)

**Creative Studio** is METRO Digital's enterprise deployment of Google Cloud's generative AI platform, enhanced with workspace collaboration, team management, and private workspace per user. Built on FastAPI + Angular, deployed on Cloud Run with infrastructure-as-code.

## 🎯 METRO Customizations

Unlike the upstream Google project, this fork adds:

| Feature | Description |
|---------|-------------|
| **Private Workspaces** | Each user gets one isolated workspace per group automatically |
| **Group Management** | AI Enabler and team-specific groups with shared resources |
| **Admin Provisioning** | Add users to groups → auto-create workspace, setup complete |
| **Email Domain Restriction** | IAP enforces `@metro.digital` or `@metro-gsc.in` access |
| **Cascade Delete Safety** | Delete user → workspaces transfer to another admin (no data loss) |
| **Workspace Switcher** | Switch between your private workspaces without re-login |

## 📖 Quick Start

### Option A: Deploy to Cloud Run (METRO 3-Env Setup)

Follow [CLOUD_SETUP.md](CLOUD_SETUP.md) for step-by-step deployment to:
- **Dev** (develop branch) → cf-genaistudi-genai-studio--gv
- **Pre-Production** (test branch) → cf-genaistudi-genai-studio--vm
- **Production** (main branch) → cf-genaistudi-genai-studio--7u

**Key requirement:** Organization IAM policy compliance (no primitive roles, Workload Identity Federation only).

### Option B: Local Development with Docker

For local development and testing:

```bash
# Prerequisites: Docker, Docker Compose, Python 3.11+, Node.js 18+

# 1. Clone and setup environment
git clone https://github.com/metro-digital-inner-source/gcc-creative-studio.git
cd gcc-creative-studio
cp .env.example .env  # Configure for local testing

# 2. Start local stack (PostgreSQL + Backend + Frontend)
docker-compose up --build

# 3. Access the app
# Frontend: http://localhost:4200
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Note:** Local Docker uses Firebase Admin SDK for auth. Cloud Run uses Google Identity Platform OIDC.
See [DEVELOPMENT.md](DEVELOPMENT.md) for full local setup details.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────┐
│  METRO Users (@metro.digital/@metro-gsc.in)  │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │ IAP + Email Check  │
         └─────────┬──────────┘
                   │
          ┌────────┴────────┐
          │                 │
    ┌─────▼─────┐    ┌─────▼──────┐
    │ Frontend  │    │  Backend   │
    │ Cloud Run │◄──►│  Cloud Run │
    │   (SSR)   │    │ (FastAPI)  │
    └─────┬─────┘    └─────┬──────┘
          │                │
          │      ┌─────────▼────────┐
          │      │   Cloud SQL      │
          │      │  PostgreSQL      │
          │      │ (user, group, ws)│
          │      └──────────────────┘
          │
          ├─► GCS (Brand Guidelines, Media)
          ├─► Secret Manager (API keys)
          └─► Vertex AI (Gemini, Imagen, Veo)
```

**Load Balancer + IAP** sits in front, enforcing email domain (`@metro.digital` / `@metro-gsc.in`) before traffic reaches Cloud Run.

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [CLOUD_SETUP.md](CLOUD_SETUP.md) | **Start here:** 3-env deployment, Terraform, GitHub Actions CI/CD |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Local Docker development, testing, debugging |
| [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) | Additional deployment configuration details |
| [DEPLOYMENT_REQUIRED_PERMISSIONS.md](DEPLOYMENT_REQUIRED_PERMISSIONS.md) | IAM roles required for deployment |
| [docs/](docs/) | METRO-specific guides (customizations, troubleshooting, WIF setup) |
| [SECURITY.md](SECURITY.md) | Security policies and incident response |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development guidelines and PR process |

## 🎨 Core Features

**🎬 Video Generation (Veo)**
- Generate videos from text or reference images
- ASSET consistency (reuse objects) or STYLE transfer modes

**🖼️ Image Generation (Imagen)**
- Text-to-image with advanced controls
- Integration with brand guidelines (PDF → automatic style transfer)

**✍️ Gemini Multimodal**
- Prompt rewriting for better generation results
- Multimodal critic (feedback on generated images)

**👥 Team Collaboration**
- Groups (e.g., "AI Enabler") with shared resources
- Private workspace per user (isolated projects)
- Admin dashboard for user/group management

## 🔐 Authentication & Authorization

- **Local Docker:** Firebase Admin SDK (development only)
- **Cloud Run:** Google Identity Platform OIDC
- **Access Control:** IAP email domain enforcement + RBAC per group
- **WIF:** No service account keys (GitHub Actions → Workload Identity Federation)

## ⚙️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Angular 18, TypeScript, Angular Material, Tailwind CSS |
| **Backend** | Python 3.11+, FastAPI, Pydantic, SQLAlchemy |
| **Database** | PostgreSQL (Cloud SQL on GCP, local postgres in Docker) |
| **Infrastructure** | Google Cloud Run, Cloud SQL, Artifact Registry, Secret Manager |
| **IaC** | Terraform (3-environment configuration) |
| **CI/CD** | GitHub Actions (WIF-based, no keys) + Cloud Build |
| **AI Models** | Vertex AI (Gemini, Imagen, Veo) |

## 🚀 Deployment Status

- ✅ Dev environment (develop branch) — actively deployed
- ✅ Pre-Production environment (test branch) — for final validation
- ✅ Production environment (main branch) — for end-users
- ✅ All 362 backend tests passing
- ✅ Frontend builds successfully (Angular 18)

## 📞 Support & Escalation

For issues, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

For urgent production incidents:
- **Backend/API issues:** Check Cloud Run logs via `gcloud run services describe`
- **Database issues:** Cloud SQL logs + connection troubleshooting
- **Deployment issues:** Check GitHub Actions workflow + Cloud Build logs

## 📝 License & Attribution

Licensed under [LICENSE](LICENSE). Based on [Google Cloud Creative Studio](https://github.com/GoogleCloudPlatform/gcc-creative-studio) with METRO Digital enhancements for enterprise team collaboration.

---

**Getting Started?** → [CLOUD_SETUP.md](CLOUD_SETUP.md) | **Local Development?** → [DEVELOPMENT.md](DEVELOPMENT.md) | **Troubleshooting?** → [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
