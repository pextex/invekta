# CRM phases 1–2 implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the approved phases 1–2: repeatable checks and one authorized PostgreSQL metrics/state flow across pipeline, dashboard, reports and profiles.
**Architecture:** Extend existing FastAPI routers with one scoped metrics service; React Query provides shared server state and unit-wide invalidation after mutations. Existing stage history, cookie sessions, version checks and visual components remain.
**Tech Stack:** React/TypeScript/Vite, TanStack Query, FastAPI/SQLAlchemy/PostgreSQL, pytest/Vitest/Playwright, ESLint/Ruff, GitHub Actions.
**Spec:** User approval attachment (14 October 2026), `docs/CRM_AUDIT.md`, `docs/DATABASE_DESIGN.md`.

## Global constraints

- Work on `feat/crm-metrics-sync`; open a PR, never merge/deploy.
- Preserve business database, session/auth contracts and seven stage labels.
- No paid services; no tasks/reminders/quotes implementation before next approval.
- No migration required for metrics: reuse existing created_at, stage history and Decimal amounts.
- Native inline execution is used to follow the explicit instruction to begin phases 1–2 immediately.

## Metric decisions

Date filters select an opportunity creation cohort, inclusive local dates in Europe/Belgrade. Current phase/value metrics describe that cohort's current state, not historical snapshots or invoiced revenue. Company/contact counts include all currently visible records for the owner filter and are explicitly labeled as totals independent of opportunity dates. Stage transitions are distinct opportunities with an observed direct from→to event during the selected period; conversion denominator is distinct opportunities observed in the source phase in that period. Missing legacy history is not reconstructed. Monthly timeline counts observed phase events, not historic amounts. Owner = company owner, not modifying actor. Default filters include all dates. Unit is selected only from enabled memberships, on analytics filter controls, without restoring a CRM-switching menu.

## Review focus

- Missing history: never fabricate conversions/historical values.
- Sales owner filter: must not broaden own-company scope.
- Stale requests and cache after logout/unit change: must not show previous user's data.
- Concurrent 409: retain user's unsaved edit, refresh current server view.
- Records beyond first 100 pipeline cards: aggregates must use full scoped SQL dataset.

### Task 1: Repeatable checks

**Files:** `.github/workflows/ci.yml`, `frontend/eslint.config.js`, frontend package lock, backend pyproject/uv lock, isolation tests.
**Interfaces:** Existing `app.test_runner`, `npm test/build`; produce `npm run lint`, `uv run ruff check .`.
- [x] Add regression checks for ownership and session persistence on isolated test DB, run current baseline.
- [x] Configure ESLint and Ruff without broad formatting or unrelated source refactors.
- [x] CI starts fresh PG16, installs locked dependencies, runs lint/build/all tests.
- [x] Verify commands and commit phase 1.

### Task 2: Shared backend metrics

**Files:** `backend/app/metrics.py`, `api/sales.py`, `schemas.py`, `tests/test_metrics.py`.
**Interfaces:** `GET /units/{unit}/summary` extended, same filters on opportunities: start_date/end_date/owner_id; summary keeps legacy fields and adds lost_count, stage_values, owners, sales_results, company_results, transitions, timeline.
- [x] Write failing tests: won/lost/value updates, filter boundaries, invalid ranges, inaccessible owners/units, exact Decimal totals, legacy missing history, stale mutation, persistence through logout/relogin.
- [x] Observe failures; implement central scope/filter/SQL aggregate functions and route integration.
- [x] Run all backend tests, schema drift check; commit.

### Task 3: Shared frontend state and analytics

**Files:** `frontend/src/lib/crmQuery.tsx`, `features/crm/{Dashboard,Reports,MetricsFilters,Pipeline,CompanyProfile,Contacts,types}`, `Workspace.tsx`, `main.tsx`.
**Interfaces:** query keys `[crm,unit,path]`, shared request/mutation API invalidates all related unit queries after success or 409; cache cleared on auth boundary; shared metrics filter model.
- [x] Write failing cache tests for mutation propagation and session clear.
- [x] Adopt shared query client in existing components; refetch on mount/focus and 30-second active polling for other-user changes.
- [x] Render dashboard KPIs and real reports using same summary payload; filter by allowed unit/date/owner. Pipeline uses same date/owner filters; profile remains complete company context.
- [x] Preserve errors/409, existing drag/drop and form UX; invalidate after companies/contacts/opportunities writes.
- [x] Run lint/build/frontend suite; commit.

### Task 4: End-to-end proof and handoff

**Files:** `frontend/e2e/crm.spec.ts`, Playwright config, isolated backend test-server utility, `docs/PHASE_1_2_VALIDATION.md`, CI E2E step.
**Interfaces:** Dedicated disposable `_test` database, dedicated ports, seeded synthetic three-unit users only; never business DB.
- [x] Exercise sales login, drag/drop and select to same endpoint, KPI/reports/profile, browser reload/logout/relogin, manager results, foreign-unit denial, amount edit and 409.
- [x] Run full checks; fresh final review and address significant issues.
- [x] Document exact files/results/metric rules and manual scenario; push branch. PR creation attempted with body file and REST payload, blocked by GitHub API Forbidden; prepared creation link and body are in validation document.

## Execution record

- Phase 1: existing baseline 45 backend/5 frontend passed; ESLint and Ruff found unused imports. Existing provider-test override compatibility was retained with an explicit import annotation; no behavior change to templates.
- Backend RED: seven metric/filter tests failed on absent fields, ignored filters and missing history aggregates. GREEN: shared service passed all tests. Added full-dataset regression beyond 100 cards; final backend 53 passed.
- Frontend RED: shared mutation helper absent; GREEN: invalidation/409/denial checks passed. Browser checks proved actual PostgreSQL persistence and UI flows.
- Review: fresh read-only reviewer found no Critical/Important defect, raised two details subsequently treated as necessary reliability fixes. Cached revoked owner names reproduced RED→GREEN (SSR actual components); separately running new-record browser scenario reproduced order dependence and passed after per-test server/database isolation.
- Final checks: 9 Vitest, 3 Playwright, 53 pytest; ESLint/Ruff/build passed, Alembic check no drift. Known large bundle and Starlette deprecation remain as prior audit limitations.
- Ruling: honor the explicit instruction to begin approved phases immediately and execute inline on requested feature branch; no second permission round or new app/worktree was needed. If the chosen current-state date cohort is not the business period desired, only metric filtering semantics need a reviewed follow-up; historical amounts cannot be invented from stage-only history.
- Remote branch pushed. GraphQL and REST PR creation both blocked by API Forbidden; no merge/deployment. Phase 3+ awaits user review as requested.
