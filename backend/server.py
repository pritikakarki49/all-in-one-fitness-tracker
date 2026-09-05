import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.authentication.app import app
except ModuleNotFoundError:
    from authentication.app import app

HOST = "0.0.0.0"
PORT = 3000


if __name__ == "__main__":
    port = int(os.environ.get("PORT", PORT))
    print(f"Server running on http://localhost:{port}")
    app.run(host=HOST, port=port, debug=False)
