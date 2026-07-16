# Database Cleanup - Remove Duplicate Workspaces

**Date**: 2026-07-16  
**Purpose**: Remove duplicate workspace entries caused by lack of idempotency in group creation  
**Context**: Multiple "AI Enabler Workspace" and other group workspaces were created due to missing find-or-create checks

---

## Prerequisites

⚠️ **IMPORTANT**: Run this cleanup AFTER deploying the code fixes (commit with idempotency changes)

- GCP Cloud SQL connection access
- `gcloud` CLI authenticated  
- Database credentials available
- Code fixes deployed (idempotency added to prevent new duplicates)

---

## Connect to Database

```bash
# Connect to Cloud SQL instance
gcloud sql connect creative-studio-db-c40e8b4d \
  --user=studio_user \
  --database=creative_studio \
  --project=cf-genaistudi-genai-studio--gv
```

**Get password from Secret Manager**:
```bash
gcloud secrets versions access latest \
  --secret=creative-studio-db-password \
  --project=cf-genaistudi-genai-studio--gv
```

---

## Step 1: Identify Duplicate Workspaces

```sql
-- Find all duplicate workspace names
SELECT 
    name,
    scope,
    COUNT(*) as duplicate_count,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM workspaces
GROUP BY name, scope
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, name;
```

**Expected Result**: List of workspace names with duplicate counts

**Example Output**:
```
name                    | scope  | duplicate_count | first_created      | last_created
------------------------|--------|-----------------|--------------------|-----------------
AI Enabler Workspace    | GLOBAL | 4               | 2026-07-10 08:00   | 2026-07-16 10:00
Some Other Workspace    | GLOBAL | 2               | 2026-07-12 14:30   | 2026-07-15 16:45
```

---

## Step 2: Analyze Each Duplicate Set

For each duplicate workspace, check details:

```sql
-- Get detailed info for a specific duplicate workspace
SELECT 
    w.id,
    w.name,
    w.scope,
    w.owner_id,
    w.created_at,
    w.updated_at,
    u.email as owner_email,
    COUNT(wm.user_id) as member_count,
    g.id as linked_group_id,
    g.name as linked_group_name
FROM workspaces w
LEFT JOIN users u ON w.owner_id = u.id
LEFT JOIN workspace_members wm ON w.id = wm.workspace_id
LEFT JOIN groups g ON w.id = g.shared_workspace_id
WHERE w.name = 'AI Enabler Workspace'  -- Replace with actual workspace name
GROUP BY w.id, w.name, w.scope, w.owner_id, w.created_at, w.updated_at, u.email, g.id, g.name
ORDER BY w.created_at;
```

**Analysis Criteria** (to decide which workspace to keep):
1. **Oldest creation date** (most likely the "real" one)
2. **Most members** (most used)
3. **Linked to a group** (has `linked_group_id`)
4. **Most recent activity** (if applicable)

---

## Step 3: Design Cleanup Strategy

For each duplicate set, identify:
- **Workspace to KEEP**: Usually the oldest OR the one with most members
- **Workspaces to DELETE**: All others

### Example Analysis for "AI Enabler Workspace"

```sql
-- Example: Find which AI Enabler Workspace to keep
SELECT 
    w.id,
    w.created_at,
    COUNT(wm.user_id) as members,
    CASE 
        WHEN g.shared_workspace_id IS NOT NULL THEN 'YES'
        ELSE 'NO'
    END as has_group_link
FROM workspaces w
LEFT JOIN workspace_members wm ON w.id = wm.workspace_id
LEFT JOIN groups g ON w.id = g.shared_workspace_id
WHERE w.name = 'AI Enabler Workspace'
GROUP BY w.id, w.created_at, g.shared_workspace_id
ORDER BY w.created_at;
```

**Decision Logic**:
- If one workspace has a group link → KEEP that one
- If multiple have group links → KEEP oldest, migrate others to it
- If none have group links → KEEP oldest, delete others

---

## Step 4: Backup Before Cleanup

⚠️ **CRITICAL**: Always backup before destructive operations

```bash
# Create Cloud SQL backup
gcloud sql backups create \
  --instance=creative-studio-db-c40e8b4d \
  --project=cf-genaistudi-genai-studio--gv \
  --description="Pre-duplicate-cleanup backup $(date +%Y-%m-%d)"
```

