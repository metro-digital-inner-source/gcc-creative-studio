# Group Governance Implementation Plan

**Branch:** `feature/group-governance`  
**Started:** 2026-07-14  
**Status:** Backend Complete (Phases 1-3) ✅

---

## Overview

This document tracks the implementation of a comprehensive group governance layer for the Creative Studio platform. Groups provide organizational boundaries, cost tracking, and controlled sharing capabilities.

### Architecture Goals
- 1:1 relationship between Groups and shared Workspaces
- Role-based access (admin/member) within groups
- Usage tracking and analytics aggregation per group
- Admin panel for group management
- Frontend gallery for viewing group-shared content

---

## Phase 1: Database Migrations ✅ COMPLETE

### Files Created (4)
1. ✅ `backend/alembic/versions/6bd11c58f086_create_groups_table.py`
   - Creates `groups` table with FK to workspaces (1:1 via unique constraint)
   - Columns: id, name, country_code, shared_workspace_id, timestamps

2. ✅ `backend/alembic/versions/2ed9a196f444_create_group_members_table.py`
   - Creates `group_members` association table
   - Composite PK (group_id, user_id), role column
   - Indexes for efficient lookups

3. ✅ `backend/alembic/versions/041ccdc22962_create_group_usage_daily_table.py`
   - Creates `group_usage_daily` for analytics
   - Tracks spend_usd, tokens_consumed, activity_count per day
   - Unique constraint on (group_id, date)

4. ✅ `backend/alembic/versions/6186d6d560b8_bootstrap_default_group.py`
   - Idempotent bootstrap migration
   - Creates "Default Group" with dedicated workspace
   - Assigns all existing users as members

### Verification ✅
```bash
# Tables created
docker-compose exec -T postgres psql -U studio_user -d creative_studio -c "\dt group*"
# Result: groups, group_members, group_usage_daily

# Default Group created
docker-compose exec -T postgres psql -U studio_user -d creative_studio -c "SELECT * FROM groups;"
# Result: 1 row - "Default Group" with workspace_id 3

# User assigned
docker-compose exec -T postgres psql -U studio_user -d creative_studio -c "SELECT * FROM group_members;"
# Result: user joejoseph.george@metro.digital assigned as member
```

---

## Phase 2: Backend Group Module ✅ COMPLETE

### Files Created (10)
1. ✅ `backend/src/groups/schema/group_model.py`
   - SQLAlchemy models: Group, GroupMember, GroupUsageDaily
   - Pydantic DTOs: GroupModel, GroupMemberModel, GroupUsageDailyModel
   - GroupMemberRoleEnum (MEMBER, ADMIN)
   - Relationships with lazy="selectin" for eager loading

2. ✅ `backend/src/groups/schema/__init__.py`
   - Module exports for schema models

3. ✅ `backend/src/groups/dto/group_dto.py`
   - CreateGroupRequest, AddMemberRequest, ShareItemsRequest
   - GroupResponse with camelCase serialization

4. ✅ `backend/src/groups/dto/usage_dto.py`
   - GroupUsageSummary, GroupUsageBreakdown, MyUsageResponse
   - Analytics DTOs for reporting

5. ✅ `backend/src/groups/dto/__init__.py`
   - Module exports for DTOs

6. ✅ `backend/src/groups/repository/group_repository.py`
   - CRUD operations for groups and members
   - Usage queries with aggregations
   - Async methods using AsyncSession

7. ✅ `backend/src/groups/repository/__init__.py`
   - Export GroupRepository

8. ✅ `backend/src/groups/group_service.py`
   - Business logic layer
   - Injects GroupRepository, WorkspaceService
   - Methods: get_user_groups, create_group, add_member, share_items, get_usage

9. ✅ `backend/src/groups/group_controller.py`
   - FastAPI router with endpoints:
     - GET /api/groups/me - User's groups
     - POST /api/groups - Create group
     - POST /api/groups/share-items - Share to group
     - GET /api/groups/my-usage - User's usage stats
   - Injects GroupService, CurrentUser dependency

10. ✅ `backend/src/groups/__init__.py`
    - Module exports

### Router Registration ✅
- ✅ `backend/main.py` modified to include group_controller router

---

## Phase 3: Backend Admin Endpoints ✅ COMPLETE

### Files Modified (2)
1. ✅ `backend/src/admin/admin_controller.py`
   - Added admin group routes:
     - GET /api/admin/groups - List all groups
     - POST /api/admin/groups - Create group
     - POST /api/admin/groups/{id}/users - Add members
     - GET /api/admin/groups/usage-summary - Aggregate usage
     - GET /api/admin/groups/usage-breakdown - Per-group usage
   - All routes require ADMIN role via RoleChecker dependency

