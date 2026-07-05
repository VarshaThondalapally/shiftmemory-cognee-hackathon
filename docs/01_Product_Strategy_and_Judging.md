# Product Strategy and Judging Fit

## One-Line Product

ShiftMemory is an AI handoff assistant for shift-based teams that remembers prior notes, documents, risks, and decisions across sessions, then generates source-backed handoffs and answers case questions without making workers repeat context.

## Real Problem

Shift work has a memory problem. Night shift sees something, morning shift needs it, supervisors need the history, and information is split across notes, chats, files, and people's heads. Generic LLMs are useful for summarization, but they forget across sessions unless the application owns memory.

ShiftMemory solves this by giving each case a durable memory layer. The system remembers what happened, recalls the right context for the next worker, improves based on feedback, and forgets data that should not remain.

## Target User for MVP

Primary demo user:

- Caregiver, nurse assistant, home-care coordinator, facility supervisor, or any shift-based operator.

Hackathon evaluator:

- Cognee team member or judge evaluating whether this product uses Cognee deeply, not superficially.

Future buyer:

- Operations teams where handoff errors create cost, risk, delay, or compliance exposure.

## Why This Is Not Just Another AI Notes App

The wedge is not "AI summarizes notes." Many teams can build that.

The wedge is: the AI has a durable, inspectable, case-scoped memory that survives new sessions, new workers, new agent surfaces, and deletion requests.

This maps directly to the hackathon's stated problem: LLM calls are stateless and lose context. ShiftMemory makes context persistent, scoped, and usable.

## Judging Criteria Alignment

### Potential Impact

Strong fit. Shift handoff failures are common across caregiving, support, logistics, operations, incident response, and field service. The MVP uses caregiving because the pain is immediately understandable, but the architecture generalizes.

### Creativity and Innovation

Moderate to strong fit. The idea is not exotic, but the implementation angle is serious: a memory-backed workflow where notes, documents, questions, supervisor feedback, and deletion all operate on the same durable Cognee memory layer.

The innovation is in making memory operational:

- different agent surfaces share the same case memory;
- feedback changes future handoffs;
- forgetting is first-class;
- handoffs include source references and unknowns.

### Technical Excellence

The MVP must be judged by implementation discipline:

- backend-controlled Cognee access;
- strict tenant and case scoping;
- structured output schemas;
- idempotent memory writes;
- memory trace logging;
- safety handling for prompt injection and hallucination;
- SRE runbooks before launch.

### Best Use of Cognee

This must be our strongest category. The build uses all four core operations:

- `remember` for notes, documents, events, and decisions;
- `recall` for handoffs, questions, and context reconstruction;
- `improve` for feedback-driven enrichment;
- `forget` for deletion, retention, and correction.

It also shows why Cognee's graph-vector model matters: semantic recall finds related notes even when wording differs, while graph structure can connect people, tasks, risks, documents, and prior decisions.

### User Experience

The user should never see Cognee terminology in the normal product flow. They should see:

- Add note
- Upload file
- Generate handoff
- Ask question
- Mark important
- Correct answer
- Remove memory

The judge mode can expose the technical trace.

### Presentation Quality

The pitch should be a story:

1. Night shift knows something important.
2. Morning shift starts with missing context.
3. A generic LLM cannot remember across sessions.
4. ShiftMemory uses Cognee as durable memory.
5. The same memory powers handoff, Q&A, feedback, and deletion.
6. This pattern expands to any shift-based workflow.

## Positioning

Recommended positioning:

"ShiftMemory is the memory layer for high-stakes team handoffs."

Avoid positioning:

- "Healthcare AI platform"
- "Medical assistant"
- "Diagnosis helper"
- "EHR replacement"

Those create compliance and scope risk. The hackathon product should be a workflow memory system with a caregiving demo.

## MVP Non-Goals

- No real patient data.
- No diagnosis, treatment, prescription, or clinical decisioning.
- No claim of HIPAA compliance in the hackathon submission.
- No EHR integration in MVP.
- No autonomous action without human review.
- No unscoped cross-case search.

## Product Principles

- Memory must be useful, not magical.
- Every generated handoff should show source references.
- The system should say "unknown" when memory is insufficient.
- Users correct memory through normal workflow actions.
- Deletion is a product feature, not an admin chore.
- Cognee proof should be available to judges without exposing technical complexity to end users.
