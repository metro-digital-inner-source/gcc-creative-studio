# Documentation Index

Welcome to METRO Digital's Creative Studio documentation. This guide will help you find the right information for your task.

## 🚀 Getting Started

**New to the project?** Start here:

1. [../README.md](../README.md) — Project overview, key features, quick links
2. [../CLOUD_SETUP.md](../CLOUD_SETUP.md) — Step-by-step deployment guide (required reading)
3. [../DEVELOPMENT.md](../DEVELOPMENT.md) — Local development with Docker

## 📚 Main Documentation

### Deployment & Infrastructure

| Document | Purpose | Audience |
|----------|---------|----------|
| [../CLOUD_SETUP.md](../CLOUD_SETUP.md) | Complete deployment walkthrough (3 environments, Terraform, GitHub Actions) | DevOps, Backend engineers |
| [../DEPLOYMENT_SETUP.md](../DEPLOYMENT_SETUP.md) | Environment configuration details | DevOps, Infrastructure team |
| [../DEPLOYMENT_REQUIRED_PERMISSIONS.md](../DEPLOYMENT_REQUIRED_PERMISSIONS.md) | IAM roles required for deployment | GCP admins, Security team |
| [GIT_COMMANDS.md](GIT_COMMANDS.md) | Git workflow for METRO (branching, merging, commits) | All developers |
| [../COMMIT_MESSAGE.md](../COMMIT_MESSAGE.md) | Conventional commit message format | All developers |

### Development & Architecture

| Document | Purpose | Audience |
|----------|---------|----------|
| [../DEVELOPMENT.md](../DEVELOPMENT.md) | Local development setup (Docker, debugging, testing) | Backend & Frontend engineers |
| [METRO_CUSTOMIZATIONS.md](METRO_CUSTOMIZATIONS.md) | METRO-specific features (groups, workspaces, admin) | Backend engineers, new team members |
| [FRONTEND_BACKEND_ALIGNMENT_PLAN.md](FRONTEND_BACKEND_ALIGNMENT_PLAN.md) | Architecture decisions, design patterns | Leads, architects |

### Operations & Troubleshooting

| Document | Purpose | Audience |
|----------|---------|----------|
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions | DevOps, on-call engineers |
| [../SECURITY.md](../SECURITY.md) | Security policies, incident response | Security team, all developers |
| [ADDITIONAL_ROLES_NEEDED.md](ADDITIONAL_ROLES_NEEDED.md) | Special permissions for team members | HR, managers |

### Contributing & Guidelines