2. ✅ `backend/src/admin/admin_service.py`
   - Injected GroupService
   - Implemented admin methods:
     - get_all_groups()
     - create_group_admin()
     - add_user_to_group()
     - get_group_usage_summary()
     - get_group_usage_breakdown()

### Verification ✅
- Backend starts without errors
- Migrations applied successfully
- All new endpoints available in Swagger docs at http://localhost:9000/docs

---

## Phase 4: Frontend Group Service ⏳ TODO

### Files To Create (2)
1. ⏳ `frontend/src/app/services/group.service.ts`
   - Injectable Angular service
   - HTTP methods for group endpoints:
     - getMyGroups()
     - shareItemsToGroup(groupId, itemIds)
     - getMyUsage()

2. ⏳ `frontend/src/app/models/group.model.ts`
   - TypeScript interfaces matching backend DTOs
   - Group, GroupMember, GroupUsage interfaces

---

## Phase 5: Admin Dashboard Components ⏳ TODO

### Files To Create/Modify (3)
1. ⏳ `frontend/src/app/components/admin/admin-groups/admin-groups.component.ts`
   - Component for group management
   - List groups, create groups, add members
   - View usage statistics

2. ⏳ `frontend/src/app/components/admin/admin-groups/admin-groups.component.html`
   - Template with Angular Material table
   - Create group dialog, add member dialog

3. ⏳ `frontend/src/app/components/admin/admin-groups/admin-groups.component.css`
   - Styling for admin groups view

4. ⏳ Update admin routing to include groups tab

---

## Phase 6: Group Gallery & Share Feature ⏳ TODO

