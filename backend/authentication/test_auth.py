import json
from pathlib import Path

import backend.authentication.auth_service as auth_service
import backend.server as server_module
from backend.fitness_data_service import append_daily_record, get_user_daily_history
from backend.progress_service import get_progress_summary
from backend.users_service import get_user_summary_list


def test_server_exposes_flask_app():
    assert hasattr(server_module, "app")


def test_handles_malformed_token_store(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    tokens_path = tmp_path / "tokens.json"
    users_path.write_text(json.dumps({"users": []}), encoding="utf-8")
    tokens_path.write_text(json.dumps({"tokens": {"tokens": []}}), encoding="utf-8")

    monkeypatch.setattr(auth_service, "USERS_PATH", users_path)
    monkeypatch.setattr(auth_service, "TOKENS_PATH", tokens_path)

    user = auth_service.create_user(
        name="Malformed Token",
        username="malformedtoken",
        password="securepass123",
        account_type="Login One",
    )
    token, session = auth_service.issue_token_for_user(user)
    assert token
    assert session["user_id"] == user["id"]


def test_create_login_logout_flow(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    tokens_path = tmp_path / "tokens.json"
    users_path.write_text(json.dumps({"users": []}), encoding="utf-8")
    tokens_path.write_text(json.dumps({"tokens": []}), encoding="utf-8")

    monkeypatch.setattr(auth_service, "USERS_PATH", users_path)
    monkeypatch.setattr(auth_service, "TOKENS_PATH", tokens_path)

    user = auth_service.create_user(
        name="Jordan Davis",
        username="jordand",
        password="securepass123",
        account_type="Login One",
    )
    assert user["username"] == "jordand"
    assert "password" not in user

    login_result = auth_service.login_user("jordand", "securepass123", "Login One")
    assert login_result["user"]["username"] == "jordand"
    assert login_result["token"]

    token = login_result["token"]
    verified = auth_service.verify_token(token)
    assert verified is not None
    assert verified["username"] == "jordand"

    assert auth_service.logout_user(token) is True
    assert auth_service.verify_token(token) is None


def test_user_profile_and_progress_summary(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    tokens_path = tmp_path / "tokens.json"
    users_path.write_text(json.dumps({"users": []}), encoding="utf-8")
    tokens_path.write_text(json.dumps({"tokens": []}), encoding="utf-8")

    monkeypatch.setattr(auth_service, "USERS_PATH", users_path)
    monkeypatch.setattr(auth_service, "TOKENS_PATH", tokens_path)

    user = auth_service.create_user(
        name="Progress User",
        username="progressuser",
        password="securepass123",
        account_type="Login Two",
    )

    record = {
        "date": "2026-09-01",
        "steps": 8200,
        "water": 7,
        "calories": 1900,
        "workout_completed": True,
        "goal_status": "On track",
    }
    appended = append_daily_record(user["id"], record)
    assert appended["steps"] == 8200

    history = get_user_daily_history(user["id"], days=7)
    assert len(history) >= 1

    summary = get_progress_summary(user["id"], days=7)
    assert summary["totals"]["steps"] >= 8200
    assert summary["workouts_completed"] >= 1

    users = get_user_summary_list()
    assert any(item["id"] == user["id"] for item in users)
