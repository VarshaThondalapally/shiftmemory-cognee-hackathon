# Product Handover

## Product

Caregiver Handoff Memory is a role-based care handoff application for home-care and assisted-living teams.

The product is built around a simple operational problem: the person leaving a shift remembers small but important details, but the person starting the next shift often receives scattered notes, stale instructions, or no source for why something matters.

The app gives each actor a separate workspace:

- Night caregiver: records what changed during the shift.
- Morning lead: generates a clean handoff and asks follow-up questions.
- Supervisor: assigns workers to care recipients, reviews important or stale notes, and controls what remains in memory.
- Hackathon judge: inspects the complete memory lifecycle and proof traces.

## Core User Story

Rosa is the supervisor. She assigns Nia to the night shift for Avery and Omar to the morning shift.

During the night, Nia records: "At 3 AM Avery woke up twice, asked for water, and settled when the room was quiet."

The next morning, Omar signs in and generates a handoff. He does not paste Nia's note. The backend recalls the relevant memory through Cognee, Gemini writes a structured handoff, and the app cites the original source note.

If Rosa marks the 3 AM note important, future handoffs prioritize it. If Rosa removes a stale instruction, it disappears from future answers.

## What Cognee Does

Cognee is the memory layer behind the product, not an end-user feature.

- Remember: notes and case facts are stored as durable memory.
- Recall: the morning handoff and follow-up questions retrieve relevant memory later.
- Improve: supervisor feedback is sent as a memory improvement signal.
- Forget: removed notes are deleted so stale context does not keep resurfacing.

The app is intentionally designed so the user does not need to understand Cognee. The product experience is: save, handoff, ask, prioritize, remove. Cognee is the infrastructure that makes memory persist across sessions and workers.

## What Gemini Does

Gemini is the reasoning layer.

It helps interpret raw caregiver notes, create a recall plan, and draft the final handoff from recalled memory.

Gemini is not trusted alone. The backend checks that generated handoff items are grounded in stored source notes. If there is no verified source, the app should avoid pretending the memory exists.

## What The Backend Does

The FastAPI backend is the trust boundary.

It owns:

- JWT demo authentication.
- Role-based access control.
- Assigned patient filtering.
- Cognee and Gemini API keys.
- Memory source IDs.
- Proof traces.
- Failure handling.
- Handoff verification.

The browser never receives Cognee or Gemini keys.

## What Is Real In The Current Build

- React product app with login.
- JWT-backed demo sessions.
- Role-specific workspaces.
- Assigned patient filtering.
- Supervisor assignment dashboard.
- FastAPI backend.
- Cognee Cloud memory adapter.
- Gemini reasoning adapter.
- Local fallback mode for development.
- Proof screen with memory backend, reasoning layer, recall plan, source IDs, and redacted traces.
- GitHub Pages landing page and demo runbook.

## What Is Demo-Only

- Demo users are hardcoded.
- JWT secret is demo-configured, not production secret-managed.
- Patient and assignment data is in-memory/demo data.
- No production database.
- No real identity provider.
- No encrypted audit-log store.
- No HIPAA compliance claim.
- No real patient data.
- No medical advice claim.

## Production Path

Before this could be used by a real care organization:

- Replace demo auth with an identity provider such as Auth0, Cognito, Clerk, or enterprise SSO.
- Move patients, shifts, notes, assignments, and audit events into a database.
- Add tenant isolation at every backend query and Cognee dataset boundary.
- Add encrypted storage, secret management, and audit retention.
- Add rate limits, abuse protection, and background jobs for long Cognee operations.
- Add formal clinical/legal review before any medical-adjacent use.
- Add deployment observability: logs, metrics, tracing, alerts, and error budgets.

## Why This Is A Good Cognee Use Case

This product is about memory changing behavior over time.

A plain LLM can summarize what is inside the current prompt. That is not enough for this workflow. The product needs to remember across workers, shifts, refreshes, and future handoffs. It also needs source-backed recall, improvement feedback, and removal of stale context.

That maps directly to Cognee's memory lifecycle.
