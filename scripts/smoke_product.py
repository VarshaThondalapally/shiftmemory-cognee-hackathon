from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)

    reset = client.post("/v1/demo/reset")
    assert reset.status_code == 200, reset.text

    cases = client.get("/v1/cases").json()["cases"]
    assert any(case["id"] == "resident-avery" for case in cases)

    first = client.post(
        "/v1/cases/resident-avery/handoff",
        json={"focus": "morning handoff before 9 family risk breakfast"},
    )
    assert first.status_code == 200, first.text
    handoff = first.json()["handoff"]
    assert "Family asked" in handoff["before_9"][0]["text"]

    note = client.post(
        "/v1/cases/resident-avery/notes",
        json={
            "type": "family",
            "text": "Mira asked to be called again if Avery refuses breakfast.",
            "source": "night worker note",
        },
    )
    assert note.status_code == 200, note.text
    new_memory_id = note.json()["memory"]["id"]

    answer = client.post(
        "/v1/cases/resident-avery/ask",
        json={"question": "What should I tell the family this morning?"},
    )
    assert answer.status_code == 200, answer.text
    assert "family" in answer.json()["answer"].lower() or "mira" in answer.json()["answer"].lower()

    improve = client.post(
        "/v1/cases/resident-avery/feedback",
        json={"memory_id": new_memory_id, "feedback": "This family request should stay at the top."},
    )
    assert improve.status_code == 200, improve.text

    forget = client.delete("/v1/cases/resident-avery/memories/mem-old-orange-juice")
    assert forget.status_code == 200, forget.text

    after_forget = client.post(
        "/v1/cases/resident-avery/handoff",
        json={"focus": "breakfast preference orange juice"},
    )
    assert after_forget.status_code == 200, after_forget.text
    payload = after_forget.json()
    text = str(payload["handoff"]) + str(payload["sources"])
    assert "Old breakfast note says" not in text

    evidence = client.get("/v1/cases/resident-avery/evidence")
    assert evidence.status_code == 200, evidence.text
    counts = evidence.json()["operation_counts"]
    for operation in ("remember", "recall", "improve", "forget"):
        assert counts.get(operation, 0) >= 1, f"missing {operation}: {counts}"

    print("PASS: handoff memory demo lifecycle works end to end")


if __name__ == "__main__":
    main()
