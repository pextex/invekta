# Plan — Permanent LUU × Invekta × Cenobots CRM

## Product outcome and constraints

Turn the existing LUU × Invekta × Cenobots CRM into a permanently hosted, login-protected website. Preserve the existing Serbian-language interface, email-and-password authentication, role-based permissions, three business-unit data boundaries, and database-backed CRM workflows. The owner selected the recommended Manus-hosted path: stable Manus URL, persistent managed MySQL, and Autoscale hosting (idle deployments may sleep and a later visit may cold-start).

The sandbox PostgreSQL instance is development-only and contains synthetic demo data. It is not a production source of truth. Start production with a clean managed database: do not copy the sandbox database, its demo account/password, or synthetic seed records. There are no real customer records to migrate. The first production administrator uses the email supplied by the owner and has access to all three units; provision an inactive profile, then allow exactly one activation only for that database-marked pending profile through the secure input flow. Keep the website unpublished until the owner has reviewed the exact deployment details and confirmed publication.

## Implementation approach

- Reuse the current React 19/Vite frontend and FastAPI/SQLAlchemy/Alembic backend rather than replacing the CRM or changing its product behavior.
- Build the frontend from its committed npm lockfile and serve the resulting static files from the FastAPI container on the same origin as `/api`; keep browser API URLs root-relative. Copy `shared/message_catalog.json` into the Node build stage at `/src/shared` for the frontend import and into the Python runtime image at `/app/shared` for the backend filesystem loader.
- Use the Manus-provided managed MySQL database through runtime `DATABASE_URL`, with a MySQL-compatible SQLAlchemy driver. Convert the existing PostgreSQL-specific business-unit registration migration to a portable, idempotent migration while retaining PostgreSQL support where needed by the existing local test suite. Serialize startup migrations with a database advisory lock so overlapping Autoscale instances cannot race; run additive schema migrations before serving the application. Persist a `bootstrap_pending` marker so the first-admin password can be installed once only on its pre-provisioned account. Do not run the development seed in production.
- Preserve password hashing, session storage, email/password login, membership checks, and role checks. Use `SameSite=None; Secure` for HTTPS Preview/published requests, with a separate secure-cookie setting for plain-HTTP local development. Validate mutating requests against the exact configured Origin allowlist; where the platform-assigned public host is not known before first publish, accept only a syntactically valid explicit Origin paired with browser `Sec-Fetch-Site: same-origin` (never `same-site`). Never derive the public origin from the internal container Host.
- Serve the compiled frontend and API from one container listening on `0.0.0.0:$PORT` (default 3000). Provide an unauthenticated database readiness endpoint for deployment health checks. Keep runtime state in MySQL, not the container filesystem.
- Maintain the hash-based CRM navigation and declare the actual browser page surface in `frontend/public/manus-routes.json` before the first Preview server start.
- Set the WebDev project logo from the existing Invekta logo asset using a durable HTTPS asset URL, without altering the in-app organization logos.
- Use the Manus-managed project repository as the website checkpoint source. Do not switch the canonical repository to GitHub or push to the user's public GitHub repository as part of this task.

## Project structure

- `frontend/src/`: Existing React screens, CRM workflows, organization portal, authentication client, and shared visual system.
- `frontend/public/`: Static route manifest required by WebDev; Vite copies it into the production bundle.
- `backend/app/`: FastAPI application and API routers, SQLAlchemy models/schemas, authentication/session and access-control logic, plus static-file serving for the production frontend.
- `backend/alembic/`: Ordered application schema migrations, made compatible with the managed MySQL dialect.
- `backend/tests/`: Existing PostgreSQL-focused API, authorization, migration, and workflow tests; run relevant checks without connecting them to the shared production database.
- `Dockerfile`: Multi-stage Node/Python production build, frontend compilation, backend dependencies, migration/startup command, and port 3000 listener.
- `plan.md` and `TODO.md`: Implementation decisions and outcome criteria.

## Design system to preserve

- **Design Movement:** Restrained, utilitarian B2B SaaS/CRM interface grounded in the supplied LUU/Invekta prototype; this is a continuity pass, not a visual redesign.
- **Core Principles:** Clear sales-information hierarchy; readable data tables and forms; recognizable business-unit context; visible feedback for saved, pending, and failed actions.
- **Color Philosophy:** Midnight navy `#10243c` anchors navigation and conveys operational trust; bright blue `#2868e8` marks primary actions; turquoise accents highlight progress; pale blue-gray `#f3f6fb` keeps dense CRM screens calm. Existing per-company marks remain intact.
- **Layout Paradigm:** Persistent left navigation with a sticky, light header and a broad working canvas; dashboard cards and sales-pipeline columns follow the existing information architecture.
- **Signature Elements:** The LUU × Invekta × Cenobots logo cluster; navy navigation with blue active states; the blue-to-turquoise progress treatment already used in the pipeline/dashboard.
- **Interaction Philosophy:** Direct, predictable CRUD interactions with explicit save/error feedback; pipeline moves persist through the API; server-side permissions remain authoritative and business-unit boundaries are never implied by styling alone.
- **Animation:** Keep only brief existing hover, focus, and state transitions; avoid decorative motion that competes with operational data or delays form actions.
- **Typography System:** Preserve the current `Inter`, then `Segoe UI`, then Arial/sans-serif stack; keep current compact body sizing and existing heading/table hierarchy.
- **Brand Essence:** One authenticated sales workspace for three distinct businesses, with unit-scoped data and a shared operating interface. Personality: clear, dependable, practical.
- **Brand Voice:** Keep the current concise Serbian CRM copy. Example headline: “Kompanije i kontakti”; example action: “Dodaj kompaniju”.
- **Wordmark & Logo:** Retain the existing three-company wordmark/mark treatment and their supplied PNG marks; do not invent a replacement identity.
- **Signature Brand Color:** Midnight navy `#10243c`.
