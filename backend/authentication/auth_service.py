import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

AUTH_DIR = Path(__file__).resolve().parent
USERS_PATH = AUTH_DIR / "users.json"
TOKENS_PATH = AUTH_DIR / "tokens.json"

DEFAULT_USERS = {"users": []}
DEFAULT_TOKENS = {"tokens": []}


def _now_utc():
    return datetime.now(timezone.utc)


def _read_json(path: Path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize_account_type(value):
    if not value:
        return "Login One"
    mapping = {
        "account one": "Login One",
        "account two": "Login Two",
        "login one": "Login One",
        "login two": "Login Two",
        "one": "Login One",
        "two": "Login Two",
    }
    return mapping.get(str(value).strip().lower(), str(value).strip())


def _hash_password(password: str, salt: str | None = None):
    if salt is None:
        salt = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 200_000)
    return {"salt": salt, "hash": hash_bytes.hex()}


def _verify_password(password: str, stored_hash: str, salt: str):
    expected = _hash_password(password, salt)["hash"]
    return secrets.compare_digest(expected, stored_hash)


def _public_user(user):
    public = {k: v for k, v in user.items() if k not in {"password_hash", "password_salt"}}
    return public


def get_all_users():
    data = _read_json(USERS_PATH, DEFAULT_USERS)
    return data.get("users", [])


def get_all_tokens():
    data = _read_json(TOKENS_PATH, DEFAULT_TOKENS)
    tokens = data.get("tokens", [])
    if isinstance(tokens, dict):
        nested = tokens.get("tokens", [])
        return nested if isinstance(nested, list) else []
    if not isinstance(tokens, list):
        return []
    return tokens


def save_users(users):
    _write_json(USERS_PATH, {"users": users})


def save_tokens(tokens):
    if isinstance(tokens, dict):
        tokens = tokens.get("tokens", [])
    if not isinstance(tokens, list):
        tokens = []
    _write_json(TOKENS_PATH, {"tokens": tokens})


def find_user(username: str, account_type: str | None = None):
    users = get_all_users()
    username_clean = (username or "").strip()
    account_clean = _normalize_account_type(account_type)

    for user in users:
        matches_username = user.get("username", "").strip().lower() == username_clean.lower()
        if account_type is not None and account_clean:
            matches_account = user.get("account_type") == account_clean
            if matches_username and matches_account:
                return user
        elif matches_username:
            return user
    return None


def create_user(name: str, username: str, password: str, account_type: str):
    if not name or not username or not password:
        raise ValueError("Name, username, and password are required.")

    cleaned_name = name.strip()
    cleaned_username = username.strip()
    cleaned_account = _normalize_account_type(account_type)

    if len(cleaned_username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    if find_user(cleaned_username, cleaned_account):
        raise ValueError("This username is already in use for that account type.")

    password_data = _hash_password(password)
    user = {
        "id": secrets.token_hex(8),
        "name": cleaned_name,
        "username": cleaned_username,
        "account_type": cleaned_account,
        "password_hash": password_data["hash"],
        "password_salt": password_data["salt"],
        "created_at": _now_utc().isoformat(),
    }

    users = get_all_users()
    users.append(user)
    save_users(users)
    return _public_user(user)


def issue_token_for_user(user):
    token = secrets.token_urlsafe(32)
    expires_at = (_now_utc() + timedelta(hours=12)).isoformat()
    session = {
        "token": token,
        "user_id": user["id"],
        "username": user["username"],
        "account_type": user["account_type"],
        "created_at": _now_utc().isoformat(),
        "expires_at": expires_at,
    }

    tokens = get_all_tokens()
    tokens = [existing for existing in tokens if existing.get("user_id") != user["id"]]
    tokens.append(session)
    save_tokens(tokens)
    return token, session


def verify_token(token: str):
    if not token:
        return None

    tokens = get_all_tokens()
    now = _now_utc()
    valid_tokens = []
    matched = None

    for record in tokens:
        expires_at = record.get("expires_at")
        if expires_at:
            try:
                expires_dt = datetime.fromisoformat(expires_at)
                if expires_dt <= now:
                    continue
            except ValueError:
                continue
        if record.get("token") == token:
            matched = record
        valid_tokens.append(record)

    if matched is None:
        save_tokens(valid_tokens)
        return None

    users = get_all_users()
    user = next((item for item in users if item.get("id") == matched.get("user_id")), None)
    if user is None:
        save_tokens(valid_tokens)
        return None

    save_tokens(valid_tokens)
    return _public_user(user)


def logout_user(token: str):
    if not token:
        return False

    tokens = get_all_tokens()
    remaining = [record for record in tokens if record.get("token") != token]
    save_tokens(remaining)
    return True


def login_user(username: str, password: str, account_type: str | None = None):
    user = find_user(username, account_type)
    if not user:
        raise ValueError("Invalid username or password.")

    stored_hash = user.get("password_hash")
    salt = user.get("password_salt")
    if not stored_hash or not salt:
        raise ValueError("Invalid username or password.")

    if not _verify_password(password, stored_hash, salt):
        raise ValueError("Invalid username or password.")

    token, _ = issue_token_for_user(user)
    return {"token": token, "user": _public_user(user)}
