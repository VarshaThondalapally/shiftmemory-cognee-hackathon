# ShiftMemory Pre-MVP Engineering Packet

Date: 2026-07-04

Product: ShiftMemory

Hackathon: WeMakeDevs x Cognee, "The Hangover Part AI: Where's My Context?"

## Executive Decision

ShiftMemory will be built as a secure memory-backed handoff system for shift-based teams. The demo domain is caregiving and operational shift handoff, but the core category is broader: never-forget workflows where each shift, agent, and review cycle can reuse memory from prior sessions.

Cognee is not a hidden add-on. Cognee is the product's memory substrate:

- `remember`: store notes, files, events, and decisions as durable memory.
- `recall`: retrieve case-specific memory for handoffs, questions, and review.
- `improve`: enrich memory and tune future recall using supervisor feedback.
- `forget`: remove stale, sensitive, incorrect, or expired memories.

The end user does not manage Cognee. The end user manages human work: notes, handoffs, questions, confirmations, and corrections. Reviewers and engineers get a separate memory trace view that proves Cognee usage.

## Packet Contents

1. [Product Strategy and Judging Fit](./01_Product_Strategy_and_Judging.md)
2. [Cognee Memory Architecture](./02_Cognee_Memory_Architecture.md)
3. [AI Agent Runtime](./03_AI_Agent_Runtime.md)
4. [System Architecture](./04_System_Architecture.md)
5. [API Contract](./05_API_Contract.md)
6. [Security Threat Model](./06_Security_Threat_Model.md)
7. [SRE Operational Readiness](./07_SRE_Operational_Readiness.md)
8. [MVP Roadmap and Acceptance Checks](./08_MVP_Roadmap_and_Acceptance.md)
9. [Submission Pitch Deck Outline](./09_Submission_Pitch_Deck_Outline.md)
10. [Final Test Report](./11_Final_Test_Report.md)

## MVP Build Rule

Do not start implementation until these are true:

- The Cognee Cloud tenant, API key, and base URL are available in backend-only secrets.
- The memory data model and case isolation rules are implemented before the UI demo flow.
- The demo uses synthetic data only.
- The app can prove that a note remembered in one session is recalled by another session or agent surface.
- The app can forget a note and show it no longer appears in future recall.
- The README and pitch explain Cognee's role clearly enough that a reviewer can see why this is not a generic LLM wrapper.

## Primary Sources

- Hackathon page: https://www.wemakedevs.org/hackathons/cognee
- Cognee core concepts: https://docs.cognee.ai/core-concepts/overview
- Cognee architecture: https://docs.cognee.ai/core-concepts/architecture
- Cognee API reference: https://docs.cognee.ai/api-reference/introduction
- Cognee Python API reference: https://docs.cognee.ai/python-api
- Cognee security and privacy: https://docs.cognee.ai/setup-configuration/security
