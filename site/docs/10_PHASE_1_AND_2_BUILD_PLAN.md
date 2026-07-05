# Phase 1 and Phase 2 Build Plan

## Phase 1: Local Product MVP

Goal: make ShiftMemory a real local app, not a static demo.

Phase 1 uses a local memory adapter that mirrors Cognee's lifecycle. This lets us test product behavior immediately without waiting for cloud keys.

Deliverables:

- FastAPI backend with memory lifecycle endpoints.
- React frontend for the actual shift handoff workflow.
- Synthetic demo case data.
- Local persisted memory in JSON.
- Handoff generation from remembered notes.
- Q&A over case memory.
- Feedback that marks memory high-signal.
- Forget action that removes memory from future handoffs.
- Memory trace view that proves each lifecycle operation.

Acceptance checks:

- Add note, refresh app, note still appears.
- Generate handoff from remembered notes.
- Ask a question and receive source-backed answer.
- Mark a note important and see it prioritized.
- Forget a note and confirm it disappears from handoff.
- View memory trace showing remember, recall, improve, forget.

## Phase 2: Cognee-Backed MVP

Goal: replace local memory with Cognee Cloud while keeping the same product UX.

Deliverables:

- Cognee Cloud credentials stored in backend-only `.env`.
- `MemoryService` implementation backed by Cognee.
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

## Current Boundary

Phase 1 is the right first build because it proves the product workflow. Phase 2 is the hackathon differentiator because it proves real persistent Cognee memory.
