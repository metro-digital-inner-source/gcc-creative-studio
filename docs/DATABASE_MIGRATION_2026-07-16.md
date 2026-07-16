# Database Migration - Fix AI Enabler Workspace Scope

**Date**: 2026-07-16  
**Purpose**: Update existing AI Enabler workspace from PRIVATE to GLOBAL scope  
**Reason**: Bug fix - non-admin users could not see PRIVATE workspace, causing "Please select workspace first" error

---

## Prerequisites

- GCP Cloud SQL connection access
- `gcloud` CLI authenticated
- Database credentials available

---

## Connect to Database

```bash
# Connect to Cloud SQL instance
gcloud sql connect creative-studio-db-c40e8b4d \
  --user=studio_user \
  --database=creative_studio \
  --project=cf-genaistudi-genai-studio--gv
```

Enter password when prompted (stored in Secret Manager: `creative-studio-db-password`)

---

## Step 1: Verify Current State

```sql
-- Check AI Enabler workspace current scope
SELECT id, name, scope, owner_id, created_at, updated_at
FROM workspaces 
WHERE name = 'AI Enabler Workspace';
```

**Expected Result**: 
- `scope` should currently be `PRIVATE`
- Note the `id` for verification

---

## Step 2: Check Affected Users

```sql
-- Find users who are members of AI Enabler workspace
SELECT 
    u.id,
    u.email,
    u.roles,
    wm.role as workspace_role
FROM users u
JOIN workspace_members wm ON u.id = wm.user_id
JOIN workspaces w ON wm.workspace_id = w.id
WHERE w.name = 'AI Enabler Workspace'
ORDER BY u.email;
```

**Expected Result**: 
- Should show `ashwin.khade01@metro-gsc.in` and other users
- Non-admin users currently cannot see this workspace

---

## Step 3: Apply Migration

```sql
-- Update AI Enabler workspace scope from PRIVATE to GLOBAL
UPDATE workspaces 
SET 
    scope = 'GLOBAL',
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'AI Enabler Workspace';

-- Verify the change
SELECT id, name, scope, owner_id, updated_at
FROM workspaces 
WHERE name = 'AI Enabler Workspace';
```

**Expected Result**:
- `scope` should now be `GLOBAL`
- `updated_at` should be current timestamp
- Should return exactly 1 row updated

---

## Step 4: Verify User Access

```sql
-- Verify users can now access the workspace
-- This query simulates what the backend API returns for a non-admin user

-- For user: ashwin.khade01@metro-gsc.in
SELECT DISTINCT
    w.id,
    w.name,
    w.scope,
    w.owner_id
FROM workspaces w
JOIN workspace_members wm ON w.id = wm.workspace_id
JOIN users u ON wm.user_id = u.id
WHERE u.email = 'ashwin.khade01@metro-gsc.in'
  AND (w.scope = 'PRIVATE' OR w.scope = 'GLOBAL')
ORDER BY w.name;
```

**Expected Result**:
- Should return 2 workspaces:
  1. Personal PRIVATE workspace: `ashwin.khade01@metro-gsc.in`
  2. Group GLOBAL workspace: `AI Enabler Workspace`

---

## Step 5: Verify Group Link

```sql
-- Ensure AI Enabler group still properly linked to workspace
SELECT 
    g.id as group_id,
    g.name as group_name,
    g.shared_workspace_id,
    w.id as workspace_id,
    w.name as workspace_name,
    w.scope
FROM groups g
JOIN workspaces w ON g.shared_workspace_id = w.id
WHERE g.name = 'AI Enabler';
```

**Expected Result**:
- `shared_workspace_id` should match `workspace_id`
- `scope` should be `GLOBAL`
- Link should be intact

---

## Rollback Plan (If Needed)

**Only use if migration causes unexpected issues**

```sql
-- Rollback to PRIVATE scope (NOT RECOMMENDED)
UPDATE workspaces 
SET 
    scope = 'PRIVATE',
    updated_at = CURRENT_TIMESTAMP
WHERE name = 'AI Enabler Workspace';
```

**Note**: Rollback would re-break non-admin user access. Only use if critical issue occurs.

---

## Verification Checklist

- [ ] Connected to database successfully
- [ ] Verified current scope is PRIVATE (Step 1)
- [ ] Identified affected users (Step 2)
- [ ] Applied UPDATE query (Step 3)
- [ ] Confirmed scope is now GLOBAL (Step 3)
- [ ] Verified user access queries work (Step 4)
- [ ] Confirmed group-workspace link intact (Step 5)

---

## Post-Migration Testing

After running migration, test with actual user:

1. **Backend API Test**:
```bash
# Get auth token as test user
TOKEN=$(gcloud auth print-identity-token)

# Test workspace switcher endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://cstudio-backend-dev-viyc62s2ga-ey.a.run.app/api/workspaces/switcher
```

Expected: Array with both workspaces

2. **Frontend Test**:
- User logs in at: https://cf-genaistudi-genai-studio--gv.web.app
- Hard refresh: Cmd+Shift+R
- Should see workspace switcher with both options
- Can select and switch between workspaces
- No "Please select workspace first" error

---

## Impact

**Before Migration**:
- ❌ Non-admin users: Cannot see AI Enabler workspace
- ❌ Workspace switcher shows no options or only personal workspace
- ❌ Users blocked from accessing application

**After Migration**:
- ✅ Non-admin users: Can see AI Enabler workspace
- ✅ Workspace switcher shows personal + group workspaces
- ✅ Users can select workspace and access all features
- ✅ "Please select workspace first" error resolved

---

## Notes

- This migration is **safe** and **reversible** (though rollback not recommended)
- Migration affects only the `AI Enabler Workspace` record
- No data loss - only scope field updated
- User memberships remain intact
- Code changes ensure future groups created with GLOBAL scope

---

**Migration completed**: [DATE/TIME]  
**Executed by**: [YOUR NAME]  
**Verification status**: [ ] PASSED / [ ] FAILED