| Document | Purpose | Audience |
|----------|---------|----------|
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | Development guidelines, PR process | All developers |
| [../CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | Team behavior and conduct | Everyone |

---

## 🔍 Quick Reference by Role

### I'm a... **New Team Member**
1. Read [../README.md](../README.md) for overview
2. Read [../DEVELOPMENT.md](../DEVELOPMENT.md) to set up local dev
3. Read [METRO_CUSTOMIZATIONS.md](METRO_CUSTOMIZATIONS.md) to understand what's different from upstream
4. Read [GIT_COMMANDS.md](GIT_COMMANDS.md) to learn our git workflow

### I'm a... **Backend Engineer**
1. Start with [../DEVELOPMENT.md](../DEVELOPMENT.md) for local setup
2. Read [METRO_CUSTOMIZATIONS.md](METRO_CUSTOMIZATIONS.md) for architecture
3. Understand database: `backend/alembic/versions/` (migrations)
4. Use [TROUBLESHOOTING.md](TROUBLESHOOTING.md) when debugging
5. Follow [../COMMIT_MESSAGE.md](../COMMIT_MESSAGE.md) for commits

### I'm a... **Frontend Engineer**
1. Start with [../DEVELOPMENT.md](../DEVELOPMENT.md) for local setup
2. Read [METRO_CUSTOMIZATIONS.md](METRO_CUSTOMIZATIONS.md) for workspace/group features
3. Check [FRONTEND_BACKEND_ALIGNMENT_PLAN.md](FRONTEND_BACKEND_ALIGNMENT_PLAN.md) for API contracts
4. Use [TROUBLESHOOTING.md](TROUBLESHOOTING.md) when debugging

### I'm a... **DevOps / Infrastructure Engineer**
1. Read [../CLOUD_SETUP.md](../CLOUD_SETUP.md) — complete deployment walkthrough
2. Read [../DEPLOYMENT_SETUP.md](../DEPLOYMENT_SETUP.md) — environment configuration
3. Read [../DEPLOYMENT_REQUIRED_PERMISSIONS.md](../DEPLOYMENT_REQUIRED_PERMISSIONS.md) — IAM roles
4. Bookmark [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for on-call use

### I'm a... **GCP Admin / Security Team**
1. Read [../DEPLOYMENT_REQUIRED_PERMISSIONS.md](../DEPLOYMENT_REQUIRED_PERMISSIONS.md) — required roles
2. Read [../SECURITY.md](../SECURITY.md) — security policies
3. Run [../infra/setup-terraform-service-accounts.sh](../infra/setup-terraform-service-accounts.sh) to create service accounts
4. Review [../CLOUD_SETUP.md](../CLOUD_SETUP.md) for architecture approval

### I'm a... **Incident Responder / On-Call**
1. Use [TROUBLESHOOTING.md](TROUBLESHOOTING.md) as your guide
2. Run diagnostic commands (listed at bottom of troubleshooting)
3. If stuck, check [../CLOUD_SETUP.md](../CLOUD_SETUP.md) for escalation contacts
4. Document findings for postmortem

---

## 📋 Common Tasks

### **How do I deploy to dev?**
→ [../CLOUD_SETUP.md](../CLOUD_SETUP.md) - Step 3: Deploy Terraform

### **How do I set up my local development environment?**
→ [../DEVELOPMENT.md](../DEVELOPMENT.md) - Local Docker section

### **How do I add a new user to a group?**
→ [METRO_CUSTOMIZATIONS.md](METRO_CUSTOMIZATIONS.md) - Section: Admin Dashboard

### **My user sync failed, what do I do?**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Section: "Could not synchronize user profile"

### **I broke the database, how do I fix it?**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Section: Database Issues

### **How do I roll back a deployment?**
→ [../CLOUD_SETUP.md](../CLOUD_SETUP.md) - Rollback Procedures section

### **What are the security requirements?**
→ [../SECURITY.md](../SECURITY.md)

### **How do I make a commit?**
→ [../COMMIT_MESSAGE.md](../COMMIT_MESSAGE.md) and [GIT_COMMANDS.md](GIT_COMMANDS.md)

---

## 🏗️ Project Structure

**METRO Deployment Architecture:**
```
Users (@metro.digital / @metro-gsc.in)
    ↓
HTTPS Load Balancer + IAP (email restriction)
    ├─ Frontend Cloud Run (cstudio-frontend-dev) → Angular SSR
    ├─ Backend Cloud Run (cstudio-backend-dev) → FastAPI
    └─ Cloud SQL (PostgreSQL) → User, Group, Workspace data
```

**Key Infrastructure Files:**
- Terraform: `../infra/environments/dev|pp|prod/` (3-env setup)
- Backend: `../backend/src/` (FastAPI services)
- Frontend: `../frontend/src/app/` (Angular components)
- Database: `../backend/alembic/versions/` (migrations)

For detailed architecture:
→ [../CLOUD_SETUP.md](../CLOUD_SETUP.md) - Architecture Diagram section
→ [METRO_CUSTOMIZATIONS.md](METRO_CUSTOMIZATIONS.md) - Feature Deep-Dive

---

## 📚 Records & Archived Documents

- [Tooling role summary](./records/tooling-role-summary.md)
- [Archived documents](./archive/)

---

## 📞 Support & Escalation

If you can't find the answer:

1. **Check TROUBLESHOOTING.md** — Most issues are documented there
2. **Search GitHub Issues** — Look for similar problems
3. **Ask in team Slack** — Tag relevant team members
4. **Create a ticket** — If it's a new issue or bug

For critical production issues:
→ [../CLOUD_SETUP.md](../CLOUD_SETUP.md) - Team Escalation & Support section

---

## 💡 Tips

- **Bookmark this page** (docs/README.md) for quick reference
- **Use Ctrl+F** to search within documents
- **GitHub Search** for code: Press `/` on github.com and search `path:docs`
- **Local search** in VS Code: Ctrl+Shift+F to search all docs

Happy coding! 🚀