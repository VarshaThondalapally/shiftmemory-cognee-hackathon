# Submission Copy

## Project Title

Caregiver Handoff Memory

## One-Liner

A secure role-based handoff app where night caregivers save small shift details once, morning leads recall them later with sources, and supervisors improve or forget memory before it misleads the next shift.

## Problem

In home-care and assisted-living work, the most important shift details are often small: a resident woke at 3 AM, a family member needs a call before breakfast, or a stale food preference should no longer be followed.

Those details are easy to lose when workers change shifts, apps refresh, or notes are scattered across messages.

## Solution

The product gives each role its own workspace:

- Night caregiver records what changed.
- Morning lead generates a clean handoff and asks follow-up questions.
- Supervisor assigns workers, prioritizes important memory, and removes stale context.
- Demo reviewer inspects proof traces.

The worker experience stays simple. Cognee runs behind the backend as the memory layer.

## How Cognee Is Used

Cognee powers the memory lifecycle:

- `remember`: store night notes and care-recipient facts.
- `recall`: retrieve relevant memory for the morning handoff.
- `improve`: send supervisor feedback back into the memory process.
- `forget`: remove wrong or stale notes so they stop appearing.

The app shows proof through source-backed handoffs and redacted backend traces.

## Why Not Just Gemini

Gemini can reason over what is currently in the prompt. The product needs memory that survives across shifts, workers, browser refreshes, and future handoffs.

Cognee provides the persistent memory layer. Gemini provides reasoning over the memory that Cognee retrieves.

## Demo Flow

1. Supervisor assigns a night caregiver and morning lead to a care recipient.
2. Night caregiver adds a 3 AM note.
3. Morning lead generates the handoff without pasting that note again.
4. Handoff cites the source note.
5. Supervisor marks it important or removes stale context.
6. Demo reviewer opens proof mode and sees the memory lifecycle traces.

## Tech Stack

- React frontend.
- FastAPI backend.
- JWT demo authentication.
- Role-based access control.
- Cognee Cloud memory backend.
- Gemini reasoning layer.
- GitHub Pages presentation site.

## Links

- GitHub: `https://github.com/VarshaThondalapally/shiftmemory-cognee-hackathon`
- Landing page: `https://varshathondalapally.github.io/shiftmemory-cognee-hackathon/`
- Local demo: `http://127.0.0.1:5173/`
- Backend health: `http://127.0.0.1:8001/healthz`

## Boundary

This is a hackathon MVP using synthetic data. It is not production healthcare software and is not a HIPAA compliance claim.