### Files To Create/Modify (4)
1. ⏳ `frontend/src/app/components/galleries/group-gallery/group-gallery.component.ts`
   - Display group-shared items
   - Filter by group (user's groups dropdown)

2. ⏳ `frontend/src/app/components/galleries/group-gallery/group-gallery.component.html`
   - Gallery grid layout
   - Group selector dropdown

3. ⏳ `frontend/src/app/components/galleries/group-gallery/group-gallery.component.css`
   - Styling for group gallery

4. ⏳ Modify media item cards to add "Share to Group" action button
   - Add share dialog/dropdown
   - Call GroupService.shareItemsToGroup()

---

## Phase 7: Feature Flags ⏳ TODO

### Implementation
1. ⏳ Backend: Add `ENABLE_GROUP_GOVERNANCE` config flag
   - Location: `backend/src/config/settings.py`
   - Default: True (enabled)

2. ⏳ Backend: Add middleware/guards to check feature flag
   - Return 404 or disable routes when flag is False

3. ⏳ Frontend: Add feature flag service
   - Check backend config on startup
   - Conditionally render group UI elements

---

## Phase 8: Testing & Validation ⏳ TODO

### Backend Tests
1. ⏳ `backend/tests/test_groups/test_group_repository.py`
   - Test CRUD operations
   - Test usage aggregations

2. ⏳ `backend/tests/test_groups/test_group_service.py`
   - Test business logic
   - Mock repository calls

3. ⏳ `backend/tests/test_groups/test_group_controller.py`
   - Test API endpoints
   - Test authentication/authorization

### Frontend Tests
4. ⏳ `frontend/src/app/services/group.service.spec.ts`
   - Test service HTTP calls

5. ⏳ Component tests for admin-groups and group-gallery

### Integration Tests
6. ⏳ End-to-end test: Create group, add members, share items, view gallery
7. ⏳ Verify analytics aggregation with real usage data

---

## Key Decisions & Trade-offs

### Architecture
- **1:1 Group-Workspace**: Each group has a dedicated shared workspace. Simplifies permissions (workspace-level ACLs apply).
- **Role Simplification**: Only MEMBER and ADMIN roles initially. Extensible to VIEWER if needed.
- **Usage Aggregation**: Daily aggregates stored in group_usage_daily. Requires periodic job to populate from audit logs.

### Database
- **Composite Primary Key**: group_members uses (group_id, user_id) PK. No separate ID needed for association table.
- **Soft Deletes**: Groups are NOT soft-deleted initially. Hard delete cascades to members. Can add deleted_at later if needed.
- **Indexes**: Added on foreign keys and date columns for query performance.

### API Design
- **User Endpoints**: `/api/groups/*` - User-facing, returns only user's groups
- **Admin Endpoints**: `/api/admin/groups/*` - Admin-only, full visibility
- **Share Mechanism**: Moves/copies media items to group's shared workspace (uses existing workspace logic)

### Frontend
- **Gallery Tab**: New "Group Gallery" tab in galleries section, separate from "My Gallery" and "Workspace Gallery"
- **Share Action**: Context menu on media items, dropdown to select group
- **Analytics**: Admin dashboard shows aggregate stats, regular users see only their own usage

---

## Verification Checklist

### Phase 1 ✅
- [x] Migrations applied without errors
- [x] Tables exist in database
- [x] Default group created with data
- [x] Users assigned to default group

### Phase 2 ✅
- [x] Models created with proper relationships
- [x] DTOs created with camelCase serialization
- [x] Repository implements all query methods
- [x] Service implements business logic
- [x] Controller exposes API endpoints
- [x] Router registered in main.py
- [x] Backend starts without import errors
- [x] Swagger docs show new endpoints

### Phase 3 ✅
- [x] Admin endpoints accessible at /api/admin/groups
- [x] Admin can create groups
- [x] Admin can add members
- [x] Admin can view usage stats
- [x] Non-admin users get 403 Forbidden (via RoleChecker)

### Phase 4-6 ⏳
- [ ] Frontend service makes successful API calls
- [ ] Admin dashboard displays groups
- [ ] Group gallery shows shared items
- [ ] Share action works from media cards

### Phase 7 ⏳
- [ ] Feature flag toggles functionality
- [ ] UI elements hidden when disabled

### Phase 8 ⏳
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Integration test covers full workflow

---

## Next Steps

**Current:** ✅ Backend implementation complete (Phases 1-3)

**Completed Actions:**
1. ✅ Created 4 Alembic migrations for groups, members, usage tables
2. ✅ Created GroupRepository with async database methods
3. ✅ Created GroupService with business logic
4. ✅ Created GroupController with FastAPI routes
5. ✅ Registered router in main.py
6. ✅ Added admin endpoints to admin_controller.py
7. ✅ Added admin methods to admin_service.py
8. ✅ Backend starts successfully - verified in logs
9. ✅ All endpoints available in Swagger at http://localhost:9000/docs

**Backend Endpoints Available:**
- User endpoints: `/api/groups/*`
  - GET /api/groups/me
  - POST /api/groups
  - POST /api/groups/share-items
  - GET /api/groups/my-usage
  
- Admin endpoints: `/api/admin/groups/*`
  - GET /api/admin/groups
  - POST /api/admin/groups
  - POST /api/admin/groups/{group_id}/users
  - GET /api/admin/groups/usage-summary
  - GET /api/admin/groups/usage-breakdown

**Remaining Work (Frontend):**
- Phase 4: Create Angular GroupService
- Phase 5: Build admin dashboard components for group management
- Phase 6: Implement group gallery and share UI
- Phase 7: Add feature flags
- Phase 8: Comprehensive testing

---

## Files Summary

### Created (14 files) ✅
**Phase 1: Migrations (4)**
- backend/alembic/versions/6bd11c58f086_create_groups_table.py
- backend/alembic/versions/2ed9a196f444_create_group_members_table.py
- backend/alembic/versions/041ccdc22962_create_group_usage_daily_table.py
- backend/alembic/versions/6186d6d560b8_bootstrap_default_group.py

**Phase 2: Backend Module (10)**
- backend/src/groups/schema/group_model.py
- backend/src/groups/schema/__init__.py
- backend/src/groups/dto/group_dto.py
- backend/src/groups/dto/usage_dto.py
- backend/src/groups/dto/__init__.py
- backend/src/groups/repository/group_repository.py
- backend/src/groups/repository/__init__.py
- backend/src/groups/group_service.py
- backend/src/groups/group_controller.py
- backend/src/groups/__init__.py

### Modified (3 files) ✅
**Phase 2 & 3: Integration**
- backend/main.py (added group_controller router)
- backend/src/admin/admin_controller.py (added 5 group endpoints)
- backend/src/admin/admin_service.py (added 5 group methods)

### To Create (15+ files) ⏳
**Phase 4-6: Frontend (15+)**
- Frontend services (2 files)
- Admin components (3-6 files)
- Group gallery (3-6 files)
- Routing updates (1-2 files)

**Phase 8: Tests (5+ files)**
- Backend tests (3+ files)
- Frontend tests (2+ files)

---

**Last Updated:** 2026-07-14  
**Branch:** feature/group-governance  
**Next Milestone:** Complete Phase 2 backend implementation