**Verify backup created**:
```bash
gcloud sql backups list \
  --instance=creative-studio-db-c40e8b4d \
  --project=cf-genaistudi-genai-studio--gv \
  --limit=3
```

---

## Step 5: Execute Cleanup

### For Each Duplicate Workspace Set:

**Template Cleanup SQL** (customize per workspace):

```sql
-- TEMPLATE: Replace values with actual IDs from your analysis

BEGIN;  -- Start transaction for safety

-- 1. Identify workspaces to delete (EXAMPLE IDs - USE YOUR ACTUAL IDs)
-- workspace_to_keep_id: 42
-- workspace_to_delete_ids: 87, 103, 156

-- 2. Migrate workspace members from duplicates to the kept workspace
INSERT INTO workspace_members (workspace_id, user_id, role, email)
SELECT 
    42 as workspace_id,  -- workspace_to_keep_id
    wm.user_id,
    wm.role,
    wm.email
FROM workspace_members wm
WHERE wm.workspace_id IN (87, 103, 156)  -- workspace_to_delete_ids
ON CONFLICT (workspace_id, user_id) DO NOTHING;  -- Skip if already exists

-- 3. Update group references to point to kept workspace
UPDATE groups
SET shared_workspace_id = 42  -- workspace_to_keep_id
WHERE shared_workspace_id IN (87, 103, 156);  -- workspace_to_delete_ids

-- 4. Delete workspace members associations for duplicates
DELETE FROM workspace_members
WHERE workspace_id IN (87, 103, 156);  -- workspace_to_delete_ids

-- 5. Delete duplicate workspaces
DELETE FROM workspaces
WHERE id IN (87, 103, 156);  -- workspace_to_delete_ids

-- 6. Verify results
SELECT 
    name,
    scope,
    COUNT(*) as count
FROM workspaces
WHERE name = 'AI Enabler Workspace'  -- Replace with actual name
GROUP BY name, scope;

-- Expected: Only 1 row (the kept workspace)

COMMIT;  -- Commit transaction if all looks good
-- ROLLBACK;  -- Use this instead if something looks wrong
```

---

## Step 6: Verify Cleanup

### Check No More Duplicates

```sql
-- Should return empty result (no duplicates)
SELECT 
    name,
    scope,
    COUNT(*) as duplicate_count
FROM workspaces
GROUP BY name, scope
HAVING COUNT(*) > 1;
```

**Expected**: Empty result set (no duplicates)

### Check Groups Have Valid Workspaces

```sql
-- Verify all groups point to valid workspaces
SELECT 
    g.id,
    g.name as group_name,
    g.shared_workspace_id,
    w.id as workspace_id,
    w.name as workspace_name,
    w.scope
FROM groups g
LEFT JOIN workspaces w ON g.shared_workspace_id = w.id
ORDER BY g.name;
```

**Expected**: Every group has a valid `workspace_id` (not NULL)

### Check Workspace Members Are Intact

```sql
-- Verify workspace members are preserved
SELECT 
    w.name as workspace_name,
    COUNT(wm.user_id) as member_count
FROM workspaces w
LEFT JOIN workspace_members wm ON w.id = wm.workspace_id
WHERE w.scope = 'GLOBAL'
GROUP BY w.id, w.name
ORDER BY w.name;
```

**Expected**: All group workspaces have appropriate member counts

---

## Step 7: Test Application

After cleanup, verify application functionality:

1. **Backend API Test**:
```bash
TOKEN=$(gcloud auth print-identity-token)

curl -H "Authorization: Bearer $TOKEN" \
  https://cstudio-backend-dev-viyc62s2ga-ey.a.run.app/api/workspaces/switcher | jq .
```

**Expected**: Array with unique workspaces (no duplicates)

2. **Frontend Test**:
- Login to: https://cf-genaistudi-genai-studio--gv.web.app
- Hard refresh: **Cmd+Shift+R**
- Open workspace switcher dropdown
- **Verify**: Each workspace appears ONCE
- **Verify**: Can switch between workspaces
- **Verify**: All functionality works

3. **User Management Test**:
- Navigate to Users > User Management
- Check workspace list in left sidebar
- **Verify**: No duplicate workspace entries
- **Verify**: Groups still linked to correct workspaces

---

## Example: Complete Cleanup for AI Enabler Workspace

This is a complete example based on typical scenario:

