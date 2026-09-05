import json
from pathlib import Path

try:
    from backend.authentication.auth_service import get_all_users
except ModuleNotFoundError:
    from authentication.auth_service import get_all_users

PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_DIR = PROJECT_ROOT / "backend" / "users"
USERS_PATH = USERS_DIR / "user_profiles.json"


def _ensure_dir():
    USERS_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path, default):
    if not path.exists():
        _ensure_dir()
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload):
    _ensure_dir()
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _public_user(user):
    return {k: v for k, v in user.items() if k not in {"password_hash", "password_salt"}}


def get_user_summary_list():
    users = get_all_users()
    return [_public_user(user) for user in users]


def get_user_profile(user_id: str):
    for user in get_all_users():
        if user.get("id") == user_id:
            return _public_user(user)
    return None


def get_user_profile_by_username(username: str, account_type: str | None = None):
    for user in get_all_users():
        if user.get("username", "").strip().lower() != (username or "").strip().lower():
            continue
        if account_type and user.get("account_type") != account_type:
            continue
        return _public_user(user)
    return None
