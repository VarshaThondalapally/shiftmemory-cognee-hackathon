# ShiftMemory

ShiftMemory is a Cognee-backed memory architecture for shift-based handoffs. The hackathon demo domain is caregiving operations, but the product category is broader: never-forget workflows where agents and workers need durable, scoped, correctable memory across sessions.

## What This Repo Contains

- `docs/`: pre-MVP engineering packet.
- `site/`: GitHub Pages-ready microsite.
- `site/demo.html`: current visual product mock.
- `.github/workflows/pages.yml`: GitHub Pages deployment workflow.

## Core Product Claim

Generic LLMs can summarize what a user pastes into a prompt. ShiftMemory uses Cognee so the product can remember, recall, improve, and forget operational context across workers, sessions, and agent surfaces.

## Cognee Usage

- `remember`: shift notes, uploaded files, confirmed handoffs, task events, and supervisor decisions.
- `recall`: handoffs, case Q&A, timelines, and judge trace proof.
- `improve`: supervisor corrections and importance feedback.
- `forget`: stale, incorrect, sensitive, or expired memory.

The MVP should use Cognee Cloud from the backend only. The browser must never receive Cognee or LLM API keys.

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
- `docs/02_Cognee_Memory_Architecture.md`
- `docs/06_Security_Threat_Model.md`
- `docs/07_SRE_Operational_Readiness.md`
- `docs/08_MVP_Roadmap_and_Acceptance.md`
