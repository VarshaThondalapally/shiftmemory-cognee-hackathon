from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)

    def auth_headers(user_id: str) -> dict[str, str]:
        response = client.post("/v1/auth/login", json={"user_id": user_id, "password": "demo"})
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    night_headers = auth_headers("night-demo")
    morning_headers = auth_headers("morning-demo")
    supervisor_headers = auth_headers("supervisor-demo")
    reviewer_headers = auth_headers("judge-demo")

    forbidden = client.post(
        "/v1/cases/resident-avery/handoff",
        json={"focus": "morning handoff"},
        headers=night_headers,
    )
    assert forbidden.status_code == 403, forbidden.text

    reset = client.post("/v1/demo/reset", headers=supervisor_headers)
    assert reset.status_code == 200, reset.text

    cases = client.get("/v1/cases", headers=morning_headers).json()["cases"]
    assert any(case["id"] == "resident-avery" for case in cases)

    first = client.post(
        "/v1/cases/resident-avery/handoff",
        json={"focus": "morning handoff before 9 family risk breakfast"},
        headers=morning_headers,
    )
    assert first.status_code == 200, first.text
    handoff = first.json()["handoff"]
    before_9_text = " ".join(item["text"] for item in handoff["before_9"])
    assert "Mira" in before_9_text or "family" in before_9_text.lower(), handoff

    note = client.post(
        "/v1/cases/resident-avery/notes",
        json={
            "type": "family",
            "text": "Mira asked to be called again if Avery refuses breakfast.",
            "source": "night worker note",
        },
        headers=night_headers,
    )
    assert note.status_code == 200, note.text
    new_memory_id = note.json()["memory"]["id"]

    overnight = client.post(
        "/v1/cases/resident-avery/notes",
        json={
            "type": "shift",
            "text": "Avery woke up twice after 3 AM but settled with water and a quiet room.",
            "source": "night worker note",
        },
        headers=night_headers,
    )
    assert overnight.status_code == 200, overnight.text

    answer = client.post(
        "/v1/cases/resident-avery/ask",
        json={"question": "What should I tell the family this morning?"},
        headers=morning_headers,
    )
    assert answer.status_code == 200, answer.text
    assert "family" in answer.json()["answer"].lower() or "mira" in answer.json()["answer"].lower()

    improve = client.post(
        "/v1/cases/resident-avery/feedback",
        json={"memory_id": new_memory_id, "feedback": "Prioritize this in the next handoff."},
        headers=supervisor_headers,
    )
    assert improve.status_code == 200, improve.text

    handoff_with_overnight = client.post(
        "/v1/cases/resident-avery/handoff",
        json={"focus": "morning handoff before 9 family risk breakfast"},
        headers=morning_headers,
    )
    assert handoff_with_overnight.status_code == 200, handoff_with_overnight.text
    handoff_payload = handoff_with_overnight.json()["handoff"]
    assert any("3 AM" in item["text"] for item in handoff_payload["watch_today"]), handoff_payload
    assert any("blue laundry bag" in item["text"] for item in handoff_payload["later_today"]), handoff_payload
    assert "Prioritize this in the next handoff" not in str(handoff_payload)

    forget = client.delete("/v1/cases/resident-avery/memories/mem-old-orange-juice", headers=supervisor_headers)
    assert forget.status_code == 200, forget.text

    after_forget = client.post(
        "/v1/cases/resident-avery/handoff",
        json={"focus": "breakfast preference orange juice"},
        headers=morning_headers,
    )
    assert after_forget.status_code == 200, after_forget.text
    payload = after_forget.json()
    text = str(payload["handoff"]) + str(payload["sources"])
    assert "Old breakfast note says" not in text

    evidence = client.get("/v1/cases/resident-avery/evidence", headers=reviewer_headers)
    assert evidence.status_code == 200, evidence.text
    evidence_payload = evidence.json()
    counts = evidence_payload["operation_counts"]
    for operation in ("remember", "recall", "improve", "forget"):
        assert counts.get(operation, 0) >= 1, f"missing {operation}: {counts}"
    assert evidence_payload["intelligence"]["name"], evidence_payload
    timeline = evidence_payload["communication_timeline"]
    assert any(item["operation"] == "recall" for item in timeline), timeline
    assert all("calls" in item for item in timeline), timeline

    print("PASS: handoff memory demo lifecycle works end to end")


if __name__ == "__main__":
    main()
