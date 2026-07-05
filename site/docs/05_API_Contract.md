# API Contract

## Contract Goals

The API must make memory behavior explicit without exposing Cognee internals to end users.

Design goals:

- all Cognee calls happen server-side;
- every write is idempotent;
- every generated claim can be traced to source IDs;
- every request is scoped by org and case;
- deletion and recall are auditable.

## Common Headers

```text
Authorization: Bearer <session-token>
Idempotency-Key: <uuid>       # required on writes
X-Request-ID: <uuid>          # optional from client, generated if missing
```

## Error Shape

```json
{
  "error": {
    "code": "memory_recall_failed",
    "message": "Unable to recall case memory. Try again.",
    "request_id": "req_01J...",
    "retryable": true
  }
}
```

## Roles

- `org_admin`: manage org settings, users, all cases.
- `supervisor`: review handoffs, mark important, forget case memories.
- `worker`: add notes, generate handoffs, ask questions for assigned cases.
- demo reviewer: read demo cases and memory traces only.

## Endpoints

### Health

```http
GET /healthz
GET /readyz
```

Readiness checks:

- app DB reachable;
- Cognee health check reachable;
- LLM provider configured;
- required secrets present.

### Create Case

```http
POST /v1/cases
```

Request:

```json
{
  "display_name": "Resident Avery",
  "demo_template": "caregiving_shift"
}
```

Response:

```json
{
  "case_id": "case_01J...",
  "display_name": "Resident Avery",
  "cognee_dataset": "shiftmemory:demo:org:demo-care:case:case_01J...",
  "status": "active"
}
```

Backend actions:

- create app DB case;
- derive Cognee dataset name;
- optionally seed synthetic demo memory.

### List Cases

```http
GET /v1/cases
```

Response:

```json
{
  "cases": [
    {
      "case_id": "case_01J...",
      "display_name": "Resident Avery",
      "status": "active",
      "last_memory_at": "2026-07-04T22:15:00Z"
    }
  ]
}
```

### Add Note

```http
POST /v1/cases/{case_id}/notes
```

Request:

```json
{
  "shift_id": "night_2026_07_04",
  "title": "Evening check-in",
  "body": "Synthetic demo note...",
  "importance": "normal",
  "tags": ["hydration", "family-request"]
}
```

Response:

```json
{
  "source_id": "note_01J...",
  "memory_id": "mem_01J...",
  "memory_status": "indexed",
  "cognee_operation": "remember"
}
```

Validation:

- body length limit;
- no empty notes;
- assigned case only;
- synthetic-data warning in demo mode.

### Upload File

```http
POST /v1/cases/{case_id}/files
Content-Type: multipart/form-data
```

Accepted MVP file types:

- `.txt`
- `.md`
- `.pdf` if parsing is implemented safely.

Response:

```json
{
  "source_id": "file_01J...",
  "memory_status": "indexing",
  "cognee_operation": "remember"
}
```

Security:

- size limit;
- MIME validation;
- virus scanning if deployed beyond demo;
- local file paths never accepted from users.

### Generate Handoff

```http
POST /v1/cases/{case_id}/handoff
```

Request:

```json
{
  "shift_id": "morning_2026_07_05",
  "since": "2026-07-04T19:00:00Z",
  "focus": ["changes", "risks", "tasks"]
}
```

Response:

```json
{
  "handoff_id": "handoff_01J...",
  "status": "draft",
  "memory_trace_id": "trace_01J...",
  "output": {
    "summary": "string",
    "changes": [],
    "risks": [],
    "tasks": [],
    "people_context": [],
    "unknowns": [],
    "source_refs": [],
    "safety_note": "This is a workflow handoff, not medical advice."
  }
}
```

Backend actions:

- call Cognee recall with multiple intents;
- call LLM with bounded recalled context;
- validate output;
- store draft and trace.

### Confirm Handoff

```http
POST /v1/cases/{case_id}/handoffs/{handoff_id}/confirm
```

Response:

```json
{
  "handoff_id": "handoff_01J...",
  "status": "confirmed",
  "remembered_as_source_id": "handoff_source_01J..."
}
```

Backend actions:

- mark handoff confirmed;
- remember confirmed handoff as new case memory.

### Ask Case Question

```http
POST /v1/cases/{case_id}/ask
```

Request:

```json
{
  "session_id": "session_01J...",
  "question": "What should the morning shift know about family requests?"
}
```

Response:

```json
{
  "answer": "string",
  "source_refs": [
    {
      "source_id": "note_01J...",
      "excerpt": "short source excerpt"
    }
  ],
  "unknowns": [],
  "memory_trace_id": "trace_01J..."
}
```

### Submit Feedback

```http
POST /v1/cases/{case_id}/feedback
```

Request:

```json
{
  "target_type": "handoff",
  "target_id": "handoff_01J...",
  "rating": "useful",
  "correction": "Make the family request more prominent."
}
```

Response:

```json
{
  "feedback_id": "fb_01J...",
  "cognee_operation": "improve",
  "status": "accepted"
}
```

### Forget Memory

```http
DELETE /v1/cases/{case_id}/memories/{source_id}
```

Request:

```json
{
  "reason": "incorrect_or_outdated",
  "confirm": true
}
```

Response:

```json
{
  "source_id": "note_01J...",
  "cognee_operation": "forget",
  "status": "forgotten"
}
```

Authorization:

- supervisor or org admin in MVP.

### Memory Trace

```http
GET /v1/cases/{case_id}/memory-traces/{trace_id}
```

Response:

```json
{
  "trace_id": "trace_01J...",
  "case_id": "case_01J...",
  "operations": [
    {
      "operation": "recall",
      "dataset": "shiftmemory:demo:org:demo-care:case:case_01J...",
      "query": "recent changes since last shift",
      "latency_ms": 820,
      "result_count": 5,
      "source_ids": ["note_01J..."]
    }
  ],
  "llm": {
    "provider": "configured-provider",
    "model": "configured-model",
    "latency_ms": 2400
  }
}
```

Visibility:

- hidden from normal users by default;
- visible in demo reviewer mode and admin mode.

## Rate Limits

Suggested MVP limits:

- add note: 60 per user per hour;
- ask question: 30 per user per hour;
- generate handoff: 10 per case per hour;
- file upload: 10 MB per file in demo;
- forget memory: supervisor/admin only, no automated bulk delete without confirmation.

## Idempotency

All write endpoints require `Idempotency-Key`.

Behavior:

- same key and same payload returns original result;
- same key and different payload returns conflict;
- keys expire after 24 hours in MVP.

## Audit Requirements

Every endpoint that changes memory must emit:

- actor ID;
- org ID;
- case ID;
- source ID;
- Cognee operation;
- request ID;
- timestamp;
- status;
- error details if failed.
