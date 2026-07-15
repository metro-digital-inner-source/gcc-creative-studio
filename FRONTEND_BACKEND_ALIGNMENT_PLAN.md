# Frontend to Backend Alignment Plan

This plan captures the current UI setup and maps required backend parity work so behavior is consistent and secure.

## Current Frontend State

1. Admin and top-level analytics are split and route-protected in the frontend.
2. Admin visibility is owner-restricted in the frontend for:
   - joejoseph.george@metro.digital
   - manish.singh@metro-gsc.in
   - abhishek.acharya@metro-gsc.in
3. Workspace switcher is now private-workspace-first and excludes group-shared workspaces from direct selection.
4. Group gallery remains the shared-content surface.
5. Users management supports direct add-by-email to group.
6. Header avatar fallback is now name-initial (or blank if no usable name).

## Backend Parity Workstreams

## 1. Admin Owner Policy Parity

Goal: enforce owner-only admin surfaces server-side (not frontend-only).

1. Add server-side owner email allowlist configuration in backend config.
2. Add a reusable authorization dependency that requires:
   - role = admin
   - email in configured owner allowlist
3. Apply this owner-admin dependency to admin analytics and admin-management endpoints.
4. Keep existing admin role checks for non-owner admin APIs only if intentionally allowed.

Candidate files:
- backend/src/config/config_service.py
- backend/src/auth/auth_guard.py
- backend/src/admin/admin_controller.py

## 2. Group Usage Analytics Reliability

Goal: resolve current runtime error for group usage analytics endpoints.

1. Fix join chain in group usage repository queries by using explicit ON clauses:
   - Group.id == GroupMember.group_id
   - Group.id == GroupUsageDaily.group_id
2. Ensure date filters do not break outer-join semantics unexpectedly.
3. Add endpoint-level tests for:
   - /api/admin/groups/usage-summary
   - /api/admin/groups/usage-breakdown
4. Validate empty-data behavior returns valid zero/empty payloads.

Candidate files:
- backend/src/groups/repository/group_repository.py
- backend/src/groups/group_service.py
- backend/src/admin/admin_service.py

## 3. Workspace Listing Contract Parity

Goal: align backend workspace API with private-only switcher behavior.

1. Add switcher-focused workspace listing contract (either via query flag or dedicated endpoint) returning only:
   - private workspaces user can access
   - excluding group shared workspaces
2. Keep existing generic list endpoint behavior if needed by other flows.
3. Document and test contract used by frontend workspace switcher.

Candidate files:
- backend/src/workspaces/workspace_controller.py
- backend/src/workspaces/workspace_service.py
- backend/src/workspaces/repository/workspace_repository.py

## 4. Group Gallery Boundary Parity

Goal: keep shared workspace access tied to group gallery flow.

1. Keep group shared workspace IDs discoverable via group membership APIs.
2. Ensure non-group users cannot enumerate/access unrelated group shared workspaces.
3. Validate media restore/share flows still work when switcher excludes shared workspaces.

Candidate files:
- backend/src/groups/group_controller.py
- backend/src/groups/group_service.py
- backend/src/workspaces/workspace_auth_guard.py

## 5. Direct Add User Contract Hardening

Goal: stabilize admin add-by-email behavior and edge cases.

1. Ensure add-by-email endpoint behavior is explicit for:
   - existing active user
   - existing soft-deleted user (restore path)
   - new user creation
   - already member conflict
2. Return stable response schema for frontend refresh and user messaging.
3. Add tests for conflict/error codes and payload shape.

Candidate files:
- backend/src/admin/admin_controller.py
- backend/src/admin/admin_service.py
- backend/src/users/user_service.py
- backend/src/groups/group_service.py

## 6. Brand Guidelines Workspace Scope Validation

Goal: preserve per-workspace brand guidelines under private-workspace-first UX.

1. Confirm create/read/update/delete operations remain scoped by workspace_id.
2. Add tests for multiple private workspaces having independent guidelines.
3. Confirm permissions stay owner/admin aware for workspace-specific guidelines.

Candidate files:
- backend/src/brand_guidelines/brand_guideline_controller.py
- backend/src/brand_guidelines/brand_guideline_service.py
- backend/src/brand_guidelines/repository/brand_guideline_repository.py

## Recommended Delivery Order

1. Group usage analytics reliability fix.
2. Admin owner policy parity.
3. Workspace listing contract parity.
4. Direct add user contract hardening.
5. Brand guidelines workspace-scope validation.

## Verification Checklist

1. Owner email users can access admin and analytics APIs; non-owner admins cannot.
2. Group usage analytics endpoints return 200 with valid payloads.
3. Workspace switcher API contract returns only allowed private workspaces.
4. Group gallery still lists shared group media and restore flow works.
5. Add user by email handles new/existing/duplicate flows with stable response.
6. Different private workspaces can store and retrieve different brand guidelines.
