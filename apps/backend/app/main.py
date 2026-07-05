from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .auth import (
    AssignmentUpdate,
    LoginRequest,
    current_user,
    demo_users,
    login,
    public_user,
    require_case_access,
    require_roles,
    role_label,
    team_snapshot,
    update_assignment,
)
from .intelligence import HANDOFF_BUCKETS, IntelligenceError, make_intelligence_service
from .memory import MemoryBackendError, make_memory_service


load_dotenv()

app = FastAPI(title="Handoff Memory API", version="0.2.0")
memory = make_memory_service()
intelligence = make_intelligence_service()

WATCH_TERMS = ("overnight", "3 am", "3am", "woke", "restless", "settled", "quiet room", "water", "medication")
PREFERENCE_TERMS = ("breakfast", "oatmeal", "orange juice", "preference", "avoid")
FAMILY_TERMS = ("family", "mira", "call", "callback", "update", "before 9")
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("DEMO_RATE_LIMIT_WINDOW_SECONDS", "600"))
RATE_LIMIT_API_REQUESTS = int(os.getenv("DEMO_RATE_LIMIT_API_REQUESTS", "240"))
RATE_LIMIT_MUTATION_REQUESTS = int(os.getenv("DEMO_RATE_LIMIT_MUTATION_REQUESTS", "60"))
API_REQUESTS: defaultdict[str, deque[float]] = defaultdict(deque)
MUTATION_REQUESTS: defaultdict[str, deque[float]] = defaultdict(deque)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_api(request: Request, call_next):
    if request.url.path.startswith("/v1/"):
        client = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        client = client or (request.client.host if request.client else "unknown")
        now = time.time()
        if too_many_requests(API_REQUESTS[client], now, RATE_LIMIT_API_REQUESTS):
            return JSONResponse({"detail": "rate_limited"}, status_code=429)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            mutation_key = f"{client}:{request.url.path}"
            if too_many_requests(MUTATION_REQUESTS[mutation_key], now, RATE_LIMIT_MUTATION_REQUESTS):
                return JSONResponse({"detail": "mutation_rate_limited"}, status_code=429)
    return await call_next(request)


class NoteCreate(BaseModel):
    type: str = Field(default="shift", min_length=2, max_length=32)
    text: str = Field(min_length=3, max_length=2000)
    source: str = Field(default="shift note", max_length=80)


class HandoffRequest(BaseModel):
    focus: str = Field(default="morning handoff", max_length=160)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=300)


class FeedbackRequest(BaseModel):
    memory_id: str | None = None
    feedback: str = Field(default="", max_length=1000)


@app.get("/v1/auth/demo-users")
def list_demo_users() -> dict[str, Any]:
    return {"users": demo_users()}


@app.post("/v1/auth/login")
def login_user(payload: LoginRequest) -> dict[str, Any]:
    return login(payload)


@app.get("/v1/auth/me")
def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"user": public_user(user)}


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "memory": memory.backend_status(), "intelligence": intelligence.status()}


@app.get("/v1/cases")
def list_cases(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"cases": visible_cases_for(user)}


