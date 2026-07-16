#!/bin/bash

# Git Merge Script - Feature to Develop
# This script stages changes, commits, and merges feature/group-governance to develop

set -e  # Exit on error

echo "========================================="
echo "Starting Merge Process"
echo "========================================="
echo ""

# Navigate to repository root
cd /Users/joejoseph.george/Workspace/GenAI_Studio/gcc-creative-studio

# Show current branch
echo "Current branch:"
git branch --show-current
echo ""

# Show status before staging
echo "Git status before staging:"
git status --short
echo ""

# Stage all changed files
echo "Staging changed files..."
git add backend/src/groups/repository/group_repository.py
git add backend/src/admin/admin_service.py
git add backend/src/admin/admin_controller.py
git add backend/src/galleries/gallery_service.py
git add backend/src/workspaces/workspace_service.py
git add backend/src/workspaces/dto/invite_user_dto.py
git add frontend/src/app/admin/users-management/users-management.component.ts
git add frontend/src/app/admin/users-management/users-management.component.html
git add frontend/src/app/services/group/group.service.ts
git add frontend/src/app/gallery/gallery.service.ts
git add frontend/src/app/common/components/invite-user-modal/invite-user-modal.component.ts
git add frontend/src/app/common/components/media-lightbox/media-lightbox.component.ts
git add frontend/src/app/common/components/media-lightbox/media-lightbox.component.html

echo "✓ Files staged"
echo ""

# Show what's staged
echo "Staged changes:"
git status --short
echo ""

# Commit with detailed message
echo "Creating commit..."
git commit -F COMMIT_MESSAGE.md

echo "✓ Commit created"
echo ""

# Show commit details
echo "Commit details:"
git log -1 --stat
echo ""

# Ask for confirmation before merge
echo "========================================="
echo "Ready to merge to develop branch"
echo "========================================="
read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Merge cancelled by user"
    exit 0
fi

# Switch to develop and merge
echo "Switching to develop branch..."
git checkout develop

echo "Pulling latest changes from origin..."
git pull origin develop

echo "Merging feature/group-governance..."
git merge feature/group-governance --no-ff -m "Merge feature/group-governance: Group Governance & Media Rendering Fixes

See COMMIT_MESSAGE.md for full details.

Key Changes:
- 🔴 CRITICAL: Fixed media rendering AttributeError
- ✨ Added group deletion functionality (admin)
- ✨ Enhanced user invitation with mandatory groups
- ✨ Replaced social media share with group gallery sharing
- 🐛 Fixed group creation visibility issue
- 🛠️ Improved authorization and error handling

Backend: 7 files | Frontend: 7 files
Deployment Ready: ✅ Backend | ⚠️ Frontend (pending permissions)"

echo "✓ Merge complete"
echo ""

# Show merge result
echo "Merge commit:"
git log -1 --oneline
echo ""

# Ask about pushing
echo "========================================="
echo "Ready to push to origin/develop"
echo "========================================="
read -p "Do you want to push to origin? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Pushing to origin/develop..."
    git push origin develop
    echo "✓ Pushed to origin"
    echo ""
    echo "========================================="
    echo "Merge Process Complete!"
    echo "========================================="
    echo ""
    echo "Next Steps:"
    echo "1. Cloud Build will auto-deploy backend to dev environment"
    echo "2. Monitor deployment: https://console.cloud.google.com/cloud-build"
    echo "3. Test in dev environment after deployment"
    echo "4. Request Firebase permissions for frontend deployment"
else
    echo "Push cancelled. You can push manually with:"
    echo "  git push origin develop"
fi

echo ""
echo "Done! 🚀"
