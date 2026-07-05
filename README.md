# ShiftMemory

ShiftMemory is a shift handoff product with a Cognee-shaped memory lifecycle. The hackathon demo domain is caregiving operations, but the product category is broader: never-forget workflows where agents and workers need durable, scoped, correctable memory across sessions.

## What This Repo Contains

- `apps/backend/`: FastAPI local MVP API.
- `apps/frontend/`: React local MVP app.
- `docs/`: engineering packet and build plan.
- `site/`: GitHub Pages-ready microsite.
- `site/demo.html`: visual workflow demo.
- `.github/workflows/pages.yml`: GitHub Pages deployment workflow.

## Core Product Claim

Generic LLMs can summarize what a user pastes into a prompt. ShiftMemory uses Cognee so the product can remember, recall, improve, and forget operational context across workers, sessions, and agent surfaces.

## Cognee Usage

- `remember`: shift notes, uploaded files, confirmed handoffs, task events, and supervisor decisions.
- `recall`: handoffs, case Q&A, timelines, and judge trace proof.
- `improve`: supervisor corrections and importance feedback.
- `forget`: stale, incorrect, sensitive, or expired memory.

The MVP should use Cognee Cloud from the backend only. The browser must never receive Cognee or LLM API keys.

## Phase 1 Local MVP

Phase 1 is now scaffolded as a local app. It uses a local memory adapter with the same lifecycle we will connect to Cognee in Phase 2.

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

## Phase 2 Cognee MVP

Phase 2 replaces the local memory adapter with Cognee Cloud calls while keeping the same frontend and API shape.

Required backend-only environment:

```text
MEMORY_BACKEND=cognee
COGNEE_BASE_URL=<your-cognee-cloud-url>
COGNEE_API_KEY=<your-cognee-key>
```

See `docs/10_PHASE_1_AND_2_BUILD_PLAN.md`.

## Local Preview

Open:

```text
site/index.html
```

The current demo is:

```text
site/demo.html
```

## GitHub Pages

After this repo is pushed to GitHub:

1. Go to repository settings.
2. Open Pages.
3. Set the source to GitHub Actions.
4. Run the `Deploy GitHub Pages site` workflow.

The workflow publishes the `site/` directory.

## Important MVP Boundaries

- Use synthetic demo data only.
- Do not claim HIPAA compliance.
- Do not provide medical advice, diagnosis, or treatment guidance.
- Treat notes and uploaded files as untrusted input.
- Require source references for generated handoffs.
- Implement `forget` before public judging.

## Best Starting Point

Read:

- `docs/00_INDEX.md`
- `docs/10_PHASE_1_AND_2_BUILD_PLAN.md`
- `docs/02_Cognee_Memory_Architecture.md`
- `docs/06_Security_Threat_Model.md`
- `docs/07_SRE_Operational_Readiness.md`
- `docs/08_MVP_Roadmap_and_Acceptance.md`
