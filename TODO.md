# TODO — Permanent CRM website

## Production hosting and release gate
- [ ] Turn the existing LUU × Invekta × Cenobots CRM into a permanently hosted website at the stable Manus-hosted URL, using Autoscale hosting. Idle deployments may sleep, so the first later visit can experience a cold start. Keep CRM records behind login. Do not publish until the owner reviews the exact deployment details and explicitly confirms publication.

## Persistent database and clean production state
- [x] Use the persistent Manus-managed MySQL database for CRM data, adapting the current PostgreSQL-based SQLAlchemy application and migrations as needed. Do not copy the sandbox development database, its demo password, its demo user, or its synthetic seed records into production. No real customer-record migration is required.

## Login, permissions, and first administrator
- [x] Preserve email-and-password CRM login, existing user roles, authorization checks, and separate data boundaries for LUU, Invekta, and Cenobots. Securely create the first production administrator for the email supplied by the owner; this administrator must have access across all three business units. Provision an inactive profile, then allow exactly one password activation only for that pre-existing database-marked pending profile. Set the password only through the secure setup flow, never in chat or a committed file; reject repeat activation/password resets and bootstrap of a second platform administrator.

## Existing CRM workflows and interface
- [x] Preserve the current frontend and database-backed workflows for companies, contacts, opportunities/sales pipeline, reports, and authorized user management. Keep the current business-unit separation and Serbian-language interface; do not substitute a demo-only frontend for the real authenticated CRM.
