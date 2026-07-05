from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .memory import LocalMemoryService


app = FastAPI(title="ShiftMemory API", version="0.1.0")
memory = LocalMemoryService()

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
def healthz() -> dict[str, str]:
    return {"status": "ok", "memory_backend": memory.backend_name}


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


@app.post("/v1/cases/{case_id}/handoff")
def generate_handoff(case_id: str, payload: HandoffRequest) -> dict[str, Any]:
    try:
        recalled, trace = memory.recall(case_id, payload.focus)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")

    handoff = build_handoff(recalled)
    return {"handoff": handoff, "sources": recalled, "trace": trace}


@app.post("/v1/cases/{case_id}/ask")
def ask_case(case_id: str, payload: AskRequest) -> dict[str, Any]:
    try:
        recalled, trace = memory.recall(case_id, payload.question, limit=5)
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")

    if not recalled:
        answer = "I do not have enough notes on this case to answer that."
    else:
        top = recalled[0]
        answer = f"Most relevant note: {top['text']}"
    return {"answer": answer, "sources": recalled, "trace": trace}


@app.post("/v1/cases/{case_id}/feedback")
def improve_memory(case_id: str, payload: FeedbackRequest) -> dict[str, Any]:
    try:
        trace = memory.improve(case_id, payload.memory_id, payload.feedback)
        return {"trace": trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_or_memory_not_found")


@app.delete("/v1/cases/{case_id}/memories/{memory_id}")
def forget_memory(case_id: str, memory_id: str) -> dict[str, Any]:
    try:
        trace = memory.forget(case_id, memory_id)
        return {"trace": trace}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_or_memory_not_found")


@app.get("/v1/cases/{case_id}/trace")
def memory_trace(case_id: str) -> dict[str, Any]:
    try:
        return {"traces": list(reversed(memory.traces(case_id)))}
    except KeyError:
        raise HTTPException(status_code=404, detail="case_not_found")


def build_handoff(items: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {
        "start_here": [],
        "watch": [],
        "tasks": [],
        "preferences": [],
        "unknowns": [],
    }
    for item in items:
        text = item["text"]
        source = item["id"]
        typed = item["type"]
        entry = {"text": text, "source_ids": [source]}
        if typed in {"risk", "incident"}:
            buckets["watch"].append(entry)
        elif typed in {"task", "family"}:
            buckets["tasks"].append(entry)
        elif typed in {"preference", "feedback"}:
            buckets["preferences"].append(entry)
        else:
            buckets["start_here"].append(entry)

    if not buckets["start_here"]:
        buckets["start_here"].append({"text": "Review the case notes before starting the shift.", "source_ids": []})
    if not buckets["watch"]:
        buckets["unknowns"].append({"text": "No active risk note was found for this case.", "source_ids": []})

    return {
        "summary": "Morning handoff generated from the case notes.",
        "start_here": buckets["start_here"][:3],
        "watch": buckets["watch"][:3],
        "tasks": buckets["tasks"][:3],
        "preferences": buckets["preferences"][:3],
        "unknowns": buckets["unknowns"],
        "safety_note": "Workflow handoff only. Not medical advice.",
    }
