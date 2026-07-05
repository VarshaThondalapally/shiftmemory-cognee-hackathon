from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from copy import deepcopy
from typing import Any

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field


JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-before-production")
JWT_ISSUER = "handoff-memory-demo"
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "28800"))

USERS: dict[str, dict[str, Any]] = {
    "night-demo": {
        "id": "night-demo",
        "name": "Nia Brooks",
        "email": "night@demo.local",
        "role": "night_caregiver",
        "title": "Night caregiver",
        "password": "demo",
    },
    "morning-demo": {
        "id": "morning-demo",
        "name": "Omar Chen",
        "email": "morning@demo.local",
        "role": "morning_lead",
        "title": "Morning lead",
        "password": "demo",
    },
    "supervisor-demo": {
        "id": "supervisor-demo",
        "name": "Rosa Lee",
        "email": "supervisor@demo.local",
        "role": "supervisor",
        "title": "Care supervisor",
        "password": "demo",
    },
    "judge-demo": {
        "id": "judge-demo",
        "name": "Demo reviewer",
        "email": "reviewer@demo.local",
        "role": "demo_judge",
        "title": "Technical reviewer",
        "password": "demo",
    },
}

ASSIGNMENTS: dict[str, dict[str, Any]] = {
    "resident-avery": {
        "case_id": "resident-avery",
        "night_caregiver_id": "night-demo",
        "morning_lead_id": "morning-demo",
        "supervisor_id": "supervisor-demo",
        "shift_window": "Tonight 7 PM - tomorrow 7 AM",
    },
    "resident-maya": {
        "case_id": "resident-maya",
        "night_caregiver_id": None,
        "morning_lead_id": "morning-demo",
        "supervisor_id": "supervisor-demo",
        "shift_window": "Tomorrow 7 AM - 3 PM",
    },
}


class LoginRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=80)
    password: str = Field(default="demo", max_length=120)


class AssignmentUpdate(BaseModel):
    case_id: str = Field(min_length=3, max_length=80)
    night_caregiver_id: str | None = Field(default=None, max_length=80)
    morning_lead_id: str | None = Field(default=None, max_length=80)


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    safe = {key: value for key, value in user.items() if key != "password"}
    safe["assigned_case_ids"] = assigned_case_ids(user)
    safe["default_view"] = default_view_for_role(user["role"])
    return safe


def login(payload: LoginRequest) -> dict[str, Any]:
    user = USERS.get(payload.user_id)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = create_token({"sub": user["id"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


def demo_users() -> list[dict[str, Any]]:
    return [public_user(user) for user in USERS.values()]


def current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="missing_authorization")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="invalid_authorization")
    payload = decode_token(token)
    user = USERS.get(str(payload.get("sub")))
    if not user:
        raise HTTPException(status_code=401, detail="unknown_user")
    return user


def require_roles(user: dict[str, Any], allowed_roles: set[str]) -> None:
    if user["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail="role_not_allowed")


def assigned_case_ids(user: dict[str, Any]) -> list[str]:
    role = user["role"]
    if role in {"supervisor", "demo_judge"}:
        return list(ASSIGNMENTS.keys())
    if role == "night_caregiver":
        return [
            case_id
            for case_id, assignment in ASSIGNMENTS.items()
            if assignment.get("night_caregiver_id") == user["id"]
        ]
    if role == "morning_lead":
        return [
            case_id
            for case_id, assignment in ASSIGNMENTS.items()
            if assignment.get("morning_lead_id") == user["id"]
        ]
    return []


def can_access_case(user: dict[str, Any], case_id: str) -> bool:
    return case_id in assigned_case_ids(user)


def require_case_access(user: dict[str, Any], case_id: str) -> None:
    if not can_access_case(user, case_id):
        raise HTTPException(status_code=403, detail="case_not_assigned")


def role_label(role: str) -> str:
    return {
        "night_caregiver": "night caregiver",
        "morning_lead": "morning lead",
        "supervisor": "supervisor",
        "demo_judge": "demo reviewer",
    }.get(role, role.replace("_", " "))


def default_view_for_role(role: str) -> str:
    return {
        "night_caregiver": "notes",
        "morning_lead": "handoff",
        "supervisor": "review",
        "demo_judge": "proof",
    }.get(role, "notes")


def team_snapshot(cases: list[dict[str, Any]]) -> dict[str, Any]:
    case_by_id = {case["id"]: case for case in cases}
    assignments = []
    for case_id, assignment in ASSIGNMENTS.items():
        item = deepcopy(assignment)
        item["case_name"] = case_by_id.get(case_id, {}).get("name", case_id)
        item["night_caregiver"] = user_brief(item.get("night_caregiver_id"))
        item["morning_lead"] = user_brief(item.get("morning_lead_id"))
        item["supervisor"] = user_brief(item.get("supervisor_id"))
        assignments.append(item)
    return {
        "users": [public_user(user) for user in USERS.values() if user["role"] != "demo_judge"],
        "assignments": assignments,
    }


def update_assignment(payload: AssignmentUpdate) -> dict[str, Any]:
    if payload.case_id not in ASSIGNMENTS:
        raise HTTPException(status_code=404, detail="case_not_found")
    if payload.night_caregiver_id is not None:
        validate_user_role(payload.night_caregiver_id, "night_caregiver")
    if payload.morning_lead_id is not None:
        validate_user_role(payload.morning_lead_id, "morning_lead")
    assignment = ASSIGNMENTS[payload.case_id]
    assignment["night_caregiver_id"] = payload.night_caregiver_id
    assignment["morning_lead_id"] = payload.morning_lead_id
    return deepcopy(assignment)


def validate_user_role(user_id: str, expected_role: str) -> None:
    user = USERS.get(user_id)
    if not user or user["role"] != expected_role:
        raise HTTPException(status_code=400, detail=f"invalid_{expected_role}")


def user_brief(user_id: str | None) -> dict[str, Any] | None:
    if not user_id or user_id not in USERS:
        return None
    user = USERS[user_id]
    return {"id": user["id"], "name": user["name"], "role": user["role"], "title": user["title"]}


def create_token(payload: dict[str, Any]) -> str:
    now = int(time.time())
    claims = {**payload, "iss": JWT_ISSUER, "iat": now, "exp": now + JWT_TTL_SECONDS}
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{b64_json(header)}.{b64_json(claims)}"
    signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return f"{signing_input}.{b64(signature)}"


def decode_token(token: str) -> dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
        actual = b64_decode(encoded_signature)
        if not hmac.compare_digest(expected, actual):
            raise ValueError("bad_signature")
        payload = json.loads(b64_decode(encoded_payload))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid_token") from exc
    if payload.get("iss") != JWT_ISSUER or int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="expired_token")
    return payload


def b64_json(value: dict[str, Any]) -> str:
    return b64(json.dumps(value, separators=(",", ":")).encode("utf-8"))


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def b64_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))
