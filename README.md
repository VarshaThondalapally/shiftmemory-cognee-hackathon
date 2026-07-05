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

## How Cognee Is Used

Cognee is the backend memory layer, not an end-user feature.

- `remember`: night notes and supervisor feedback are written as durable memory.
- `recall`: handoffs and case questions retrieve remembered context.
- `improve`: reviewer feedback is written back so future outputs prioritize better context.
- `forget`: removed notes are deleted from future recall.

The browser never receives Cognee or LLM keys. The frontend talks only to the FastAPI backend.

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

## Use Cognee Cloud

Use local mode while designing the UI. Use Cognee mode for the final hackathon proof run.

Backend-only `.env`:

```text
MEMORY_BACKEND=cognee
COGNEE_BASE_URL=https://your-tenant.aws.cognee.ai
COGNEE_API_KEY=your_key
COGNEE_STRICT=true
COGNEE_DATASET_PREFIX=handoff-demo
```

Use the hackathon Cognee balance only for lifecycle actions: add note, generate handoff, ask question, prioritize, remove, and demo reset. Do not spend it on page refreshes or UI navigation.

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
