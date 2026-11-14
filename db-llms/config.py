"""Settings shared by chat.py, server.py and the scripts.

You shouldn't need to edit this. To change a setting, copy .env.example to .env
and edit that instead.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _load_env_file(path: Path) -> None:
    """Read KEY=value lines from .env into os.environ (real env vars win)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file(ROOT / ".env")

DB_PORT = os.environ.get("DB_PORT", "5432")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"postgresql://workshop_ro:workshop@localhost:{DB_PORT}/telemetry"
)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
