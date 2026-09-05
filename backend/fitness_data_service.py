import json
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FITNESS_DIR = PROJECT_ROOT / "backend" / "fitness-data"
DAILY_RECORDS_PATH = FITNESS_DIR / "daily-records.json"


def _ensure_dir():
    FITNESS_DIR.mkdir(parents=True, exist_ok=True)


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


def get_all_records():
    data = _read_json(DAILY_RECORDS_PATH, {"records": []})
    records = data.get("records", [])
    return records if isinstance(records, list) else []


def save_records(records):
    _write_json(DAILY_RECORDS_PATH, {"records": records})


def _normalize_record(user_id: str, payload: dict):
    date_value = (payload.get("date") or date.today().isoformat()).strip()
    try:
        date.fromisoformat(date_value)
    except ValueError as exc:  # pragma: no cover
        raise ValueError("Record date must be valid YYYY-MM-DD.") from exc

    normalized = {
        "user_id": user_id,
        "date": date_value,
        "steps": int(payload.get("steps", 0) or 0),
        "water": int(payload.get("water", 0) or 0),
        "calories": int(payload.get("calories", 0) or 0),
        "workout_minutes": int(payload.get("workout_minutes", payload.get("duration", 0)) or 0),
        "workout_type": (payload.get("workout_type") or payload.get("type") or "Workout").strip() or "Workout",
        "workout_completed": bool(payload.get("workout_completed", payload.get("workoutMinutes") or payload.get("duration", 0) > 0)),
        "goal_status": payload.get("goal_status") or "On track",
    }
    return normalized


def append_daily_record(user_id: str, payload: dict):
    if not user_id:
        raise ValueError("User ID is required.")
    record = _normalize_record(user_id, payload)
    records = get_all_records()
    merged = []
    replaced = False

    for item in records:
        if item.get("user_id") == user_id and item.get("date") == record["date"]:
            merged.append({**item, **record})
            replaced = True
        else:
            merged.append(item)

    if not replaced:
        merged.append(record)

    save_records(merged)
    return next(item for item in merged if item.get("user_id") == user_id and item.get("date") == record["date"])


def get_user_daily_history(user_id: str, days: int = 7):
    if not user_id:
        return []
    days = max(1, int(days or 7))
    start_date = date.today() - timedelta(days=days - 1)
    history = []
    for record in get_all_records():
        if record.get("user_id") != user_id:
            continue
        try:
            current_date = date.fromisoformat(record.get("date"))
        except ValueError:
            continue
        if current_date >= start_date:
            history.append(record)
    history.sort(key=lambda item: item.get("date", ""))
    return history


def get_today_record(user_id: str):
    for record in get_all_records():
        if record.get("user_id") == user_id and record.get("date") == date.today().isoformat():
            return record
    return None
