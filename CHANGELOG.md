# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — feature/dynamic-allowlist — 2026-06-21

### Added

#### Backend — Dynamic Allowlist (`962ae23`)
- New `allowlist` module with model, repository, service, and controller layers.
- `AllowlistEntry` database table with email and domain matching support.
- Admin-only API endpoints at `/api/admin/allowlist`:
  - `POST /api/admin/allowlist` — Add an email or domain to the allowlist.
  - `GET /api/admin/allowlist` — List all entries (supports `active_only` filter).
  - `GET /api/admin/allowlist/{entry_id}` — Get a specific entry.
  - `PUT /api/admin/allowlist/{entry_id}` — Update entry (toggle active/notes).
  - `DELETE /api/admin/allowlist/{entry_id}` — Soft-deactivate an entry.
  - `POST /api/admin/allowlist/cache/clear` — Force-clear the in-memory cache.
- In-memory caching layer (60s TTL) for allowlist lookups to reduce DB load.
- Database migration: `add_allowlist_001_create_table.py`.
- Auth guard updated to use DB-backed allowlist with env var fallback:
  - Priority order: 1) DB allowlist → 2) `ALLOWED_EMAILS` env var → 3) `ALLOWED_ORGS` env var.
  - Fully backward-compatible with existing environment-based config.
- Allowlist router registered in `main.py`.

#### Frontend — Feature Switches (`c553cf0`)
- Environment feature flags `ENABLE_VTO` and `ENABLE_FUN_TEMPLATES` added to `environment.ts` and `environment.prod.ts`.
- `/vto` and `/fun-templates` routes are conditionally registered based on feature flags; when disabled, they redirect to home.
- VTO and Fun Templates entries removed from the header tools menu when their respective flag is `false`.
- VTO action button hidden in the shared media lightbox when `ENABLE_VTO` is `false`.
- Navigation handlers in `HomeComponent` and `MediaDetailComponent` guard against VTO calls when the feature is off.
- Admin media template management is unaffected by these flags.

#### Documentation
- `README.md` — Added **Cloud Build Config Clarification** section documenting the canonical build config file for frontend deployments and the recommended manual trigger command for feature branches.

### Fixed

#### Allowlist Enforcement Hardening (`2026-06-22`)
- **DB-only enforcement:** Auth guard now properly enforces DB-backed allowlist access control even when `ALLOWED_EMAILS` and `IDENTITY_PLATFORM_ALLOWED_ORGS` env vars are empty.
- **Fail-closed behavior:** When DB allowlist checks fail and no env-var fallback is configured, auth now returns `503 Service Unavailable` instead of silently allowing access.
- **Case-insensitive matching:** Email and domain comparisons are now normalized to lowercase for consistency across both DB and env-var restrictions.
- **Active-entry detection:** New `has_active_entries()` method in `AllowlistService` and `AllowlistRepository` enables runtime detection of whether DB-backed access control is active.
- **Comprehensive test coverage:** Added 6 new test cases for auth guard behavior:
  - DB-only allowlist rejection and approval
  - Env-var fallback email matching
  - Case-insensitive email matching across env and DB sources
  - Fail-closed (503) behavior when DB authorization cannot be evaluated
  - Config reset between test cases to prevent order-dependent leakage

#### Login Regression — Auth Flow Recovery (`2026-06-21`)
- Backend auth guard now injects `AllowlistService` through FastAPI dependency injection instead of instantiating it with `Depends()` manually.
- Frontend auth interceptor now avoids forcing a logout for pre-login/background requests, preventing the sign-in flow from being torn down while the user is authenticating.
- This restores the previous develop branch behavior where unauthenticated startup requests no longer break login with `User session is not valid or has expired. 2`.

#### Frontend — Route Typing (`70ebbef`)
- TypeScript compile error in `app-routing.module.ts`: `pathMatch` on redirect routes now uses `'full' as const` to satisfy Angular's strict `'full' | 'prefix' | undefined` type.

#### Frontend — Auth Session (`1fdf5db`)
- Session state is now cleared on login or backend sync failure, preventing stale token states that made the app appear logged in without a real user profile.
- `getValidIdentityPlatformToken$()` now throws an error immediately when no valid session exists, instead of returning an empty observable that caused requests to proceed with an undefined Bearer token.
- `logout()` now calls `google.accounts.id.disableAutoSelect()` to prevent Google One Tap from auto-signing in the previous account after an explicit logout.
- Session cleanup logic consolidated into a single `clearSessionState()` private method.

---

## v0.1.0 — 2025-05-08

### Added

- Initial release of Creative Studio platform.
