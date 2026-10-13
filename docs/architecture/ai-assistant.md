# AI draft assistant

Implemented in app/api/ai.py, app/ai_provider.py and AiAssistant.tsx. Migration a162bced9031 adds private drafts and per-user generation budget. No email sending capability, background tasks or mailbox access. User instructions and selected CRM context are transmitted only on explicit generation. Incoming email and opportunity notes are identified as untrusted data in system instructions. The model receives no tools and cannot operate the CRM. Output is validated as subject/body before storage.

Authorization uses active sessions, enabled memberships and company ownership for sales users. List/edit constrain author, unit and current company visibility. A session/access recheck after provider completion prevents saving after revocation. The user row lock serializes generation-budget reservations; HTTP generation runs after releasing that lock. Output versions protect manual edits. There is no claim of prompt-injection immunity or factual correctness.

Validation: 41 PostgreSQL backend tests and two existing frontend tests passed; build passed. Provider protocol tests use mocked transport; they do not establish live OpenAI connectivity. Browser checks exercise the real missing-key state and a simulated provider for generated/editable drafts. Original API key is absent, so actual model output remains unverified pending configuration.
