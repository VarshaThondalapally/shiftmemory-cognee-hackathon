# Phase 1 and Phase 2 Build Plan

## Phase 1: Local Product MVP

Goal: make the caregiver handoff use case work as a real local app, not a static demo.

Phase 1 uses a local memory adapter that mirrors Cognee's lifecycle. This lets us test the product flow immediately without waiting for Cloud keys.

Deliverables:

- FastAPI backend with memory lifecycle endpoints.
- React frontend for the actual caregiver handoff workflow.
- Synthetic demo case data.
- Local persisted memory in JSON.
- Handoff generation from remembered notes.
- Q&A over case memory.
- Feedback that marks memory high-signal.
- Forget action that removes memory from future handoffs.
- Judge proof view that proves each lifecycle operation.

Acceptance checks:

- Add note, refresh app, note still appears.
- Generate handoff from remembered notes.
- Ask a question and receive source-backed answer.
- Mark a note important and see it prioritized.
- Forget a note and confirm it disappears from handoff.
- View proof screen showing remember, recall, improve, forget.

## Phase 2: Cognee-Backed MVP

Goal: replace local memory with Cognee Cloud while keeping the same product UX.

Deliverables:

- Cognee Cloud credentials stored in backend-only `.env`.
- `CogneeMemoryService` implementation backed by Cognee Cloud HTTP APIs.
- `remember` calls for notes, files, confirmed handoffs, and supervisor signals.
- `recall` calls for handoff generation and Q&A.
- `improve` calls from feedback and marked-important actions.
- `forget` calls for deletion and retention.
- Judge trace showing Cognee operation IDs, source IDs, and latency.
- Optional LLM provider for more natural handoff writing.

Acceptance checks:

- Browser never receives Cognee API key.
- Case memory persists across backend restart.
- Cognee trace confirms remember, recall, improve, forget.
- Deleted memory no longer appears in recall.
- Case A cannot recall Case B memory.
- Handoff output cites source IDs.

## Cognee Balance Policy

Use Cognee balance for actions that prove memory:

- add note;
- reset demo seed data before a judge run;
- generate handoff;
- ask case question;
- mark important;
- remove wrong note.

Do not spend Cognee balance on:

- page refresh;
- switching tabs;
- selecting a case;
- polling proof data;
- repeated fake seed spam.

For the hackathon demo, use two synthetic cases and roughly 8-12 notes total. That is enough to prove persistent memory, case isolation, improvement, and forgetting.

## Current Boundary

Phase 1 is complete enough to prove the product workflow locally. Phase 2 is activated by setting `MEMORY_BACKEND=cognee`, `COGNEE_BASE_URL`, and `COGNEE_API_KEY`; that is the final hackathon proof path.
