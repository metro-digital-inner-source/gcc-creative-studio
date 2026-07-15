# METRO Customizations Guide

This document details all custom features added to Creative Studio for METRO Digital, distinguishing them from the upstream Google Cloud project.

## Overview: What Changed

| Aspect | Upstream (Google) | METRO Fork |
|--------|-------------------|-----------|
| **Multi-tenancy** | Single organization, shared resources | Group-based, isolated private workspaces |
| **User Workspaces** | Global shared workspace | Private workspace per user per group |
| **Group Management** | N/A | AI Enabler + team groups with auto-provisioning |
| **Admin Interface** | N/A | Full admin dashboard (users, groups, workspaces) |
| **Email Restriction** | N/A | `@metro.digital` / `@metro-gsc.in` via IAP |
| **Auth Model** | Firebase Admin SDK (local) | Google Identity Platform OIDC (cloud) |
| **Data Safety** | N/A | Cascade delete prevention (workspace ownership transfer) |
| **Workspace Switcher** | N/A | UI switch between private workspaces without re-login |

## Feature Deep-Dive

### 1. Private Workspaces (Core Feature)

**What it is:** Each user gets one private workspace **per group** they join.

**Example:** If user `alice@metro.digital` is member of:
- "AI Enabler" group → workspace `alice-ai-enabler`
- "Video Team" group → workspace `alice-video-team`

Each workspace is fully isolated (projects, images, videos, etc.).

**Implementation:**
- Backend: `src/workspaces/workspace_service.py` (lines 45-120)
- Database: `workspaces` table has `user_id`, `group_id`, `workspace_type='private'`
- API: `POST /api/workspaces` auto-creates on user group membership

**User Experience:**
- Users don't manually create workspaces
- Workspace appears when added to group
- Switching workspaces via dropdown (top-right UI)
- Logout auto-clears workspace context

### 2. Group Management & Auto-Provisioning

**What it is:** Groups are teams. Add user to group → workspace auto-created.

**Admin Flow (from Admin Dashboard):**
1. Admin selects group (e.g., "AI Enabler")
2. Admin enters user email: `manish.singh@metro-gsc.in`
3. Backend:
   - Fetches/creates user account (Firebase)
   - Creates user record in DB
   - Creates private workspace for this user in this group
   - Adds user to group membership
4. User logs in next time → sees new workspace automatically

**Implementation:**
- Backend: `src/admin/admin_service.py` (lines 145-210)
  - `add_user_to_group_by_email()` method
  - Uses SQLAlchemy ORM (no raw SQL)
  - Includes error handling with logging
- Database: `user_group_association` junction table
- API: `POST /api/admin/users/add-to-group`

**Code Example (Backend):**
```python
# When user added to group, auto-create workspace
workspace = WorkspaceModel(
    user_id=user.id,
    group_id=group.id,
    workspace_type="private",
    created_at=datetime.utcnow()
)
db.add(workspace)
db.commit()
```

**Key Constraint:** Users get **exactly one workspace per group** (no multi-group assignment).

### 3. Admin Dashboard

**What it is:** Super-admin interface to manage users, groups, workspaces.

**Location:** Frontend at `/admin` (requires admin role)

**Capabilities:**
- **User Management**
  - View all users
  - Delete user (with ownership transfer if they own workspaces)
  - Reset user permissions/roles
  
- **Group Management**
  - View groups (AI Enabler, etc.)
  - Add members to group (via email)
  - Remove members from group
  
- **Workspace Management**
  - View all workspaces (private + shared)
  - Transfer ownership (if user deleted)
  - Reset/archive workspaces

**Frontend Code:**
- `src/app/admin/users-management/` — User CRUD operations
- `src/app/admin/groups-management/` — Group operations
- `src/app/admin/workspaces-management/` — Workspace operations

**Backend API:**
- `src/admin/admin_controller.py` — Admin endpoints
- `src/admin/admin_service.py` — Business logic

### 4. Email Domain Restriction (IAP)

**What it is:** Identity-Aware Proxy enforces email domain before app loads.

**Allowed Domains:**
- `@metro.digital`
- `@metro-gsc.in`

**How it works:**
1. User tries to access `https://cstudio-dev.metro.digital`
2. IAP intercepts → redirects to Google login (if not authenticated)
3. User logs in with their `@metro.digital` or `@metro-gsc.in` account
4. IAP verifies domain → allows traffic to Cloud Run
5. App receives `x-goog-iap-jwt-assertion` header with user info

