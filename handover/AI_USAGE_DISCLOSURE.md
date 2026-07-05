# AI Usage Disclosure

This project used AI assistance during both development and runtime. This disclosure is included so hackathon reviewers can clearly see what was human-directed, what was AI-assisted, and what the product itself uses at runtime.

## Development AI: OpenAI Codex

OpenAI Codex in the Codex desktop app was used as an AI pair engineer and founding-engineer assistant.

Codex assisted with:

- Interpreting the Cognee hackathon requirements and judging expectations.
- Reviewing the existing repository direction and identifying product gaps.
- Turning the idea into a clearer care-handoff workflow.
- Designing the backend/frontend architecture.
- Implementing FastAPI routes, JWT demo authentication, role-based access control, and assignment logic.
- Implementing React workspaces for night caregiver, morning lead, supervisor, and demo reviewer.
- Updating the landing page, demo runbook, README, docs, and final handover bundle.
- Running local tests, browser checks, backend health checks, Git commits, and pushes.

The human builder directed the product decisions, challenged weak UX, rejected unclear screens, supplied the Cognee/Gemini credentials locally, and made the key product pivot from a role-tab prototype to authenticated role workspaces.

## Runtime AI: Gemini

Gemini is used by the product as the reasoning layer.

It helps:

- Understand raw caregiver notes.
- Decide what memory needs to be recalled for a handoff.
- Draft a structured handoff from remembered context.
- Answer follow-up questions using retrieved source notes.

Gemini is not treated as the source of truth. The backend verifies that handoff content maps back to stored notes and source IDs.

## Runtime Memory: Cognee

Cognee is used as the persistent memory layer.

The product uses Cognee for the memory lifecycle:

- Remember: store case notes and handoff facts.
- Recall: retrieve relevant memory for morning handoffs and follow-up questions.
- Improve: use supervisor feedback as an improvement signal.
- Forget: remove stale or wrong memory from future recall.

Cognee API keys are held by the backend. The frontend does not receive Cognee keys.

## AI-Assisted Visual Asset

The landing page hero visual was created with AI assistance for the hackathon presentation site.

## Data Disclosure

- No real patient data was used.
- Demo care-recipient names and notes are synthetic.
- The app is not presented as medical advice, diagnosis, treatment guidance, or HIPAA-compliant production software.

## What AI Did Not Do

AI did not provide legal, clinical, or compliance approval.

AI did not replace human product judgment. The human builder made the final decisions on product direction, critique, acceptance, and submission positioning.
