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

################################################################################
# LOCAL DOCKER DEPLOYMENT BOOTSTRAP
# 
# ⚠️  LOCAL ONLY - DOES NOT AFFECT CLOUD DEPLOYMENTS ⚠️
#
# This script resets and restarts your LOCAL Docker development environment.
# It does NOT:
#   - Run any gcloud commands
#   - Trigger Cloud Build
#   - Modify cloud infrastructure
#   - Push to remote repositories
#   - Change production/staging environments
#
# Safe to run anytime you want a fresh local development environment.
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  GCC Creative Studio - Local Docker Bootstrap${NC}"
echo -e "${YELLOW}  ⚠️  LOCAL ONLY - Does not affect cloud deployments ⚠️${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Verify we're on develop branch
echo -e "${BLUE}[1/8]${NC} Checking git branch..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo -e "${YELLOW}⚠️  Warning: You are on branch '${CURRENT_BRANCH}', not 'develop'${NC}"
    echo -e "${YELLOW}   This script is designed for the develop branch.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborted.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ On develop branch${NC}"
fi

# Step 2: Verify environment files exist
echo ""
echo -e "${BLUE}[2/8]${NC} Checking environment files..."

if [ ! -f "backend/.env" ]; then
    echo -e "${RED}✗ backend/.env not found!${NC}"
    echo -e "${YELLOW}Please create backend/.env with local configuration.${NC}"
    echo -e "${YELLOW}See documentation for required values.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ backend/.env exists${NC}"

if [ ! -f "frontend/src/environments/environment.development.ts" ]; then
    echo -e "${RED}✗ frontend environment file not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ frontend/src/environments/environment.development.ts exists${NC}"

# Step 3: Stop and remove existing containers + volumes
echo ""
echo -e "${BLUE}[3/8]${NC} Stopping and removing existing containers..."
if docker-compose ps -q 2>/dev/null | grep -q .; then
    docker-compose down -v
    echo -e "${GREEN}✓ Cleaned up old containers and volumes${NC}"
else
    echo -e "${GREEN}✓ No existing containers to remove${NC}"
fi

# Step 4: Verify Docker is running
echo ""
echo -e "${BLUE}[4/8]${NC} Verifying Docker is running..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Step 5: Build fresh containers
echo ""
echo -e "${BLUE}[5/8]${NC} Building containers (this may take a few minutes)..."
docker-compose build --no-cache
echo -e "${GREEN}✓ Containers built successfully${NC}"

# Step 6: Start services
echo ""
echo -e "${BLUE}[6/8]${NC} Starting services..."
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"

# Step 7: Wait for services to be healthy
echo ""
echo -e "${BLUE}[7/8]${NC} Waiting for services to be healthy..."
echo -n "Waiting for database"
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U studio_user -d creative_studio > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Database took longer than expected, but continuing...${NC}"
    fi
done

echo -n "Waiting for backend to start"
for i in {1..60}; do
    if docker-compose logs backend 2>&1 | grep -q "Application startup complete"; then
        echo ""
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 60 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Backend took longer than expected${NC}"
        echo -e "${YELLOW}   Check logs with: docker-compose logs backend${NC}"
    fi
done

# Step 8: Display status and health checks
echo ""
echo -e "${BLUE}[8/8]${NC} Running health checks..."
echo ""

# Service status
echo -e "${BLUE}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Local development environment is ready!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Access your services:${NC}"
echo -e "  ${GREEN}Frontend:${NC}  http://localhost:4200"
echo -e "  ${GREEN}Backend:${NC}   http://localhost:9000/api"
echo -e "  ${GREEN}Adminer:${NC}   http://localhost:8081"
echo -e "  ${GREEN}Postgres:${NC}  localhost:5432"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  ${YELLOW}View all logs:${NC}       docker-compose logs -f"
echo -e "  ${YELLOW}View backend logs:${NC}   docker-compose logs -f backend"
echo -e "  ${YELLOW}View frontend logs:${NC}  docker-compose logs -f frontend"
echo -e "  ${YELLOW}Stop services:${NC}       docker-compose down"
echo -e "  ${YELLOW}Restart services:${NC}    docker-compose restart"
echo ""
echo -e "${YELLOW}⚠️  Remember to allow popups in your browser for localhost:4200${NC}"
echo -e "${YELLOW}   (Required for Firebase authentication)${NC}"
echo ""
