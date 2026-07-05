from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "local_memory.json"
GENERIC_FEEDBACK_TEXTS = {
    "prioritize this in the next handoff.",
    "supervisor marked this note important for future handoffs.",
}


class MemoryBackendError(RuntimeError):
    def __init__(self, message: str, communication: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.communication = communication


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def seed_state() -> dict[str, Any]:
    return {
        "cases": {
            "resident-avery": {
                "id": "resident-avery",
                "name": "Avery Johnson",
                "team": "Home care morning handoff",
                "shift": "Morning worker taking over",
                "summary": "A caregiver needs a fast, trustworthy handoff from notes left overnight.",
                "memories": [
                    {
                        "id": "mem-family-9am",
                        "type": "family",
                        "text": "Family asked for an update before 9 AM. Call Mira before breakfast if possible.",
                        "created_at": "2026-07-04T19:42:00+00:00",
                        "source": "night worker note",
                        "important": True,
                    },
                    {
                        "id": "mem-restless-med-change",
                        "type": "risk",
                        "text": "Avery was restless after the medication change and settled after water and a quiet room.",
                        "created_at": "2026-07-04T20:10:00+00:00",
                        "source": "overnight observation",
                        "important": False,
                    },
                    {
                        "id": "mem-oatmeal-breakfast",
                        "type": "preference",
                        "text": "Breakfast preference changed to oatmeal today. Avoid orange juice because it upset Avery yesterday.",
                        "created_at": "2026-07-04T21:05:00+00:00",
                        "source": "morning prep note",
                        "important": False,
                    },
                    {
                        "id": "mem-laundry-bag",
                        "type": "task",
                        "text": "Send the blue laundry bag with the family pickup after lunch.",
                        "created_at": "2026-07-04T22:18:00+00:00",
                        "source": "shift checklist",
                        "important": False,
                    },
                    {
                        "id": "mem-old-orange-juice",
                        "type": "review",
                        "text": "Old breakfast note says Avery prefers orange juice. Night shift flagged it as outdated.",
                        "created_at": "2026-07-04T23:12:00+00:00",
                        "source": "outdated preference note",
                        "important": False,
                    },
                ],
                "traces": [],
            },
            "resident-maya": {
                "id": "resident-maya",
                "name": "Maya Patel",
                "team": "Home care morning handoff",
                "shift": "Afternoon worker taking over",
                "summary": "Second case used to prove case memory does not leak across residents.",
                "memories": [
                    {
                        "id": "mem-maya-transport",
                        "type": "task",
                        "text": "Transportation confirmed for Maya's 2 PM appointment.",
                        "created_at": "2026-07-04T18:05:00+00:00",
                        "source": "coordinator note",
                        "important": True,
                    }
                ],
                "traces": [],
            },
        }
    }


@dataclass
class MemoryResult:
    item: dict[str, Any]
    trace: dict[str, Any]


class LocalMemoryService:
    """Local adapter with the same product lifecycle the Cognee adapter uses."""

    backend_name = "local-demo-memory"
    durable_memory = False
    phase = "phase-1-local"

    def __init__(self, path: Path = DATA_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save(seed_state())
        else:
            try:
                state = self._load()
                first_case = next(iter(state["cases"].values()))
                if "summary" not in first_case or "traces" not in first_case:
                    self._save(seed_state())
            except Exception:
                self._save(seed_state())

    def backend_status(self) -> dict[str, Any]:
        return {
            "name": self.backend_name,
            "phase": self.phase,
            "durable_memory": self.durable_memory,
            "configured": True,
            "strict": False,
            "message": "Local demo memory is active. Set MEMORY_BACKEND=cognee with Cognee credentials for Cloud memory.",
        }

    def reset(self) -> dict[str, Any]:
        state = seed_state()
        self._save(state)
        return {"status": "reset", "memory_backend": self.backend_name}

    def list_cases(self) -> list[dict[str, Any]]:
        state = self._load()
        cases = []
        for case in state["cases"].values():
            memories = self._visible_memories(case["memories"])
            cases.append(
                {
                    "id": case["id"],
                    "name": case["name"],
                    "team": case["team"],
                    "shift": case["shift"],
                    "summary": case["summary"],
                    "memory_count": len(memories),
                    "needs_review_count": sum(1 for item in memories if item["type"] == "review"),
                    "important_count": sum(1 for item in memories if item.get("important")),
                    "last_memory_at": memories[-1]["created_at"] if memories else None,
                }
            )
        return cases

    def get_case(self, case_id: str) -> dict[str, Any]:
        case = self._case(case_id)
        memories = sorted(self._visible_memories(case["memories"]), key=lambda item: item["created_at"], reverse=True)
        return {
            "id": case["id"],
            "name": case["name"],
            "team": case["team"],
            "shift": case["shift"],
            "summary": case["summary"],
            "guide": {
                "problem": "Morning staff needs the few things that changed overnight without rereading every note.",
                "promise": "Generate a handoff, ask a case question, then correct or remove bad notes.",
            },
            "memories": memories,
        }

    def remember(
        self,
        case_id: str,
        memory_type: str,
        text: str,
        source: str,
        understanding: dict[str, Any] | None = None,
    ) -> MemoryResult:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        item = self._new_item(memory_type, text, source, understanding)
        case["memories"].append(item)
        trace = self._trace(
            "remember",
            case_id,
            [item["id"]],
            time.perf_counter() - start,
            {
                "source": source,
                "understanding": understanding,
                "proof": "A worker added a note that future handoffs can retrieve.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return MemoryResult(item=item, trace=trace)

    def recall(
        self,
        case_id: str,
        query: str,
        limit: int = 8,
        search_type: str | None = None,
        intent: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        recalled = self._rank(self._visible_memories(case["memories"]), query, intent)[:limit]
        trace = self._trace(
            "recall",
            case_id,
            [item["id"] for item in recalled],
            time.perf_counter() - start,
            {
                "query": query,
                "intent": intent,
                "proof": "The handoff or answer was built from stored case notes.",
                "strategy": "local structured fallback; Cognee adapter uses Cloud recall when configured",
                "requested_search_type": search_type,
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return recalled, trace

    def improve(self, case_id: str, memory_id: str | None, feedback: str) -> dict[str, Any]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        touched: list[str] = []
        if memory_id:
            for item in case["memories"]:
                if item["id"] == memory_id:
                    item["important"] = True
                    touched.append(item["id"])
                    break
            if not touched:
                raise KeyError(memory_id)

        feedback_text = feedback.strip()
        if feedback_text and not self._is_generic_feedback(feedback_text):
            item = self._new_item("feedback", feedback_text, "supervisor review")
            item["important"] = True
            case["memories"].append(item)
            touched.append(item["id"])

        trace = self._trace(
            "improve",
            case_id,
            touched,
            time.perf_counter() - start,
            {
                "feedback": feedback_text,
                "proof": "A reviewer changed what future handoffs should prioritize.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return trace

    def forget(self, case_id: str, memory_id: str) -> dict[str, Any]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        before = len(case["memories"])
        case["memories"] = [item for item in case["memories"] if item["id"] != memory_id]
        if len(case["memories"]) == before:
            raise KeyError(memory_id)

        trace = self._trace(
            "forget",
            case_id,
            [memory_id],
            time.perf_counter() - start,
            {
                "reason": "user_removed_note",
                "proof": "A removed note should not appear in future handoffs or answers.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return trace

    def traces(self, case_id: str) -> list[dict[str, Any]]:
        return self._case(case_id)["traces"][-100:]

    def evidence(self, case_id: str) -> dict[str, Any]:
        case = self._case(case_id)
        traces = case["traces"]
        counts = Counter(trace["operation"] for trace in traces)
        visible_memories = self._visible_memories(case["memories"])
        return {
            "case_id": case_id,
            "case_name": case["name"],
            "backend": self.backend_status(),
            "active_memory_count": len(visible_memories),
            "operation_counts": dict(counts),
            "proof_steps": [
                {
                    "label": "Night note stored",
                    "operation": "remember",
                    "complete": counts["remember"] > 0 or len(case["memories"]) > 0,
                    "meaning": "A note exists outside the prompt and can be reused later.",
                },
                {
                    "label": "Morning handoff recalled notes",
                    "operation": "recall",
                    "complete": counts["recall"] > 0,
                    "meaning": "The handoff did not depend on the user pasting context again.",
                },
                {
                    "label": "Supervisor priority changed future output",
                    "operation": "improve",
                    "complete": counts["improve"] > 0,
                    "meaning": "Important information is promoted for later workers.",
                },
                {
                    "label": "Wrong note removed",
                    "operation": "forget",
                    "complete": counts["forget"] > 0,
                    "meaning": "Deleted or stale information stops participating in recall.",
                },
            ],
            "balance_policy": [
                "Use Cloud calls only on add note, generate handoff, ask question, mark important, and remove note.",
                "Do not spend Cognee balance on page refresh, UI navigation, or repeated polling.",
                "Use two small demo cases so judges see the full lifecycle without burning credits.",
            ],
            "communication_timeline": self._communication_timeline(traces),
            "recent_traces": list(reversed(traces[-12:])),
        }

    def _communication_timeline(self, traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
        timeline = []
        for trace in reversed(traces[-24:]):
            metadata = trace.get("metadata", {})
            calls = metadata.get("cognee_calls") or []
            if metadata.get("cognee_call"):
                calls = [metadata["cognee_call"], *calls]
            timeline.append(
                {
                    "trace_id": trace["id"],
                    "operation": trace["operation"],
                    "created_at": trace["created_at"],
                    "backend": trace["backend"],
                    "latency_ms": trace["latency_ms"],
                    "memory_ids": trace["memory_ids"],
                    "proof": metadata.get("proof"),
                    "query": metadata.get("query"),
                    "calls": calls,
                }
            )
        return timeline

    def _rank(
        self,
        memories: list[dict[str, Any]],
        query: str,
        intent: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query_lower = query.lower()
        terms = {part.lower() for part in re.split(r"[^a-zA-Z0-9]+", query) if len(part) > 2}
        bucket = (intent or {}).get("bucket")
        type_priority = {
            "family": 5,
            "risk": 4,
            "task": 3,
            "preference": 2,
            "review": 1,
            "feedback": 0,
        }

        def score(item: dict[str, Any]) -> tuple[int, str]:
            text = f"{item['type']} {item['text']} {item['source']}".lower()
            term_hits = sum(1 for term in terms if term in text)
            importance = 4 if item.get("important") else 0
            type_hit = 3 if item["type"] in query_lower else 0
            bucket_hit = 6 if bucket and item.get("understanding", {}).get("handoff_bucket") == bucket else 0
            priority = type_priority.get(item["type"], 0)
            return (term_hits + importance + type_hit + bucket_hit + priority, item["created_at"])

        return sorted(memories, key=score, reverse=True)

    def _visible_memories(self, memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [item for item in memories if not self._is_generic_feedback(item.get("text", ""))]

    def _is_generic_feedback(self, text: str) -> bool:
        return text.strip().lower() in GENERIC_FEEDBACK_TEXTS

    def _new_item(
        self,
        memory_type: str,
        text: str,
        source: str,
        understanding: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        item = {
            "id": f"mem-{uuid4().hex[:12]}",
            "type": memory_type,
            "text": text.strip(),
            "created_at": now_iso(),
            "source": source,
            "important": False,
        }
        if understanding:
            item["understanding"] = understanding
        return item

    def _trace(
        self,
        operation: str,
        case_id: str,
        memory_ids: list[str],
        elapsed_seconds: float,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": f"trace-{uuid4().hex[:12]}",
            "operation": operation,
            "backend": self.backend_name,
            "case_id": case_id,
            "memory_ids": memory_ids,
            "latency_ms": round(elapsed_seconds * 1000, 2),
            "metadata": metadata,
            "created_at": now_iso(),
        }

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, state: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _case(self, case_id: str) -> dict[str, Any]:
        return self._case_from_state(self._load(), case_id)

    def _case_from_state(self, state: dict[str, Any], case_id: str) -> dict[str, Any]:
        try:
            return state["cases"][case_id]
        except KeyError as exc:
            raise KeyError(case_id) from exc


class CogneeMemoryService(LocalMemoryService):
    backend_name = "cognee-cloud"
    durable_memory = True
    phase = "phase-2-cognee"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        path: Path = DATA_PATH,
        strict: bool = True,
        dataset_prefix: str = "handoff-demo",
    ) -> None:
        super().__init__(path)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.strict = strict
        self.dataset_prefix = dataset_prefix
        self.timeout = httpx.Timeout(40.0)

    def backend_status(self) -> dict[str, Any]:
        return {
            "name": self.backend_name,
            "phase": self.phase,
            "durable_memory": self.durable_memory,
            "configured": bool(self.base_url and self.api_key),
            "strict": self.strict,
            "dataset_prefix": self.dataset_prefix,
            "message": "Cognee Cloud is the memory layer. Local JSON is only the product workflow cache.",
        }

    def remember(
        self,
        case_id: str,
        memory_type: str,
        text: str,
        source: str,
        understanding: dict[str, Any] | None = None,
    ) -> MemoryResult:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        item = self._new_item(memory_type, text, source, understanding)
        dataset = self._dataset_for_memory(case_id, item["id"])
        item["cognee_dataset"] = dataset
        try:
            remote = self._remember_remote(case, item, dataset)
        except MemoryBackendError as exc:
            self._record_cognee_failure(
                state,
                case,
                "remember_failed",
                [item["id"]],
                start,
                exc,
                "Cognee remember failed before the note was accepted as durable memory.",
            )
            raise
        case["memories"].append(item)
        trace = self._trace(
            "remember",
            case_id,
            [item["id"]],
            time.perf_counter() - start,
            {
                "source": source,
                "cognee_dataset": dataset,
                "cognee_response": remote.get("response"),
                "cognee_calls": [remote],
                "understanding": understanding,
                "proof": "The note was sent to Cognee Cloud as durable memory.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return MemoryResult(item=item, trace=trace)

    def recall(
        self,
        case_id: str,
        query: str,
        limit: int = 8,
        search_type: str | None = None,
        intent: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        visible_memories = self._visible_memories(case["memories"])
        datasets = [item.get("cognee_dataset") or self._dataset_for_memory(case_id, item["id"]) for item in visible_memories]
        try:
            remote = self._recall_remote(query, datasets, limit, search_type)
        except MemoryBackendError as exc:
            self._record_cognee_failure(
                state,
                case,
                "recall_failed",
                [],
                start,
                exc,
                "Cognee recall failed before a verified handoff could be built.",
            )
            raise
        recalled = self._recall_from_cognee_response(remote, visible_memories, query, limit, intent)
        trace = self._trace(
            "recall",
            case_id,
            [item["id"] for item in recalled],
            time.perf_counter() - start,
            {
                "query": query,
                "intent": intent,
                "cognee_datasets": datasets,
                "cognee_response": remote.get("response"),
                "cognee_calls": [remote],
                "requested_search_type": search_type,
                "verified_source_ids": [item["id"] for item in recalled],
                "proof": "Cognee Cloud was queried for case-scoped memory before building the output.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return recalled, trace

    def improve(self, case_id: str, memory_id: str | None, feedback: str) -> dict[str, Any]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        touched: list[str] = []
        target_datasets: list[str] = []
        if memory_id:
            for item in case["memories"]:
                if item["id"] == memory_id:
                    item["important"] = True
                    touched.append(item["id"])
                    target_datasets.append(item.get("cognee_dataset") or self._dataset_for_memory(case_id, item["id"]))
                    break
            if not touched:
                raise KeyError(memory_id)

        feedback_text = feedback.strip()
        remote_remember: dict[str, Any] | None = None
        if feedback_text and not self._is_generic_feedback(feedback_text):
            feedback_item = self._new_item("feedback", feedback_text, "supervisor review")
            feedback_item["important"] = True
            feedback_dataset = self._dataset_for_memory(case_id, feedback_item["id"])
            feedback_item["cognee_dataset"] = feedback_dataset
            try:
                remote_remember = self._remember_remote(case, feedback_item, feedback_dataset)
            except MemoryBackendError as exc:
                self._record_cognee_failure(
                    state,
                    case,
                    "improve_failed",
                    touched,
                    start,
                    exc,
                    "Cognee remember failed while storing reviewer feedback.",
                )
                raise
            case["memories"].append(feedback_item)
            touched.append(feedback_item["id"])
            target_datasets.append(feedback_dataset)

        improve_text = feedback_text or "Supervisor marked this note important."
        try:
            remote_improve = self._improve_remote(target_datasets, improve_text) if target_datasets else {"calls": []}
        except MemoryBackendError as exc:
            self._record_cognee_failure(
                state,
                case,
                "improve_failed",
                touched,
                start,
                exc,
                "Cognee improve failed before reviewer priority could be stored in memory.",
            )
            raise
        cognee_calls = []
        if remote_remember:
            cognee_calls.append(remote_remember)
        cognee_calls.extend(remote_improve.get("calls", []))

        trace = self._trace(
            "improve",
            case_id,
            touched,
            time.perf_counter() - start,
            {
                "feedback": feedback_text,
                "cognee_datasets": target_datasets,
                "cognee_remember_response": remote_remember.get("response") if remote_remember else None,
                "cognee_improve_response": [call.get("response") for call in remote_improve.get("calls", [])],
                "cognee_calls": cognee_calls,
                "proof": "Reviewer priority was sent to Cognee without creating duplicate generic notes.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return trace

    def forget(self, case_id: str, memory_id: str) -> dict[str, Any]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        item = next((memory for memory in case["memories"] if memory["id"] == memory_id), None)
        if not item:
            raise KeyError(memory_id)
        dataset = item.get("cognee_dataset") or self._dataset_for_memory(case_id, memory_id)
        try:
            remote = self._forget_remote(dataset)
        except MemoryBackendError as exc:
            self._record_cognee_failure(
                state,
                case,
                "forget_failed",
                [memory_id],
                start,
                exc,
                "Cognee forget failed, so the note remains active.",
            )
            raise
        case["memories"] = [memory for memory in case["memories"] if memory["id"] != memory_id]
        trace = self._trace(
            "forget",
            case_id,
            [memory_id],
            time.perf_counter() - start,
            {
                "reason": "user_removed_note",
                "cognee_dataset": dataset,
                "cognee_response": remote.get("response"),
                "cognee_calls": [remote],
                "proof": "The Cognee dataset for this note was removed before the app stopped using it.",
            },
        )
        case["traces"].append(trace)
        self._save(state)
        return trace

    def reset(self) -> dict[str, Any]:
        state = seed_state()
        for case in state["cases"].values():
            for item in case["memories"]:
                dataset = self._dataset_for_memory(case["id"], item["id"])
                item["cognee_dataset"] = dataset
                remote = self._remember_remote(case, item, dataset)
                trace = self._trace(
                    "remember",
                    case["id"],
                    [item["id"]],
                    0,
                    {
                        "source": item["source"],
                        "cognee_dataset": dataset,
                        "cognee_response": remote.get("response"),
                        "cognee_calls": [remote],
                        "proof": "Seed note was written to Cognee for the live demo reset.",
                    },
                )
                case["traces"].append(trace)
        self._save(state)
        return {"status": "reset", "memory_backend": self.backend_name}

    def _remember_remote(self, case: dict[str, Any], item: dict[str, Any], dataset: str) -> dict[str, Any]:
        document = json.dumps(
            {
                "case_id": case["id"],
                "case_name": case["name"],
                "memory_id": item["id"],
                "type": item["type"],
                "text": item["text"],
                "source": item["source"],
                "important": item.get("important", False),
                "created_at": item["created_at"],
                "understanding": item.get("understanding"),
            },
            indent=2,
        )
        return self._post_multipart(
            "/api/v1/remember",
            data={
                "datasetName": dataset,
                "run_in_background": "false",
                "chunk_size": "1024",
                "chunks_per_batch": "4",
            },
            files=[("data", (f"{item['id']}.json", document, "application/json"))],
        )

    def _recall_remote(
        self,
        query: str,
        datasets: list[str],
        limit: int,
        search_type: str | None = None,
    ) -> dict[str, Any]:
        if not datasets:
            return {
                "provider": "cognee",
                "direction": "backend_to_memory",
                "method": "POST",
                "endpoint": "/api/v1/recall",
                "status": "skipped",
                "reason": "no_active_datasets",
                "request": {
                    "json": {
                        "searchType": search_type,
                        "datasets": [],
                        "query": query,
                        "topK": limit,
                        "onlyContext": True,
                        "includeReferences": True,
                        "scope": "auto",
                    }
                },
                "response": None,
            }
        return self._post_json(
            "/api/v1/recall",
            {
                "searchType": search_type,
                "datasets": datasets,
                "query": query,
                "systemPrompt": "Return source-grounded context. Preserve any memory_id fields from the stored JSON.",
                "topK": limit,
                "onlyContext": True,
                "verbose": False,
                "includeReferences": True,
                "scope": "auto",
                "contextProfile": "agent",
            },
        )

    def _recall_from_cognee_response(
        self,
        remote: dict[str, Any],
        visible_memories: list[dict[str, Any]],
        query: str,
        limit: int,
        intent: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        body = remote.get("response", {}).get("body")
        ordered_ids = self._extract_memory_ids(body, visible_memories)
        memories_by_id = {item["id"]: item for item in visible_memories}
        recalled = [memories_by_id[memory_id] for memory_id in ordered_ids if memory_id in memories_by_id]
        if recalled:
            return recalled[:limit]
        if truthy(os.getenv("COGNEE_ALLOW_LOCAL_RANK_FALLBACK", "false")):
            return self._rank(visible_memories, query, intent)[:limit]
        return []

    def _extract_memory_ids(self, value: Any, visible_memories: list[dict[str, Any]]) -> list[str]:
        text = json.dumps(value, default=str).lower()
        known_ids = [item["id"] for item in visible_memories]
        found: list[str] = []
        for memory_id in known_ids:
            if memory_id.lower() in text:
                found.append(memory_id)
        for item in visible_memories:
            if item["id"] in found:
                continue
            normalized = normalize_text(item["text"])
            if len(normalized) >= 32 and normalized[:80] in normalize_text(text):
                found.append(item["id"])
        return found

    def _improve_remote(self, datasets: list[str], feedback: str) -> dict[str, Any]:
        calls = []
        for dataset in datasets:
            calls.append(
                self._post_json(
                    "/api/v1/improve",
                    {
                        "datasetName": dataset,
                        "data": feedback,
                        "runInBackground": False,
                        "buildGlobalContextIndex": False,
                    },
                )
            )
        return {"calls": calls}

    def _forget_remote(self, dataset: str) -> dict[str, Any]:
        return self._post_json(
            "/api/v1/forget",
            {"dataset": dataset, "everything": False, "memoryOnly": False},
        )

    def _record_cognee_failure(
        self,
        state: dict[str, Any],
        case: dict[str, Any],
        operation: str,
        memory_ids: list[str],
        start: float,
        exc: MemoryBackendError,
        proof: str,
    ) -> None:
        metadata: dict[str, Any] = {
            "proof": proof,
            "error": str(exc),
        }
        if exc.communication:
            metadata["cognee_calls"] = [exc.communication]
        trace = self._trace(operation, case["id"], memory_ids, time.perf_counter() - start, metadata)
        case["traces"].append(trace)
        self._save(state)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, json=payload)

    def _post_multipart(
        self,
        path: str,
        data: dict[str, Any],
        files: list[tuple[str, tuple[str, str, str]]],
    ) -> dict[str, Any]:
        return self._request("POST", path, data=data, files=files)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Api-Key": self.api_key,
        }
        start = time.perf_counter()
        call: dict[str, Any] = {
            "provider": "cognee",
            "direction": "backend_to_memory",
            "method": method,
            "endpoint": path,
            "auth": {
                "authorization": "redacted",
                "x_api_key": "redacted",
            },
            "request": self._sanitize_request(kwargs),
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, headers=headers, **kwargs)
                call["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
                call["response"] = {
                    "status_code": response.status_code,
                    "ok": response.is_success,
                    "body": self._response_body(response),
                }
                call["status"] = "ok" if response.is_success else "error"
                response.raise_for_status()
                return call
        except Exception as exc:
            call["latency_ms"] = call.get("latency_ms") or round((time.perf_counter() - start) * 1000, 2)
            call["status"] = "error"
            call["error"] = str(exc)
            if self.strict:
                raise MemoryBackendError(f"Cognee call failed: {exc}", communication=call) from exc
            return call

    def _sanitize_request(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        request: dict[str, Any] = {}
        if "json" in kwargs:
            request["json"] = self._compact(kwargs["json"])
        if "data" in kwargs:
            request["form"] = self._compact(kwargs["data"])
        if "files" in kwargs:
            request["files"] = [self._sanitize_file(field, file_info) for field, file_info in kwargs["files"]]
        return request

    def _sanitize_file(self, field: str, file_info: tuple[str, str, str]) -> dict[str, Any]:
        filename, content, content_type = file_info
        return {
            "field": field,
            "filename": filename,
            "content_type": content_type,
            "content": self._compact(self._maybe_json(content)),
        }

    def _response_body(self, response: httpx.Response) -> Any:
        if not response.content:
            return None
        try:
            return self._compact(response.json())
        except ValueError:
            return self._compact(response.text)

    def _maybe_json(self, value: str) -> Any:
        try:
            return json.loads(value)
        except ValueError:
            return value

    def _compact(self, value: Any) -> Any:
        text = json.dumps(value, default=str)
        if len(text) <= 1200:
            return value
        return {"preview": text[:1200], "truncated": True}

    def _dataset_for_memory(self, case_id: str, memory_id: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", f"{case_id}-{memory_id}").strip("-")
        return f"{self.dataset_prefix}-{slug}"


def make_memory_service() -> LocalMemoryService:
    backend = os.getenv("MEMORY_BACKEND", "").strip().lower()
    base_url = os.getenv("COGNEE_BASE_URL", "").strip()
    api_key = os.getenv("COGNEE_API_KEY", "").strip()
    if backend == "cognee" or (base_url and api_key):
        strict = truthy(os.getenv("COGNEE_STRICT", "true"))
        dataset_prefix = os.getenv("COGNEE_DATASET_PREFIX", "handoff-demo")
        return CogneeMemoryService(base_url=base_url, api_key=api_key, strict=strict, dataset_prefix=dataset_prefix)
    return LocalMemoryService()
