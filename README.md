# Caregiver Handoff Memory Demo

A caregiver finishes a night shift. They leave a few small but important notes: family asked for an update, the resident was restless, breakfast preference changed, and one old note is wrong.

Morning staff opens the app and clicks one button. The app generates a clean handoff from remembered notes, cites the source notes, lets a supervisor prioritize important information, and removes stale notes from future answers.

That is the hackathon use case: a memory-backed handoff assistant for teams where missing one small note creates confusion in the next shift.

## What The Demo Proves

- Add a night note.
- Refresh or restart the app.
- Generate the morning handoff without pasting context again.
- Ask a question like "What should I tell the family?"
- Mark a note important and see future handoffs prioritize it.
- Remove a wrong note and confirm it no longer appears.
- Open the proof screen to show the memory lifecycle.

## Final Submission Architecture

The submitted product uses three separate responsibilities:

- Gemini is the reasoning layer. It understands raw notes, creates the recall plan, and writes the final handoff.
- Cognee is the memory layer. It stores remembered notes and retrieves the relevant context later.
- The FastAPI backend is the verifier. It owns keys, case boundaries, source checks, audit traces, and failure handling.

The browser never receives Cognee or LLM keys. The frontend talks only to the FastAPI backend.

## How Cognee Is Used

Cognee is the backend memory layer, not an end-user feature.

- `remember`: night notes and case facts are written as durable memory.
- `recall`: handoffs and case questions retrieve remembered context.
- `improve`: reviewer feedback is audited and sent to Cognee as a re-processing signal, without turning reviewer wording into a worker-facing handoff fact.
- `forget`: removed notes are deleted from future recall.

For final mode, the backend only uses Cognee recall results that can be mapped back to stored source notes. If Cognee returns no verifiable source, the handoff says no verified memory was found instead of inventing a note.

## Run Locally

Backend:

```powershell
cd apps/backend
C:\Users\thond\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd apps/frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Shortcut after dependencies are installed:

```powershell
.\scripts\dev.ps1
```

## Final Hackathon Mode

Use local mode while designing the UI. Use Cognee plus Gemini mode for the final hackathon proof run.

Backend-only `.env` for final mode. You can copy from `apps/backend/.env.final.example`:

```text
MEMORY_BACKEND=cognee
COGNEE_BASE_URL=https://tenant-your-tenant-id.aws.cognee.ai
COGNEE_API_KEY=your_key
COGNEE_TENANT_ID=your_tenant_id
COGNEE_STRICT=true
COGNEE_DATASET_PREFIX=handoff-demo
COGNEE_ALLOW_LOCAL_RANK_FALLBACK=false
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
LLM_STRICT=true
```

Use the hackathon Cognee balance only for lifecycle actions: add note, generate handoff, ask question, prioritize, remove, and demo reset. Do not spend it on page refreshes or UI navigation.

For local development without paid or hackathon API calls, copy `apps/backend/.env.example` instead. That keeps `MEMORY_BACKEND=local` and leaves `LLM_PROVIDER` empty so the deterministic fallback is used.

## What The Proof Screen Shows

- The active memory backend: local fallback or Cognee Cloud.
- The active reasoning layer: local fallback or Gemini.
- The recall plan created for the handoff.
- Redacted backend-to-Cognee requests and responses.
- Source IDs used in the handoff.
- Failures, including Cognee API errors, without exposing API keys.

## Final Verified Run

Last verified on 2026-07-05 against the tenant-specific Cognee Cloud API and Gemini `gemini-2.5-flash`.

- Cognee `remember`: 200 for seed notes and the live 3 AM night-shift note.
- Cognee `recall`: 200 and returned the 3 AM note into the `watch_today` handoff section.
- Cognee `cognify`: 200 when reviewer feedback marked the 3 AM source important.
- Cognee `forget`: 200 and removed the stale orange-juice source from the next handoff.
- Backend verification rejected uncited facts and kept reviewer wording out of the worker-facing handoff.
- GitHub Pages deployment passed and the public site returned HTTP 200.

## Smoke Test

```powershell
cd apps/backend
.\.venv\Scripts\python.exe ..\..\scripts\smoke_product.py
```

Expected output:

```text
PASS: handoff memory demo lifecycle works end to end
```

## Repo Structure

- `apps/backend/`: FastAPI backend and memory adapters.
- `apps/frontend/`: React product demo.
- `scripts/smoke_product.py`: end-to-end demo lifecycle test.
- `docs/`: architecture, security, SRE, and submission docs.
- `site/`: GitHub Pages microsite.

## Boundaries

- Synthetic demo data only.
- Not HIPAA compliant.
- Not medical advice, diagnosis, or treatment guidance.
- Notes are treated as untrusted input.
- Source references are required for handoffs and answers.
