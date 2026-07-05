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

## Phase 2: Cognee and Gemini MVP

Goal: replace local memory and local handoff writing with Cognee Cloud plus Gemini while keeping the same product UX.

Deliverables:

- Cognee Cloud credentials stored in backend-only `.env`.
- `CogneeMemoryService` implementation backed by Cognee Cloud HTTP APIs.
- `remember` calls for notes, files, confirmed handoffs, and supervisor signals.
- `recall` calls for handoff generation and Q&A.
- `improve` calls from feedback and marked-important actions.
- `forget` calls for deletion and retention.
- Gemini note understanding before memory write.
- Gemini recall planning before Cognee recall.
- Gemini handoff writing from only verified Cognee-returned sources.
- Judge trace showing Cognee operation IDs, source IDs, and latency.
- Backend verifier that rejects unsourced generated claims.

Acceptance checks:

- Browser never receives Cognee API key.
- Browser never receives Gemini API key.
- Case memory persists across backend restart.
- Cognee trace confirms remember, recall, improve, forget.
- Proof screen shows active memory and reasoning layers.
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

Phase 1 remains as the local smoke-test path. Phase 2 is activated by setting `MEMORY_BACKEND=cognee`, the tenant-specific `COGNEE_BASE_URL`, `COGNEE_TENANT_ID`, `COGNEE_API_KEY`, `LLM_PROVIDER=gemini`, and `GEMINI_API_KEY`; that is the final hackathon proof path.