**Configuration:**
- Terraform: `infra/modules/iap.tf` (sets IAP policy)
- Backend: `src/auth/auth_service.py` (reads JWT header, extracts email)
- Local Docker: Skipped (uses `ALLOWED_EMAILS` env var instead)

**For Local Testing:**
```bash
# .env
ENVIRONMENT=local
ALLOWED_EMAILS="alice@metro.digital,bob@metro-gsc.in"
```

### 5. Cascade Delete Prevention

**What it is:** Deleting a user doesn't accidentally delete groups/workspaces.

**Scenario (Before Fix):**
1. User `manish.singh@metro-gsc.in` is added to "AI Enabler" group
2. A shared workspace is created for the group
3. This shared workspace is assigned `owner_id = manish.singh`
4. **BUG:** Delete user → workspace deleted → group loses its shared workspace → group appears empty

**After Fix:**
1. Admin deletes user
2. Backend checks: "Does this user own any workspaces?"
3. Yes → find another admin in the same group → transfer ownership
4. If no other admin available → return 409 Conflict (refuse deletion)

**Implementation:**
- Backend: `src/users/user_service.py` (lines 158-205)
  - `delete_user()` checks workspace ownership
  - Uses bulk UPDATE statement (SQLAlchemy)
  - Transfers ownership to first found admin
  - Returns error if no admin available for transfer

**Code Example:**
```python
def delete_user(user_id: str, db_session):
    user = db_session.query(UserModel).get(user_id)
    
    # Find workspaces owned by this user
    owned_workspaces = db_session.query(WorkspaceModel).filter(
        WorkspaceModel.owner_id == user_id
    ).all()
    
    # Transfer to another admin in same group
    for workspace in owned_workspaces:
        other_admin = find_group_admin(workspace.group_id, exclude_user_id=user_id)
        if other_admin:
            db_session.execute(
                update(WorkspaceModel).where(
                    WorkspaceModel.id == workspace.id
                ).values(owner_id=other_admin.id)
            )
        else:
            raise 409 Conflict("User owns workspaces with no other admin to transfer to")
    
    # Then soft-delete user
    user.deleted_at = datetime.utcnow()
    db_session.commit()
```

