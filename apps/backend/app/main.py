from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .memory import MemoryBackendError, make_memory_service


load_dotenv()

app = FastAPI(title="Handoff Memory API", version="0.2.0")
memory = make_memory_service()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "memory": memory.backend_status()}


@app.get("/v1/cases")
def list_cases() -> dict[str, Any]:
    return {"cases": memory.list_cases()}


@app.get("/v1/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    try:
        return memory.get_case(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


@app.post("/v1/cases/{case_id}/notes")
def add_note(case_id: str, payload: NoteCreate) -> dict[str, Any]:
    try:
        result = memory.remember(case_id, payload.type, payload.text, payload.source)
        return {"memory": result.item, "trace": result.trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/v1/cases/{case_id}/handoff")
def generate_handoff(case_id: str, payload: HandoffRequest) -> dict[str, Any]:
    try:
        recalled, trace = memory.recall(case_id, payload.focus)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    handoff = build_handoff(recalled)
    return {"handoff": handoff, "sources": recalled, "trace": trace}


@app.post("/v1/cases/{case_id}/ask")
def ask_case(case_id: str, payload: AskRequest) -> dict[str, Any]:
    try:
        recalled, trace = memory.recall(case_id, payload.question, limit=5)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if not recalled:
        answer = "I do not have enough notes on this case to answer that."
    else:
        answer = answer_question(payload.question, recalled)
    return {"answer": answer, "sources": recalled, "trace": trace}


@app.post("/v1/cases/{case_id}/feedback")
def improve_memory(case_id: str, payload: FeedbackRequest) -> dict[str, Any]:
    try:
        trace = memory.improve(case_id, payload.memory_id, payload.feedback)
        return {"trace": trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_or_memory_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.delete("/v1/cases/{case_id}/memories/{memory_id}")
def forget_memory(case_id: str, memory_id: str) -> dict[str, Any]:
    try:
        trace = memory.forget(case_id, memory_id)
        return {"trace": trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_or_memory_not_found")
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/v1/cases/{case_id}/trace")
def memory_trace(case_id: str) -> dict[str, Any]:
    try:
        return {"traces": list(reversed(memory.traces(case_id)))}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


@app.get("/v1/cases/{case_id}/evidence")
def memory_evidence(case_id: str) -> dict[str, Any]:
    try:
        return memory.evidence(case_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


@app.post("/v1/demo/reset")
def reset_demo() -> dict[str, Any]:
    try:
        return memory.reset()
    except MemoryBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


def build_handoff(items: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "before_9": [],
        "watch_today": [],
        "care_preferences": [],
        "later_today": [],
        "review_with_supervisor": [],
    }
    for item in items:
        text = item["text"]
        source = item["id"]
        typed = item["type"]
        entry = {"text": text, "source_ids": [source], "source": item["source"], "important": item.get("important", False)}
        if typed in {"family", "feedback"} or "before 9" in text.lower():
            buckets["before_9"].append(entry)
        elif typed in {"risk", "incident"}:
            buckets["watch_today"].append(entry)
        elif typed in {"preference", "feedback"}:
            buckets["care_preferences"].append(entry)
        elif typed == "review":
            buckets["review_with_supervisor"].append(entry)
        elif typed == "task":
            buckets["later_today"].append(entry)
        else:
            buckets["review_with_supervisor"].append(entry)

    if not buckets["before_9"]:
        buckets["before_9"].append({"text": "No urgent before-9 item was found.", "source_ids": [], "source": None, "important": False})
    if not buckets["watch_today"]:
        buckets["watch_today"].append({"text": "No overnight watch item was found.", "source_ids": [], "source": None, "important": False})

    return {
        "summary": "Today's handoff was generated from remembered case notes.",
        "before_9": buckets["before_9"][:3],
        "watch_today": buckets["watch_today"][:3],
        "care_preferences": buckets["care_preferences"][:3],
        "later_today": buckets["later_today"][:3],
        "review_with_supervisor": buckets["review_with_supervisor"][:3],
        "safety_note": "This is a workflow handoff draft, not medical advice.",
    }


def answer_question(question: str, items: list[dict[str, Any]]) -> str:
    lower = question.lower()
    if "family" in lower or "call" in lower:
        family = [item for item in items if item["type"] in {"family", "feedback"}]
        if family:
            return f"Tell the family this first: {family[0]['text']}"
    if "breakfast" in lower or "food" in lower or "preference" in lower:
        preferences = [item for item in items if item["type"] == "preference"]
        if preferences:
            return f"Use the latest preference note: {preferences[0]['text']}"
    if "watch" in lower or "risk" in lower or "worry" in lower:
        risks = [item for item in items if item["type"] == "risk"]
        if risks:
            return f"Watch this today: {risks[0]['text']}"
    top = items[0]
    return f"Most relevant note: {top['text']}"