@app.get("/v1/cases/{case_id}")
def get_case(case_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_case_access(user, case_id)
    try:
        return memory.get_case(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


@app.post("/v1/cases/{case_id}/notes")
def add_note(case_id: str, payload: NoteCreate, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"night_caregiver", "supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        case = memory.get_case(case_id)
        source = f"{role_label(user['role'])} note - {user['name']}"
        understanding = intelligence.analyze_note(case, payload.type, payload.text, source)
        result = memory.remember(case_id, payload.type, payload.text, source, understanding)
        return {"memory": result.item, "trace": result.trace, "understanding": understanding}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except IntelligenceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/v1/cases/{case_id}/handoff")
def generate_handoff(case_id: str, payload: HandoffRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"morning_lead", "supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        case = memory.get_case(case_id)
        recall_plan = intelligence.plan_recall(case, payload.focus)
        evidence_by_bucket, recalled, recall_traces = recall_for_plan(case_id, recall_plan)
        handoff = intelligence.write_handoff(case, payload.focus, evidence_by_bucket)
        verified_handoff = verify_handoff(handoff, recalled)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except IntelligenceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "handoff": verified_handoff,
        "sources": recalled,
        "trace": {
            "recall_plan": recall_plan,
            "recall_traces": recall_traces,
            "intelligence": intelligence.status(),
        },
    }


@app.post("/v1/cases/{case_id}/ask")
def ask_case(case_id: str, payload: AskRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"morning_lead", "supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        case = memory.get_case(case_id)
        recalled, trace = memory.recall(
            case_id,
            payload.question,
            limit=8,
            search_type="CHUNKS",
            intent={"bucket": None, "intent": "Answer a worker question from remembered notes."},
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except IntelligenceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    try:
        answer = intelligence.answer_question(case, payload.question, recalled)
    except IntelligenceError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"answer": answer, "sources": recalled, "trace": trace}


@app.post("/v1/cases/{case_id}/feedback")
def improve_memory(case_id: str, payload: FeedbackRequest, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        trace = memory.improve(case_id, payload.memory_id, payload.feedback)
        return {"trace": trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_or_memory_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.delete("/v1/cases/{case_id}/memories/{memory_id}")
def forget_memory(case_id: str, memory_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        trace = memory.forget(case_id, memory_id)
        return {"trace": trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_or_memory_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/v1/cases/{case_id}/trace")
def memory_trace(case_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        return {"traces": list(reversed(memory.traces(case_id)))}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


@app.get("/v1/cases/{case_id}/evidence")
def memory_evidence(case_id: str, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor", "demo_judge"})
    require_case_access(user, case_id)
    try:
        evidence = memory.evidence(case_id)
        evidence["intelligence"] = intelligence.status()
        return evidence
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


@app.get("/v1/team/assignments")
def get_assignments(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor", "demo_judge"})
    return team_snapshot(memory.list_cases())


@app.post("/v1/team/assignments")
def assign_shift(payload: AssignmentUpdate, user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor"})
    assignment = update_assignment(payload)
    return {"assignment": assignment, "team": team_snapshot(memory.list_cases())}


@app.post("/v1/demo/reset")
def reset_demo(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    require_roles(user, {"supervisor", "demo_judge"})
    try:
        return memory.reset()
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def visible_cases_for(user: dict[str, Any]) -> list[dict[str, Any]]:
    all_cases = memory.list_cases()
    if user["role"] in {"supervisor", "demo_judge"}:
        return all_cases
    allowed = set(public_user(user)["assigned_case_ids"])
    return [case for case in all_cases if case["id"] in allowed]


def recall_for_plan(
    case_id: str,
    recall_plan: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    evidence_by_bucket = {bucket: [] for bucket in HANDOFF_BUCKETS}
    recalled_by_id: dict[str, dict[str, Any]] = {}
    recall_traces = []
    for step in recall_plan:
        recalled, trace = memory.recall(
            case_id,
            step["query"],
            limit=step.get("top_k", 8),
            search_type=step.get("search_type"),
            intent=step,
        )
        recall_traces.append(trace)
        bucket = step.get("bucket")
        if bucket not in evidence_by_bucket:
            bucket = "review_with_supervisor"
        for item in recalled:
            target_bucket = bucket_for_item(item, bucket)
            if item["id"] in recalled_by_id:
                continue
            recalled_by_id[item["id"]] = item
            evidence_by_bucket[target_bucket].append(item)
    return evidence_by_bucket, list(recalled_by_id.values()), recall_traces


def bucket_for_item(item: dict[str, Any], fallback: str) -> str:
    understood = item.get("understanding", {}).get("handoff_bucket")
    if understood in HANDOFF_BUCKETS:
        return understood
    text = item.get("text", "").lower()
    typed = item.get("type")
    if typed == "task":
        if "before 9" in text or "callback" in text or ("call" in text and "family" in text):
            return "before_9"
        return "later_today"
    if typed in {"risk", "incident"} or contains_any(text, WATCH_TERMS):
        return "watch_today"
    if typed == "family" or contains_any(text, FAMILY_TERMS):
        return "before_9"
    if typed == "preference" or contains_any(text, PREFERENCE_TERMS):
        return "care_preferences"
    if typed == "review":
        return "review_with_supervisor"
    return fallback if fallback in HANDOFF_BUCKETS else "review_with_supervisor"


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def too_many_requests(bucket: deque[float], now: float, limit: int) -> bool:
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


def verify_handoff(handoff: dict[str, Any], sources: list[dict[str, Any]]) -> dict[str, Any]:
    source_by_id = {item["id"]: item for item in sources}
    summary = handoff.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        summary = "Morning handoff generated from verified remembered notes."
    verified = {
        "summary": summary,
        "safety_note": "This is a workflow handoff draft from remembered notes, not medical advice.",
        "writer": handoff.get("writer") or intelligence.status()["name"],
    }
    for bucket in HANDOFF_BUCKETS:
        verified_items = []
        for raw_item in handoff.get(bucket, []):
            if not isinstance(raw_item, dict):
                continue
            text = str(raw_item.get("text") or "").strip()
            source_ids = [source_id for source_id in raw_item.get("source_ids", []) if source_id in source_by_id]
            if not text:
                continue
            if not source_ids and text != "No verified source-backed note found.":
                continue
            verified_items.append(
                {
                    "text": text,
                    "source_ids": source_ids,
                    "source": source_by_id[source_ids[0]].get("source") if source_ids else None,
                    "important": any(source_by_id[source_id].get("important") for source_id in source_ids),
                }
            )
        if not verified_items:
            verified_items.append(
                {
                    "text": "No verified source-backed note found.",
                    "source_ids": [],
                    "source": None,
                    "important": False,
                }
            )
        verified[bucket] = verified_items[:3]
    return verified


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_spa(full_path: str) -> FileResponse:
        if full_path.startswith(("v1/", "healthz")):
            raise HTTPException(status_code=404, detail="not_found")
        target = FRONTEND_DIST / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(FRONTEND_DIST / "index.html")
