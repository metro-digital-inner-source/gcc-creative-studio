# Local Development Guide

**⚠️ This guide is for LOCAL Docker development only and does NOT affect cloud deployments.**

## Quick Start

```bash
# One-command setup (from repo root)
./bootstrap-local.sh
```

This script will:
- ✅ Clean up old containers and volumes
- ✅ Build fresh Docker images
- ✅ Start all services (frontend, backend, postgres, adminer)
- ✅ Wait for services to be healthy
- ✅ Display access URLs and useful commands

## Prerequisites

1. **Docker Desktop** installed and running
2. **Git** on `develop` branch (or branch with local config)
3. **Environment files** configured (see below)

## Environment Configuration

### 1. Backend Environment (`.env`)

**Location**: `backend/.env`

**⚠️ This file is gitignored and must be created locally**

```bash
# Common env vars
FRONTEND_URL="http://localhost:4200"
ENVIRONMENT="local"
LOG_LEVEL="INFO"

# Project ID: cf-genaistudi-genai-studio--gv (dev project)
GOOGLE_CLOUD_PROJECT="cf-genaistudi-genai-studio--gv"
PROJECT_ID="cf-genaistudi-genai-studio--gv"
GENMEDIA_BUCKET="cf-genaistudi-genai-studio--gv-cs-development-bucket"
SIGNING_SA_EMAIL="cs-development-read@cf-genaistudi-genai-studio--gv.iam.gserviceaccount.com"
GOOGLE_TOKEN_AUDIENCE="211114879177-ike5p3lh888itb7ge6bekl9a9f59io9k.apps.googleusercontent.com"
IDENTITY_PLATFORM_ALLOWED_ORGS=""

# --- Database Configuration (Local Docker Postgres) ---
DB_USER="studio_user"
DB_PASS="studio_pass"
DB_NAME="creative_studio"
DB_HOST="postgres"
DB_PORT="5432"
USE_CLOUD_SQL_AUTH_PROXY=false
ADMIN_USER_EMAIL="test@example.com"
```

### 2. Frontend Environment (`environment.development.ts`)

**Location**: `frontend/src/environments/environment.development.ts`

**Key settings for local development:**

```typescript
export const environment = {
  firebase: {
    apiKey: 'AIzaSyA7NbHjxfNNjKAryGrB-7enKr5c0bK3RJc',
    authDomain: 'cf-genaistudi-genai-stud-6ae6c.firebaseapp.com',
    projectId: 'cf-genaistudi-genai-studio--gv',
    storageBucket: 'cf-genaistudi-genai-studio--gv.firebasestorage.app',
    messagingSenderId: '211114879177',
    appId: '1:211114879177:web:1083fcfb3573a483c48518',
    measurementId: 'G-E68V431TV4',
  },
  production: false,
  isLocal: true,  // ← IMPORTANT: Enables Firebase popup auth
  backendURL: 'http://localhost:9000/api',  // ← Local backend
  // ... other settings
};
```

## Services & Ports

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:4200 | Angular application |
| **Backend API** | http://localhost:9000/api | FastAPI backend |
| **PostgreSQL** | localhost:5432 | Database (user: `studio_user`, pass: `studio_pass`, db: `creative_studio`) |
| **Adminer** | http://localhost:8081 | Database management UI |

## Manual Commands

If you prefer not to use the bootstrap script:

```bash
# Stop and clean everything
docker-compose down -v

# Build containers
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

## Authentication Setup

**Local development uses Firebase popup authentication.**

### Browser Configuration

**⚠️ IMPORTANT**: You must allow popups for `localhost:4200` in your browser.

#### Chrome
1. Click the popup blocker icon in the address bar (🚫)
2. Select "Always allow pop-ups from localhost:4200"
3. Refresh the page

#### Safari
1. Click the popup blocker icon in the address bar
2. Select "Allow"
3. For permanent: Safari → Settings → Websites → Pop-up Windows → Allow for localhost

#### Firefox
1. Click the popup blocker icon in the address bar
2. Select "Allow popups for localhost:4200"

## Troubleshooting

### Backend fails to start

**Check logs**:
```bash
docker-compose logs backend | grep -i "error\|failed"
```

**Common issues**:
- Database migrations failing → Run `docker-compose down -v` to reset DB
- Port 9000 already in use → Check for other running processes
- Missing `.env` file → Create `backend/.env` with required values

### Frontend won't connect to backend

**Verify**:
```bash
curl http://localhost:9000/api
# Should return: {"detail":"Not Found"}

curl http://localhost:4200
# Should return HTML
```

**Common issues**:
- Backend not running → Check `docker-compose ps`
- Wrong `backendURL` in environment.development.ts
- CORS errors → Verify `FRONTEND_URL` in backend `.env`

### Login popup blocked or closes immediately

**This is a browser security feature, not a code issue.**

**Solution**: Allow popups for localhost:4200 (see Authentication Setup above)

### Database connection errors

**Reset database**:
```bash
docker-compose down -v  # Removes volumes
docker-compose up -d    # Recreates fresh DB
```

**Check database is healthy**:
```bash
docker-compose exec postgres pg_isready -U studio_user -d creative_studio
```

## Development Workflow

### Making code changes

**Backend changes**:
- Code is mounted as volume, but Python dependencies require rebuild
- Hot reload is enabled for FastAPI

**Frontend changes**:
- Vite dev server provides hot module replacement
- Changes reflect immediately in browser

### Rebuilding after dependency changes

```bash
# Backend: requirements changed
docker-compose build backend
docker-compose restart backend

# Frontend: package.json changed
docker-compose build frontend
docker-compose restart frontend
```

### Running tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
cd frontend
npm run test
```

### Database migrations

**Create new migration**:
```bash
docker-compose exec backend alembic revision -m "description"
```

**Apply migrations**:
```bash
docker-compose exec backend alembic upgrade head
```

**Migrations run automatically on backend startup.**

## Cleaning Up

```bash
# Stop services (keeps volumes)
docker-compose down

# Stop and remove volumes (full clean)
docker-compose down -v

# Remove images too
docker-compose down -v --rmi all
```

## Differences from Cloud Deployment

| Aspect | Local | Cloud |
|--------|-------|-------|
| **Environment** | `ENVIRONMENT=local` | `ENVIRONMENT=development/production` |
| **Database** | Docker Postgres | Cloud SQL |
| **Authentication** | Firebase popup | Google Identity Platform One Tap |
| **Storage** | GCS (dev bucket) | GCS (env-specific bucket) |
| **Secrets** | `.env` file | Secret Manager |
| **Deployment** | Docker Compose | Cloud Run + Firebase Hosting |

## Cloud Deployment

**This local setup does NOT affect cloud deployments.**

For cloud deployment instructions, see:
- [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md) - Cloud deployment guide
- [infra/GITHUB_ACTIONS_SETUP.md](infra/GITHUB_ACTIONS_SETUP.md) - CI/CD setup

## Need Help?

1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Full reset: `./bootstrap-local.sh`
4. Still stuck? Check the troubleshooting section above
