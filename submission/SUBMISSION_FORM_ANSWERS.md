# Submission Form Answers

Use this as copy for the hackathon submission form.

## Project Name

Caregiver Handoff Memory

## Short Description

A secure role-based handoff app where night caregivers save shift details once, morning leads recall them later with sources, and supervisors improve or forget memory before it misleads the next shift.

## GitHub Repository

`https://github.com/VarshaThondalapally/shiftmemory-cognee-hackathon`

## Deployed Link

`https://varshathondalapally.github.io/shiftmemory-cognee-hackathon/`

Note: the deployed link is the public landing/demo explainer. The full interactive app currently runs locally because it requires a FastAPI backend with Cognee and Gemini server-side keys.

## Demo Video Link

Upload `submission/video/caregiver-handoff-memory-demo.mp4` to YouTube as unlisted, then paste the YouTube URL here.

## Problem

In home-care and assisted-living handoffs, important details are often small: a resident woke at 3 AM, a family member needs an update before breakfast, or an old preference should no longer be followed.

Those notes are easy to lose when workers change shifts, apps refresh, or the next worker has to ask someone to repeat context.

## Solution

Caregiver Handoff Memory gives each actor a separate workspace:

- Supervisor assigns night and morning workers to care recipients.
- Night caregiver saves only what changed during the shift.
- Morning lead generates a source-backed handoff and asks follow-up questions.
- Supervisor marks important memory or removes stale context.
- Judge mode shows the memory lifecycle proof.

## How Cognee Is Used

Cognee is the persistent memory layer behind the workflow.

- Remember: night notes and care-recipient facts are stored as memory.
- Recall: handoffs and follow-up questions retrieve relevant case memory.
- Improve: supervisor feedback is sent as an improvement signal.
- Forget: stale or wrong memory is removed from future recall.

The app does not ask end users to understand Cognee. They use normal workflow actions: save, handoff, ask, keep important, and remove.

## How AI Agents/LLMs Are Used

Gemini is the reasoning layer. It interprets raw notes, creates recall plans, and writes the structured handoff from remembered sources.

OpenAI Codex was used during development as an AI pair/founding engineer to help analyze requirements, design architecture, implement the MVP, test locally, and prepare submission materials. See `handover/AI_USAGE_DISCLOSURE.md`.

## Why This Needs Cognee Instead Of Only Gemini

Gemini can reason over what is currently in a prompt. The product needs memory that survives across shifts, workers, browser refreshes, future handoffs, supervisor feedback, and deletion of stale context.

Cognee provides persistent memory lifecycle behavior. Gemini reasons over the context that Cognee recalls.

## Tech Stack

- React frontend.
- FastAPI backend.
- JWT demo authentication.
- Role-based access control.
- Cognee Cloud memory backend.
- Gemini reasoning layer.
- GitHub Pages presentation site.

## Boundaries

This is a hackathon MVP with synthetic demo data. It is not production healthcare software, not medical advice, and not a HIPAA compliance claim.
