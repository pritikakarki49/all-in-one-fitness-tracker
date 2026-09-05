import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.authentication.auth_service import (
        create_user,
        issue_token_for_user,
        login_user,
        logout_user,
        verify_token,
    )
    from backend.fitness_data_service import append_daily_record, get_today_record, get_user_daily_history
    from backend.progress_service import get_progress_summary
    from backend.users_service import get_user_profile, get_user_summary_list
except ModuleNotFoundError:
    try:
        from authentication.auth_service import (
            create_user,
            issue_token_for_user,
            login_user,
            logout_user,
            verify_token,
        )
        from fitness_data_service import append_daily_record, get_today_record, get_user_daily_history
        from progress_service import get_progress_summary
        from users_service import get_user_profile, get_user_summary_list
    except ModuleNotFoundError:
        from .auth_service import (
            create_user,
            issue_token_for_user,
            login_user,
            logout_user,
            verify_token,
        )
        from ..fitness_data_service import append_daily_record, get_today_record, get_user_daily_history
        from ..progress_service import get_progress_summary
        from ..users_service import get_user_profile, get_user_summary_list

PROJECT_ROOT = Path(__file__).resolve().parents[2]
app = Flask(__name__, static_folder=str(PROJECT_ROOT), static_url_path="")
app.config["JSON_SORT_KEYS"] = False


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@app.route("/api/auth/<path:subpath>", methods=["OPTIONS"])
def handle_auth_options(subpath):
    return "", 204


def get_token_from_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    token_cookie = request.cookies.get("auth_token")
    if token_cookie:
        return token_cookie

    return None


def require_auth_user():
    token = get_token_from_request()
    user = verify_token(token)
    if user is None:
        return None
    return user


@app.route("/api/auth/signup", methods=["POST"])
def api_signup():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    account_type = payload.get("account_type") or payload.get("account") or "Login One"

    try:
        user = create_user(name=name, username=username, password=password, account_type=account_type)
        token, _ = issue_token_for_user(user)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    response = jsonify({
        "message": "Signup successful.",
        "user": user,
        "token": token,
    })
    response.set_cookie("auth_token", token, httponly=True, samesite="Lax", max_age=43200)
    return response


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    account_type = payload.get("account_type") or payload.get("account") or "Login One"

    try:
        result = login_user(username=username, password=password, account_type=account_type)
    except ValueError:
        return jsonify({"error": "Invalid username or password."}), 401

    token = result["token"]
    user = result["user"]
    response = jsonify({
        "message": "Login successful.",
        "user": user,
        "token": token,
    })
    response.set_cookie("auth_token", token, httponly=True, samesite="Lax", max_age=43200)
    return response


@app.route("/api/auth/check", methods=["GET"])
def api_check():
    token = get_token_from_request()
    user = verify_token(token)
    if user is None:
        return jsonify({"authenticated": False, "error": "Authentication required."}), 401
    return jsonify({"authenticated": True, "user": user})


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    token = get_token_from_request()
    success = logout_user(token)
    response = jsonify({"message": "Logged out successfully."} if success else {"error": "No active session found."})
    response.set_cookie("auth_token", "", expires=0, httponly=True, samesite="Lax")
    if not success:
        return response, 401
    return response


@app.route("/api/users", methods=["GET"])
def api_users():
    user = require_auth_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    return jsonify({"users": get_user_summary_list()})


@app.route("/api/users/me", methods=["GET"])
def api_current_user():
    user = require_auth_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    return jsonify({"user": get_user_profile(user["id"])})


@app.route("/api/users/<user_id>", methods=["GET"])
def api_user_by_id(user_id):
    auth_user = require_auth_user()
    if auth_user is None:
        return jsonify({"error": "Authentication required."}), 401
    user = get_user_profile(user_id)
    if user is None:
        return jsonify({"error": "User not found."}), 404
    return jsonify({"user": user})


@app.route("/api/fitness/records", methods=["GET"])
def api_fitness_records():
    user = require_auth_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    days = int((request.args.get("days") or 7))
    records = get_user_daily_history(user["id"], days=days)
    return jsonify({"records": records})


@app.route("/api/fitness/today", methods=["GET"])
def api_fitness_today():
    user = require_auth_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401
    return jsonify({"record": get_today_record(user["id"])})


@app.route("/api/fitness/record", methods=["POST"])
def api_fitness_record_post():
    user = require_auth_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401

    payload = request.get_json(silent=True) or {}
    try:
        record = append_daily_record(user["id"], payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": "Fitness record saved.", "record": record})


@app.route("/api/progress", methods=["GET"])
@app.route("/api/progress/summary", methods=["GET"])
def api_progress_summary():
    user = require_auth_user()
    if user is None:
        return jsonify({"error": "Authentication required."}), 401

    days = int((request.args.get("days") or 7))
    summary = get_progress_summary(user["id"], days=days)
    return jsonify(summary)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    if path in ("", "/"):
        return send_from_directory(PROJECT_ROOT, "homepage.html")

    # Serve frontend pages and other project files
    safe_path = (PROJECT_ROOT / path).resolve()

    if safe_path.is_file() and str(safe_path).startswith(str(PROJECT_ROOT)):
        return send_from_directory(PROJECT_ROOT, path)

    # Handle folder links such as /frontend/pages/tracker/
    if path.endswith("/"):
        index_file = safe_path / "index.html"
        if index_file.is_file() and str(index_file).startswith(str(PROJECT_ROOT)):
            return send_from_directory(safe_path, "index.html")

    return jsonify({"error": "Not found."}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.run(host="0.0.0.0", port=port, debug=False)
