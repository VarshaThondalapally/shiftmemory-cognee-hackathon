# Submission Pitch Deck Outline

## Slide 1: ShiftMemory

Title:

ShiftMemory

Subtitle:

Persistent AI memory for high-stakes team handoffs.

Speaker note:

"We built ShiftMemory because every shift-based workflow has the same failure mode: the next person starts without the full context."

## Slide 2: The Problem

Main point:

LLMs are stateless, and shift work is context-heavy.

Bullets:

- Notes live across people, files, chats, and memory.
- Generic AI forgets unless every context is pasted again.
- Handoff mistakes create cost, delay, and risk.

Visual:

Night shift note disappearing before morning shift.

## Slide 3: Product Story

Main point:

Night shift remembers once. Morning shift starts informed.

Flow:

1. Worker adds note.
2. ShiftMemory remembers it.
3. Morning shift generates handoff.
4. Supervisor corrects or marks important.
5. Future agents recall improved memory.

## Slide 4: Why Cognee

Main point:

Cognee is the memory layer, not a side integration.

Bullets:

- `remember` stores notes, files, and confirmed handoffs.
- `recall` retrieves scoped case memory.
- `improve` uses feedback to enrich future results.
- `forget` removes incorrect or expired memory.

Visual:

Memory lifecycle diagram.

## Slide 5: Architecture

Main point:

The backend controls memory, authorization, and generation.

Diagram:

Frontend -> Backend -> Cognee Cloud -> LLM -> Source-backed handoff

Bullets:

- Browser never sees Cognee API key.
- One dataset per case for MVP isolation.
- App DB stores audit and workflow state.
- Cognee stores graph-vector memory.

## Slide 6: Demo

Main point:

The demo proves persistent memory across sessions.

Demo beats:

- Add night-shift note.
- Generate morning handoff.
- Ask case question.
- Improve with supervisor feedback.
- Forget incorrect note.
- Show judge memory trace.

## Slide 7: Best Use of Cognee

Main point:

ShiftMemory uses the full Cognee lifecycle.

Evidence:

- remember: note/file ingestion;
- recall: handoff and Q&A;
- improve: supervisor feedback;
- forget: deletion and retention;
- graph-vector memory: relationships plus semantic retrieval;
- trace view: operation proof.

## Slide 8: Security and Trust

Main point:

Memory without trust is dangerous.

Bullets:

- Synthetic demo data only.
- Case-scoped datasets.
- Source-backed outputs.
- Prompt injection controls.
- Backend-only secrets.
- Forget and audit built into MVP.

## Slide 9: Expansion

Main point:

One memory layer can power many agents.

Future surfaces:

- web dashboard;
- Slack or Teams bot;
- scheduled morning handoff;
- supervisor review agent;
- incident review agent;
- n8n workflow.

## Slide 10: Why This Wins

Main point:

ShiftMemory turns Cognee's memory model into a real workflow people understand.

Closing:

"The product is simple on the surface because the complexity is handled where it belongs: in a secure backend and in Cognee's persistent memory layer."

## Submission README Claims

Use these claims only if implemented:

- "Uses Cognee Cloud for persistent case memory."
- "Implements remember, recall, improve, and forget."
- "Includes judge trace proving Cognee operation usage."
- "Uses source-backed generated handoffs."
- "Uses synthetic data only."

Do not claim:

- HIPAA compliance.
- clinical decision support.
- production security certification.
- autonomous care recommendations.