```sql
-- Assume analysis showed:
-- - Workspace ID 42 (created first, has 3 members, linked to group 1)
-- - Workspace ID 87 (created later, has 2 members, no group link)
-- - Workspace ID 103 (created later, has 1 member, no group link)
-- - Workspace ID 156 (created later, has 0 members, no group link)

BEGIN;

-- Migrate members from duplicates to kept workspace (ID 42)
INSERT INTO workspace_members (workspace_id, user_id, role, email)
SELECT 
    42 as workspace_id,
    wm.user_id,
    wm.role,
    wm.email
FROM workspace_members wm
WHERE wm.workspace_id IN (87, 103, 156)
ON CONFLICT (workspace_id, user_id) DO NOTHING;

-- Update any group references (should already be 42, but just in case)
UPDATE groups
SET shared_workspace_id = 42
WHERE shared_workspace_id IN (87, 103, 156);

-- Delete duplicate workspace members
DELETE FROM workspace_members
WHERE workspace_id IN (87, 103, 156);

-- Delete duplicate workspaces
DELETE FROM workspaces
WHERE id IN (87, 103, 156);

-- Verify
SELECT name, scope, COUNT(*) FROM workspaces 
WHERE name = 'AI Enabler Workspace' 
GROUP BY name, scope;
-- Expected: 1 row

COMMIT;
```

---

## Rollback Plan

If issues occur after cleanup:

### Restore from Backup

```bash
# List available backups
gcloud sql backups list \
  --instance=creative-studio-db-c40e8b4d \
  --project=cf-genaistudi-genai-studio--gv

# Restore from backup (CAUTION: This replaces current data)
gcloud sql backups restore BACKUP_ID \
  --backup-instance=creative-studio-db-c40e8b4d \
  --instance=creative-studio-db-c40e8b4d \
  --project=cf-genaistudi-genai-studio--gv
```

⚠️ **Warning**: Restoring from backup will lose ALL changes made after the backup was created

---

## Prevention: Future Duplicate Prevention

### Code Changes Deployed ✅

The following code changes prevent future duplicates:

1. **group_service.py** - `create_group()` method:
   - Now checks if workspace exists using `find_by_name()`
   - Reuses existing workspace if found
   - Creates new only if missing

2. **group_service.py** - `ensure_admin_access_to_ai_enabler()` method:
   - Now checks if "AI Enabler Workspace" exists
   - Reuses existing workspace if found
   - Creates new only if missing

### Verification

After code deployment, test idempotency:

```bash
# Test creating a group multiple times
# Should reuse same workspace, not create duplicates

# Check logs for "Reusing existing workspace" messages
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=cstudio-backend-dev AND \
  textPayload=~'Reusing existing workspace'" \
  --project=cf-genaistudi-genai-studio--gv \
  --limit=10
```

---

## Checklist

### Pre-Cleanup
- [ ] Code fixes deployed (idempotency added)
- [ ] Connected to Cloud SQL
- [ ] Identified all duplicate workspaces
- [ ] Analyzed each duplicate set
- [ ] Decided which workspace to keep per set
- [ ] Created database backup

### During Cleanup
- [ ] Executed cleanup SQL in transaction (BEGIN...COMMIT)
- [ ] Verified results before COMMIT
- [ ] No errors during execution

### Post-Cleanup
- [ ] No more duplicate workspaces in database
- [ ] All groups have valid workspace references
- [ ] Workspace members preserved
- [ ] Backend API returns unique workspaces
- [ ] Frontend UI shows no duplicates
- [ ] All application functionality works
- [ ] Users can switch between workspaces

---

## Summary

**Before Cleanup**:
- ❌ Multiple duplicate "AI Enabler Workspace" entries (4+ duplicates)
- ❌ Workspace switcher shows same workspace multiple times
- ❌ Confusing UX for users

**After Cleanup**:
- ✅ Each workspace appears exactly once
- ✅ Workspace switcher shows unique list
- ✅ All members preserved
- ✅ All groups still functional
- ✅ Future duplicates prevented by code

---

**Cleanup executed**: [DATE/TIME]  
**Executed by**: [YOUR NAME]  
**Workspaces cleaned**: [LIST WORKSPACE NAMES]  
**Status**: [ ] SUCCESS / [ ] PARTIAL / [ ] FAILED  
**Notes**: ___________________________________
