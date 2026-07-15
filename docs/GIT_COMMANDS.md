# Quick Git Commands Reference

## Option 1: Use Automated Script (Recommended)

```bash
cd /Users/joejoseph.george/Workspace/GenAI_Studio/gcc-creative-studio
chmod +x merge-to-develop.sh
./merge-to-develop.sh
```

The script will:
- Stage all changed files
- Commit with comprehensive message
- Ask for confirmation before merge
- Switch to develop branch
- Pull latest changes
- Merge feature branch
- Ask for confirmation before push
- Push to origin/develop

---

## Option 2: Manual Git Commands

### Step 1: Stage Changed Files
```bash
cd /Users/joejoseph.george/Workspace/GenAI_Studio/gcc-creative-studio

# Backend files
git add backend/src/groups/repository/group_repository.py
git add backend/src/admin/admin_service.py
git add backend/src/admin/admin_controller.py
git add backend/src/galleries/gallery_service.py
git add backend/src/workspaces/workspace_service.py
git add backend/src/workspaces/dto/invite_user_dto.py

# Frontend files
git add frontend/src/app/admin/users-management/users-management.component.ts
git add frontend/src/app/admin/users-management/users-management.component.html
git add frontend/src/app/services/group/group.service.ts
git add frontend/src/app/gallery/gallery.service.ts
git add frontend/src/app/common/components/invite-user-modal/invite-user-modal.component.ts
git add frontend/src/app/common/components/media-lightbox/media-lightbox.component.ts
git add frontend/src/app/common/components/media-lightbox/media-lightbox.component.html
```

### Step 2: Check Staged Files
```bash
git status
```

### Step 3: Commit with Detailed Message
```bash
git commit -F COMMIT_MESSAGE.md
```

### Step 4: Review Commit
```bash
git log -1 --stat
```

### Step 5: Switch to Develop Branch
```bash
git checkout develop
```

### Step 6: Pull Latest Changes
```bash
git pull origin develop
```

### Step 7: Merge Feature Branch
```bash
git merge feature/group-governance --no-ff -m "Merge feature/group-governance: Group Governance & Media Rendering Fixes"
```

### Step 8: Push to Origin
```bash
git push origin develop
```

---

## Option 3: Create Pull Request (Recommended for Team Review)

### Via GitHub CLI
```bash
gh pr create --base develop --head feature/group-governance \
  --title "Group Governance & Media Rendering Fixes" \
  --body-file COMMIT_MESSAGE.md
```

### Via GitHub Web
1. Go to: https://github.com/YOUR_ORG/gcc-creative-studio/compare/develop...feature/group-governance
2. Click "Create Pull Request"
3. Copy content from `COMMIT_MESSAGE.md` into PR description
4. Assign reviewers
5. Wait for approval
6. Merge via GitHub UI

---

## Post-Merge Verification

### Check Cloud Build Status
```bash
# View recent builds
gcloud builds list --limit=5

# Follow specific build
gcloud builds log BUILD_ID --stream
```

### Monitor Deployment
- Console: https://console.cloud.google.com/cloud-build
- Cloud Run: https://console.cloud.google.com/run
- Logs: https://console.cloud.google.com/logs

### Test Deployed Changes
1. Navigate to dev environment URL
2. Test group deletion functionality
3. Test user invitation with groups
4. Test share to group gallery
5. Verify media rendering works

---

## Rollback (If Needed)

### Revert Merge Commit
```bash
git revert -m 1 HEAD
git push origin develop
```

### Or Reset to Previous State
```bash
git reset --hard HEAD~1
git push origin develop --force  # ⚠️ Use with caution
```

---

## Files Changed Summary

**Backend (7 files):**
- groups/repository/group_repository.py
- admin/admin_service.py
- admin/admin_controller.py
- galleries/gallery_service.py
- workspaces/workspace_service.py
- workspaces/dto/invite_user_dto.py

**Frontend (7 files):**
- admin/users-management/users-management.component.ts
- admin/users-management/users-management.component.html
- services/group/group.service.ts
- gallery/gallery.service.ts
- common/components/invite-user-modal/invite-user-modal.component.ts
- common/components/media-lightbox/media-lightbox.component.ts
- common/components/media-lightbox/media-lightbox.component.html

---

## Need Help?

**View commit message:**
```bash
cat COMMIT_MESSAGE.md
```

**View this guide:**
```bash
cat docs/GIT_COMMANDS.md
```

**Check current branch:**
```bash
git branch --show-current
```

**See what's changed:**
```bash
git diff develop
```
