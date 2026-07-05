from __future__ import annotations

import json
import os
import re
import time
from typing import Any

import httpx


HANDOFF_BUCKETS = (
    "before_9",
    "watch_today",
    "care_preferences",
    "later_today",
    "review_with_supervisor",
)

SEARCH_TYPES = {
    None,
    "GRAPH_COMPLETION",
    "RAG_COMPLETION",
    "HYBRID_COMPLETION",
    "TEMPORAL",
    "AGENTIC_COMPLETION",
    "FEELING_LUCKY",
}

WATCH_TERMS = (
    "overnight",
    "3 am",
    "3am",
    "woke",
    "wake",
    "restless",
    "settled",
    "quiet room",
    "water",
    "dizzy",
    "lower than usual",
    "check again",
    "after medication",
)
PREFERENCE_TERMS = ("breakfast", "oatmeal", "orange juice", "preference", "avoid")
FAMILY_TERMS = ("family", "mira", "call", "callback", "update")


class IntelligenceError(RuntimeError):
    pass


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


class LocalIntelligenceService:
    provider_name = "local-structured-fallback"
    configured = True
    strict = False

    def status(self) -> dict[str, Any]:
        return {
            "name": self.provider_name,
            "configured": self.configured,
            "strict": self.strict,
            "role": "Creates recall plans and source-grounded handoff drafts.",
            "message": "Local deterministic intelligence is active. Set LLM_PROVIDER=gemini with an API key for Gemini reasoning.",
        }

    def analyze_note(self, case: dict[str, Any], memory_type: str, text: str, source: str) -> dict[str, Any]:
        bucket = self._bucket_for(memory_type, text)
        return {
            "provider": self.provider_name,
            "kind": self._kind_for(memory_type, text),
            "summary": text.strip(),
            "entities": self._entities(case, text),
            "time_context": self._time_context(text),
            "handoff_bucket": bucket,
            "importance": "high" if bucket == "before_9" or memory_type in {"risk", "family"} else "medium",
            "source_quote": text.strip()[:240],
            "future_recall_intents": self._future_intents(bucket),
            "safety_flags": [],
            "confidence": 0.72,
        }

    def plan_recall(self, case: dict[str, Any], focus: str) -> list[dict[str, Any]]:
        return [
            {
                "bucket": "review_with_supervisor",
                "intent": "Find all source notes needed for a morning handoff: overnight changes, urgent family requests, changed preferences, later tasks, and stale notes.",
                "query": (
                    f"{case['name']} morning handoff overnight changes watch items family before 9 "
                    f"breakfast preferences oatmeal orange juice tasks laundry review stale notes {focus}"
                ),
                "search_type": "CHUNKS",
                "top_k": 12,
            },
        ]

    def write_handoff(
        self,
        case: dict[str, Any],
        focus: str,
        evidence_by_bucket: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        handoff = {
            "summary": "Morning handoff generated from verified remembered notes.",
            "before_9": self._bucket_items(evidence_by_bucket, "before_9"),
            "watch_today": self._bucket_items(evidence_by_bucket, "watch_today"),
            "care_preferences": self._bucket_items(evidence_by_bucket, "care_preferences"),
            "later_today": self._bucket_items(evidence_by_bucket, "later_today"),
            "review_with_supervisor": self._bucket_items(evidence_by_bucket, "review_with_supervisor"),
            "safety_note": "This is a workflow handoff draft from remembered notes, not medical advice.",
            "writer": self.provider_name,
        }
        return handoff

    def answer_question(self, case: dict[str, Any], question: str, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "No verified remembered note was found for that question."
        selected = sources[0]
        lower = question.lower()
        if "family" in lower or "call" in lower:
            selected = next((item for item in sources if item["type"] == "family" or contains_any(item["text"], FAMILY_TERMS)), selected)
        elif "breakfast" in lower or "food" in lower or "preference" in lower:
            selected = next(
                (item for item in sources if item["type"] == "preference" or contains_any(item["text"], PREFERENCE_TERMS)),
                selected,
            )
        elif "watch" in lower or "risk" in lower or "worry" in lower:
            selected = next((item for item in sources if item["type"] == "risk" or contains_any(item["text"], WATCH_TERMS)), selected)
        return f"{selected['text']} Source: {selected['id']}."

    def _bucket_items(self, evidence_by_bucket: dict[str, list[dict[str, Any]]], bucket: str) -> list[dict[str, Any]]:
        items = evidence_by_bucket.get(bucket, [])[:3]
        if not items:
            return [
                {
                    "text": "No verified source-backed note found.",
                    "source_ids": [],
                    "source": None,
                    "important": False,
                }
            ]
        return [
            {
                "text": item["text"],
                "source_ids": [item["id"]],
                "source": item.get("source"),
                "important": bool(item.get("important")),
            }
            for item in items
        ]

    def _bucket_for(self, memory_type: str, text: str) -> str:
        lower = text.lower()
        if memory_type == "task":
            if "before 9" in lower or "callback" in lower or ("call" in lower and "family" in lower):
                return "before_9"
            return "later_today"
        if memory_type in {"risk", "incident"} or contains_any(lower, WATCH_TERMS):
            return "watch_today"
        if memory_type == "family" or "before 9" in lower or contains_any(lower, FAMILY_TERMS):
            return "before_9"
        if memory_type == "preference" or contains_any(lower, PREFERENCE_TERMS):
            return "care_preferences"
        if memory_type == "review":
            return "review_with_supervisor"
        return "review_with_supervisor"

    def _kind_for(self, memory_type: str, text: str) -> str:
        return {
            "family": "family_request",
            "risk": "watch_item",
            "task": "open_task",
            "preference": "care_preference",
            "review": "needs_review",
            "feedback": "reviewer_feedback",
        }.get(memory_type, "shift_note")

    def _entities(self, case: dict[str, Any], text: str) -> list[str]:
        entities = [case.get("name", "resident")]
        for name in ("Mira", "family", "Avery", "Maya"):
            if name.lower() in text.lower() and name not in entities:
                entities.append(name)
        return entities

    def _time_context(self, text: str) -> str:
        lower = text.lower()
        if "3 am" in lower or "3am" in lower:
            return "after 3 AM"
        if "before 9" in lower:
            return "before 9 AM"
        if "after lunch" in lower:
            return "after lunch"
        if "overnight" in lower:
            return "overnight"
        return "unspecified"

    def _future_intents(self, bucket: str) -> list[str]:
        return {
            "before_9": ["urgent family requests", "time-sensitive morning tasks"],
            "watch_today": ["overnight changes", "morning watch items", "comfort actions that worked"],
            "care_preferences": ["changed preferences", "outdated instructions"],
            "later_today": ["unresolved practical tasks", "later today checklist"],
            "review_with_supervisor": ["conflicts", "stale notes", "items needing review"],
        }[bucket]


class GeminiIntelligenceService(LocalIntelligenceService):
    provider_name = "gemini"
    configured = True

    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest", strict: bool = True) -> None:
        self.api_key = api_key
        self.model = model
        self.strict = strict
        self.timeout = httpx.Timeout(35.0)

    def status(self) -> dict[str, Any]:
        return {
            "name": self.provider_name,
            "model": self.model,
            "configured": bool(self.api_key),
            "strict": self.strict,
            "role": "Understands notes, creates recall plans, and writes source-grounded handoffs.",
            "message": "Gemini is active as the reasoning layer. Cognee remains the memory layer.",
        }

    def analyze_note(self, case: dict[str, Any], memory_type: str, text: str, source: str) -> dict[str, Any]:
        prompt = f"""
You are the reasoning layer for a caregiver shift-handoff product.
Extract structured meaning from a single note. Do not give advice.
Return JSON only with:
kind, summary, entities, time_context, handoff_bucket, importance, source_quote,
future_recall_intents, safety_flags, confidence.

Allowed handoff_bucket values: {list(HANDOFF_BUCKETS)}
Allowed importance values: low, medium, high.

Case:
{json.dumps(self._case_brief(case), indent=2)}

Note:
{json.dumps({"type": memory_type, "text": text, "source": source}, indent=2)}
"""
        data = self._generate_json(prompt, self._fallback_analyze(case, memory_type, text, source))
        data["provider"] = self.provider_name
        return self._normalize_understanding(data, case, memory_type, text, source)

    def plan_recall(self, case: dict[str, Any], focus: str) -> list[dict[str, Any]]:
        prompt = f"""
You are planning memory retrieval for a caregiver morning handoff.
Create 4 to 6 recall queries for Cognee. Return a JSON array only.
Each item must have: bucket, intent, query, search_type, top_k.

Use Cognee search types only from:
GRAPH_COMPLETION, RAG_COMPLETION, HYBRID_COMPLETION, TEMPORAL, AGENTIC_COMPLETION, FEELING_LUCKY, or null.

Cover overnight changes, family/time-sensitive requests, changed preferences,
later practical tasks, and review/conflicts.

Case:
{json.dumps(self._case_brief(case), indent=2)}

Focus:
{focus}
"""
        fallback = super().plan_recall(case, focus)
        if truthy(os.getenv("COGNEE_FAST_DEMO_RECALL", "true")):
            return fallback
        data = self._generate_json(prompt, fallback)
        if not isinstance(data, list):
            data = fallback
        return self._normalize_plan(data, fallback)

    def write_handoff(
        self,
        case: dict[str, Any],
        focus: str,
        evidence_by_bucket: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        prompt = f"""
You write concise caregiver workflow handoffs.
Use only the evidence provided. Do not add facts, warnings, diagnosis, or medical advice.
Every non-empty item must cite source_ids that exist in the evidence.
Return JSON only with:
summary, before_9, watch_today, care_preferences, later_today, review_with_supervisor, safety_note.
Each bucket is an array of objects: text, source_ids.
If a bucket has no evidence, write exactly: "No verified source-backed note found." with source_ids [].

Case:
{json.dumps(self._case_brief(case), indent=2)}

Focus:
{focus}

Evidence:
{json.dumps(self._evidence_brief(evidence_by_bucket), indent=2)}
"""
        fallback = super().write_handoff(case, focus, evidence_by_bucket)
        data = self._generate_json(prompt, fallback)
        if not isinstance(data, dict):
            data = fallback
        data["writer"] = self.provider_name
        return data

    def answer_question(self, case: dict[str, Any], question: str, sources: list[dict[str, Any]]) -> str:
        if not sources:
            return "No verified remembered note was found for that question."
        prompt = f"""
Answer the worker's question using only the source notes below.
Be concise. Include source ids inline at the end.
If the sources do not answer it, say no verified remembered note was found.
Do not give medical advice.

Case:
{json.dumps(self._case_brief(case), indent=2)}

Question:
{question}

Sources:
{json.dumps([self._source_brief(item) for item in sources], indent=2)}
"""
        data = self._generate_text(prompt)
        return data or super().answer_question(case, question, sources)

    def _fallback_analyze(self, case: dict[str, Any], memory_type: str, text: str, source: str) -> dict[str, Any]:
        return super().analyze_note(case, memory_type, text, source)

    def _generate_json(self, prompt: str, fallback: Any) -> Any:
        try:
            text = self._call_gemini(prompt, json_mode=True)
            return parse_json(text)
        except Exception as exc:
            if self.strict:
                raise IntelligenceError(f"Gemini call failed: {self._redact_error(exc)}") from exc
            return fallback

    def _generate_text(self, prompt: str) -> str:
        try:
            return self._call_gemini(prompt, json_mode=False).strip()
        except Exception as exc:
            if self.strict:
                raise IntelligenceError(f"Gemini call failed: {self._redact_error(exc)}") from exc
            return ""

    def _call_gemini(self, prompt: str, json_mode: bool) -> str:
        model_path = self.model if self.model.startswith("models/") else f"models/{self.model}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent"
        generation_config: dict[str, Any] = {"temperature": 0.1}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }
        start = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, params={"key": self.api_key}, json=payload)
            response.raise_for_status()
        body = response.json()
        try:
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            raise IntelligenceError(f"Gemini returned no text after {elapsed} ms") from exc

    def _redact_error(self, exc: Exception) -> str:
        return re.sub(r"key=[^'\"\\s]+", "key=redacted", str(exc))

    def _normalize_understanding(
        self,
        data: dict[str, Any],
        case: dict[str, Any],
        memory_type: str,
        text: str,
        source: str,
    ) -> dict[str, Any]:
        fallback = self._fallback_analyze(case, memory_type, text, source)
        normalized = {**fallback, **data}
        if normalized.get("handoff_bucket") not in HANDOFF_BUCKETS:
            normalized["handoff_bucket"] = fallback["handoff_bucket"]
        if normalized.get("importance") not in {"low", "medium", "high"}:
            normalized["importance"] = fallback["importance"]
        normalized["future_recall_intents"] = ensure_string_list(normalized.get("future_recall_intents"), fallback["future_recall_intents"])
        normalized["entities"] = ensure_string_list(normalized.get("entities"), fallback["entities"])
        normalized["safety_flags"] = ensure_string_list(normalized.get("safety_flags"), [])
        normalized["confidence"] = clamp_float(normalized.get("confidence"), fallback["confidence"])
        normalized["source_quote"] = str(normalized.get("source_quote") or text).strip()[:260]
        normalized["provider"] = self.provider_name
        return normalized

    def _normalize_plan(self, data: list[Any], fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        fallback_by_bucket = {item["bucket"]: item for item in fallback}
        for raw in data:
            if not isinstance(raw, dict):
                continue
            bucket = raw.get("bucket")
            if bucket not in HANDOFF_BUCKETS:
                continue
            backup = fallback_by_bucket.get(bucket, fallback[0])
            search_type = raw.get("search_type")
            if search_type not in SEARCH_TYPES or search_type in {None, "TEMPORAL", "HYBRID_COMPLETION"}:
                search_type = backup["search_type"]
            normalized.append(
                {
                    "bucket": bucket,
                    "intent": str(raw.get("intent") or backup["intent"])[:240],
                    "query": str(raw.get("query") or backup["query"])[:500],
                    "search_type": search_type,
                    "top_k": max(3, min(int(raw.get("top_k") or backup["top_k"]), 12)),
                }
            )
        seen = {item["bucket"] for item in normalized}
        normalized.extend(item for item in fallback if item["bucket"] not in seen)
        return normalized[:6]

    def _case_brief(self, case: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": case.get("id"),
            "name": case.get("name"),
            "team": case.get("team"),
            "shift": case.get("shift"),
            "summary": case.get("summary"),
        }

    def _evidence_brief(self, evidence_by_bucket: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        return {
            bucket: [self._source_brief(item) for item in items[:6]]
            for bucket, items in evidence_by_bucket.items()
        }

    def _source_brief(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "type": item["type"],
            "text": item["text"],
            "source": item.get("source"),
            "important": item.get("important", False),
            "understanding": item.get("understanding"),
        }


def parse_json(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", stripped, re.DOTALL)
    if not match:
        raise ValueError("no JSON object found")
    return json.loads(match.group(1))


def ensure_string_list(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned[:10]
    return fallback


def clamp_float(value: Any, fallback: float) -> float:
    try:
        return max(0.0, min(float(value), 1.0))
    except (TypeError, ValueError):
        return fallback


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def make_intelligence_service() -> LocalIntelligenceService:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("LLM_API_KEY", "").strip()
    if provider == "gemini" or (provider == "" and api_key):
        model = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()
        strict = truthy(os.getenv("LLM_STRICT", "true"))
        return GeminiIntelligenceService(api_key=api_key, model=model, strict=strict)
    return LocalIntelligenceService()