**API Behavior:**
- `DELETE /api/users/{user_id}`
- Returns `200 OK` (transfer successful)
- Returns `409 Conflict` (no admin available)
- Returns `404 Not Found` (user doesn't exist)

### 6. Workspace Switcher (UI Feature)

**What it is:** Dropdown in top-right to switch between user's private workspaces.

**Location:** Frontend main navbar, after user avatar

**How it works:**
1. User logs in → backend returns list of workspaces they belong to
2. UI dropdown shows: "AI Enabler Workspace", "Video Team Workspace", etc.
3. User clicks one → app reloads workspace context (projects, galleries, etc.)
4. No re-login needed

**Frontend Code:**
- `src/app/components/workspace-switcher/` — Component logic
- `src/app/services/workspace/workspace.service.ts` — API calls

**Backend API:**
- `GET /api/workspaces/my-workspaces` — List user's workspaces
- `POST /api/workspaces/{workspace_id}/activate` — Switch to workspace

**Local Testing:**
```bash
# 1. Login as alice@metro.digital
# 2. Add alice to multiple groups via admin dashboard
# 3. UI should show dropdown with multiple workspaces
```

### 7. Auto-Generated Workspace Names

**What it is:** Workspaces auto-name using pattern: `{user-email-prefix}-{group-name-slug}`

**Examples:**
- User `alice` + Group "AI Enabler" → `alice-ai-enabler`
- User `bob.smith` + Group "Video Team" → `bob-smith-video-team`

**Implementation:**
- Backend: `src/workspaces/workspace_service.py` (lines 80-95)
  - Extracts email prefix before `@`
  - Slugifies group name (lowercase, replace spaces with hyphens)
  - Ensures uniqueness (appends counter if collision)

**Database:** `workspaces.name` field, unique constraint per group

## Migration from Upstream

If you're updating from the upstream Google project to this METRO fork:

### 1. Database Schema Changes

New tables:
- `group` — Team/group entity
- `user_group_association` — User ↔ Group membership

New columns:
- `users.deleted_at` — Soft delete timestamp
- `workspaces.workspace_type` — 'private' or 'shared'
- `workspaces.group_id` — FK to group

**Migration Script:** `backend/alembic/versions/001_initial_schema.py`

Run: `alembic upgrade head` (auto-runs on Cloud Run deploy)

### 2. Environment Variables

New required for cloud:
```bash
# Cloud Run
ENVIRONMENT=production
GOOGLE_TOKEN_AUDIENCE=YOUR_OAUTH_CLIENT_ID
IDENTITY_PLATFORM_ALLOWED_ORGS=""  # Or specific domains
ALLOWED_EMAILS=""  # For local dev only
```

### 3. Firebase vs Identity Platform

**Upstream:** Firebase Admin SDK (development only)
**METRO:** Google Identity Platform OIDC (production)

For cloud deployment:
1. Create OAuth 2.0 Client ID in Google Cloud Console
2. Set `GOOGLE_TOKEN_AUDIENCE` to client ID
3. Update IAP policy to use this client

**For local dev:** Still use Firebase Admin SDK (via docker-compose)

## Comparison: Key Code Differences

### User Deletion (Cascade Safety)

**Upstream:**
```python
@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, db: Session):
    user = db.query(User).get(user_id)
    db.delete(user)  # ❌ Cascades! Deletes workspaces, galleries, etc.
    db.commit()
```

**METRO:**
```python
@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, db: Session):
    user = db.query(User).get(user_id)
    
    # Transfer ownership first
    owned_workspaces = db.query(Workspace).filter_by(owner_id=user_id).all()
    for ws in owned_workspaces:
        other_admin = find_group_admin(ws.group_id, exclude_user_id=user_id)
        if not other_admin:
            raise HTTPException(409, "No admin to transfer ownership to")
        db.execute(update(Workspace).where(Workspace.id == ws.id).values(owner_id=other_admin.id))
    
    # Then soft-delete
    user.deleted_at = datetime.utcnow()
    db.commit()  # ✅ Safe! Workspaces preserved
```

### Workspace Creation (Auto-creation)

**Upstream:** Users manually create workspaces via UI

**METRO:** Workspaces auto-created when user joins group
```python
def add_user_to_group_by_email(email: str, group_id: str, db: Session):
    user = get_or_create_user(email)
    db.add(UserGroupAssociation(user_id=user.id, group_id=group_id))
    
    # Auto-create workspace
    workspace = Workspace(
        user_id=user.id,
        group_id=group_id,
        name=generate_workspace_name(user, group),
        workspace_type="private"
    )
    db.add(workspace)
    db.commit()
```

## Testing METRO Features

### Unit Tests

```bash
# Backend tests (all 362 tests)
cd backend
pytest tests/

# Specific test file
pytest tests/admin/test_admin_service.py -v
```

### Integration Tests (Local Docker)

```bash
# Start docker-compose
docker-compose up -d

# 1. Admin adds user to group
curl -X POST http://localhost:8000/api/admin/users/add-to-group \
  -H "Content-Type: application/json" \
  -d '{"email":"test@metro.digital","group_id":"ai-enabler"}'

# 2. User logs in (auto-gets workspace)
curl http://localhost:8000/api/users/me

# 3. User sees workspace in list
curl http://localhost:8000/api/workspaces/my-workspaces

# 4. User switches workspace (updates context)
curl -X POST http://localhost:8000/api/workspaces/WORKSPACE_ID/activate

# 5. Admin deletes user (should transfer ownership)
curl -X DELETE http://localhost:8000/api/users/USER_ID
```

### Manual UI Testing

1. **Setup:** Multiple test users in different groups
2. **Test 1:** Login as user1 → verify sees private workspace only
3. **Test 2:** Add user1 to second group → logout → login → should see both workspaces
4. **Test 3:** Use workspace switcher dropdown → verify projects/galleries change
5. **Test 4:** Admin deletes user1 → verify workspace still exists + transferred to admin2

## Reverting to Upstream (If Needed)

If you need to go back to upstream Google project:

```bash
# Fetch upstream
git fetch upstream main

# Create a branch tracking upstream
git checkout -b upstream-main upstream/main

# Review differences
git diff main..upstream-main

# If you want to rebase (destructive!)
git rebase upstream-main main  # ⚠️ Loses all METRO changes
```

**⚠️ WARNING:** Reverting means losing:
- Group management
- Private workspaces
- Admin dashboard
- Email restriction
- All METRO-specific data

Keep METRO fork unless you have strong reason to return to upstream.

## Support & Documentation

For more details:
- [README.md](../README.md) — Project overview
- [CLOUD_SETUP.md](../CLOUD_SETUP.md) — Deployment guide
- [DEVELOPMENT.md](../DEVELOPMENT.md) — Local development
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Common issues
