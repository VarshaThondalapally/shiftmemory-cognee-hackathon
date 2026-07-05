from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "local_memory.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_state() -> dict[str, Any]:
    return {
        "cases": {
            "resident-avery": {
                "id": "resident-avery",
                "name": "Resident Avery",
                "team": "Home care handoff",
                "shift": "Morning shift",
                "memories": [
                    {
                        "id": "mem-family-call",
                        "type": "family",
                        "text": "Family asked for a morning callback before 10.",
                        "created_at": "2026-07-04T19:42:00+00:00",
                        "source": "night shift note",
                        "important": True,
                    },
                    {
                        "id": "mem-hydration",
                        "type": "risk",
                        "text": "Hydration was lower than usual. Check again at breakfast.",
                        "created_at": "2026-07-04T20:10:00+00:00",
                        "source": "evening observation",
                        "important": False,
                    },
                    {
                        "id": "mem-picture-cards",
                        "type": "preference",
                        "text": "Picture cards worked better than open-ended prompts.",
                        "created_at": "2026-07-04T21:05:00+00:00",
                        "source": "speech practice note",
                        "important": False,
                    },
                ],
                "traces": [],
            }
        }
    }


@dataclass
class MemoryResult:
    item: dict[str, Any]
    trace: dict[str, Any]


class LocalMemoryService:
    """Phase 1 memory adapter with the same lifecycle as Cognee."""

    backend_name = "local-phase1"

    def __init__(self, path: Path = DATA_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save(seed_state())

    def list_cases(self) -> list[dict[str, Any]]:
        state = self._load()
        cases = []
        for case in state["cases"].values():
            cases.append(
                {
                    "id": case["id"],
                    "name": case["name"],
                    "team": case["team"],
                    "shift": case["shift"],
                    "memory_count": len(case["memories"]),
                    "last_memory_at": case["memories"][-1]["created_at"] if case["memories"] else None,
                }
            )
        return cases

    def get_case(self, case_id: str) -> dict[str, Any]:
        case = self._case(case_id)
        return {
            "id": case["id"],
            "name": case["name"],
            "team": case["team"],
            "shift": case["shift"],
            "memories": sorted(case["memories"], key=lambda item: item["created_at"], reverse=True),
        }

    def remember(self, case_id: str, memory_type: str, text: str, source: str) -> MemoryResult:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        item = {
            "id": f"mem-{uuid4().hex[:12]}",
            "type": memory_type,
            "text": text.strip(),
            "created_at": now_iso(),
            "source": source,
            "important": False,
        }
        case["memories"].append(item)
        trace = self._trace("remember", case_id, [item["id"]], time.perf_counter() - start, {"source": source})
        case["traces"].append(trace)
        self._save(state)
        return MemoryResult(item=item, trace=trace)

    def recall(self, case_id: str, query: str, limit: int = 8) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        start = time.perf_counter()
        state = self._load()
        case = self._case_from_state(state, case_id)
        terms = {part.lower() for part in query.split() if len(part) > 2}

        def score(item: dict[str, Any]) -> tuple[int, str]:
            text = f"{item['type']} {item['text']} {item['source']}".lower()
            term_hits = sum(1 for term in terms if term in text)
            importance = 2 if item.get("important") else 0
            type_boost = 1 if item["type"] in query.lower() else 0
            return (term_hits + importance + type_boost, item["created_at"])

        ranked = sorted(case["memories"], key=score, reverse=True)
        recalled = ranked[:limit]
        trace = self._trace("recall", case_id, [item["id"] for item in recalled], time.perf_counter() - start, {"query": query})
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
        if feedback.strip():
            item = {
                "id": f"mem-{uuid4().hex[:12]}",
                "type": "feedback",
                "text": feedback.strip(),
                "created_at": now_iso(),
                "source": "supervisor feedback",
                "important": True,
            }
            case["memories"].append(item)
            touched.append(item["id"])
        trace = self._trace("improve", case_id, touched, time.perf_counter() - start, {"feedback": feedback})
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
        trace = self._trace("forget", case_id, [memory_id], time.perf_counter() - start, {"reason": "user_requested"})
        case["traces"].append(trace)
        self._save(state)
        return trace

    def traces(self, case_id: str) -> list[dict[str, Any]]:
        return self._case(case_id)["traces"][-80:]

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
