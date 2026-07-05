# SRE Operational Readiness

## Operational Goal

ShiftMemory should fail honestly. If memory recall is unavailable, the system should not invent a handoff. If deletion fails, the system should surface and retry it. If the LLM is slow, the user should see predictable behavior.

## MVP Service Level Objectives

### Availability

Target:

- 99.0 percent for hackathon demo window.

Measure:

- successful API responses for authenticated demo flows.

### API Latency

Targets:

- CRUD endpoints p95 under 1000 ms.
- Add note including Cognee remember p95 under 5000 ms.
- Generate handoff p95 under 8000 ms.
- Ask question p95 under 7000 ms.

### Memory Reliability

Targets:

- remember success rate above 99 percent in demo.
- recall success rate above 99 percent in demo.
- forget success rate 100 percent for tested demo deletion.

### Output Faithfulness

Targets:

- 100 percent of generated factual bullets have source IDs in demo.
- 0 cross-case source references.
- 0 medical advice claims.

## Service Level Indicators

Track:

- request count by endpoint;
- HTTP 4xx and 5xx rate;
- p50, p95, p99 latency;
- Cognee remember latency and error rate;
- Cognee recall latency and error rate;
- Cognee improve latency and error rate;
- Cognee forget latency and error rate;
- LLM latency and error rate;
- output validation failure rate;
- source citation coverage;
- rate-limit hits;
- pending memory indexing count;
- delete pending count;
- Cognee or LLM balance remaining if exposed by provider.

## Alert Thresholds

MVP alerts can be simple logs or dashboard warnings.

Critical:

- forget failure count greater than 0;
- cross-case source validation failure greater than 0;
- Cognee auth failure;
- API key missing;
- generated output without source IDs.

Warning:

- API 5xx rate above 2 percent for 5 minutes;
- Cognee recall failure above 5 percent for 5 minutes;
- LLM timeout above 10 percent for 5 minutes;
- handoff p95 above 10 seconds for 10 minutes;
- pending memory indexing older than 5 minutes;
- Cognee or LLM balance low.

## Runbooks

### Cognee Recall Outage

Symptoms:

- handoff generation fails;
- case Q&A fails;
- Cognee recall errors in logs.

Immediate action:

1. Check `/readyz`.
2. Check Cognee health endpoint or Cloud status.
3. Verify API key and base URL.
4. Disable AI handoff generation if recall is unavailable.
5. Show manual notes timeline as fallback.

User message:

```text
Case memory is temporarily unavailable. Manual notes are still available, but AI handoff generation is paused.
```

### Cognee Remember Failure

Symptoms:

- note saved but memory status stays pending.

Immediate action:

1. Keep source in app DB.
2. Queue retry.
3. Mark source `memory_status=pending`.
4. Do not include the note in AI handoff until indexed.

User message:

```text
Your note was saved. Memory indexing is still pending.
```

### Cognee Forget Failure

Symptoms:

- delete endpoint returns failure;
- deleted source still appears in recall.

Immediate action:

1. Tombstone source in app DB.
2. Block source from app-layer output.
3. Retry Cognee forget.
4. Alert engineering immediately.
5. Verify with recall test.

User message:

```text
This memory is hidden from the app while deletion is being completed.
```

### LLM Provider Outage

Symptoms:

- recall succeeds but handoff generation fails.

Immediate action:

1. Keep recalled sources available.
2. Show source list without generated summary.
3. Retry with backup provider if configured.
4. Do not generate from stale or missing context.

### Balance Exhaustion

Symptoms:

- provider returns quota, payment, or credit errors.

Immediate action:

1. Disable generation endpoints.
2. Keep note creation available if it does not incur provider cost.
3. Show admin warning.
4. Switch to fallback key only if approved.

### Bad Memory Ingestion

Symptoms:

- incorrect note remembered;
- prompt-injection source remembered;
- irrelevant source dominates handoff.

Immediate action:

1. Mark source disputed.
2. Use forget if incorrect or unsafe.
3. Use improve if source is valid but ranking is poor.
4. Add supervisor correction.
5. Regenerate handoff and verify trace.

### Suspected Cross-Case Recall

Symptoms:

- output cites wrong case source.

Immediate action:

1. Disable generated outputs.
2. Preserve trace.
3. Check dataset naming and auth.
4. Run case isolation test.
5. Review source validation code.
6. Do not resume until fixed.

## Observability Design

Every request gets:

- `request_id`;
- `actor_id`;
- `org_id`;
- `case_id`;
- endpoint;
- status;
- latency.

Every memory operation gets:

- `memory_operation_id`;
- Cognee operation;
- Cognee dataset;
- source ID;
- status;
- latency;
- error code.

Every generation gets:

- model provider;
- model name;
- token counts if available;
- memory trace ID;
- validation result;
- output source coverage.

## Readiness Checklist

`/readyz` should fail if:

- app DB unavailable;
- Cognee base URL missing;
- Cognee API key missing;
- LLM key missing;
- required migrations not applied.

`/healthz` should pass if:

- server process is alive.

## Backup and Recovery

MVP:

- export demo data seed files;
- recreate Cognee datasets from app sources if needed;
- keep no real sensitive data.

Production path:

- app DB backups;
- object storage versioning;
- Cognee dataset export if supported by deployment;
- documented restore drill.

## Launch Readiness Gate

Before public demo:

- add note works;
- recall uses Cognee;
- handoff has sources;
- improve changes future behavior or at least records feedback and calls Cognee;
- forget removes memory from recall;
- case isolation test passes;
- secrets are backend-only;
- runbook docs are linked in README.
