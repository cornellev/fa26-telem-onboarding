"""Check that everything for the workshop is installed and running.

    python scripts/check_setup.py

Each line is a pass (✓) or a fail (✗) with the one command that fixes it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

OK, BAD = "\033[32m✓\033[0m", "\033[31m✗\033[0m"
failures = 0


def report(passed: bool, what: str, fix: str = "") -> bool:
    global failures
    print(f"{OK if passed else BAD} {what}")
    if not passed:
        failures += 1
        print(f"    fix: {fix}")
    return passed


def main() -> None:
    v = sys.version_info
    report(v >= (3, 10), f"Python {v.major}.{v.minor} (need 3.10+)",
           "brew install python   (macOS) / sudo apt install python3   (WSL), then recreate .venv")

    try:
        import mcp, ollama, psycopg  # noqa: F401
    except ImportError as e:
        report(False, f"Python packages ({e.name} missing)",
               "source .venv/bin/activate && pip install -r requirements.txt")
        return finish()
    report(True, "Python packages installed")

    from config import DATABASE_URL, OLLAMA_MODEL

    start_ollama = ("brew services start ollama   (or open the Ollama app)" if sys.platform == "darwin"
                    else "ollama serve   (in a second terminal, and leave it running)")
    try:
        pulled = {m.model for m in ollama.list().models}
        report(True, "Ollama is running")
        report(OLLAMA_MODEL in pulled or f"{OLLAMA_MODEL}:latest" in pulled,
               f"Model {OLLAMA_MODEL} downloaded", f"ollama pull {OLLAMA_MODEL}")
    except Exception:
        report(False, "Ollama is running (localhost:11434)", start_ollama)

    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
            counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                      for t in ("runs", "laps", "samples")}
        report(True, "Postgres reachable as workshop_ro")
        expected = {"runs": 4, "laps": 20, "samples": 12037}
        report(counts == expected, f"Seed data loaded {counts}",
               "docker compose down -v && docker compose up -d")
    except psycopg.OperationalError as e:
        if "authentication failed" in str(e) or "does not exist" in str(e):
            report(False, "Postgres reachable as workshop_ro (old or unseeded volume)",
                   "docker compose down -v && docker compose up -d")
        else:
            report(False, "Postgres reachable as workshop_ro",
                   "docker compose up -d   (is Docker Desktop running? `docker ps` should work)")
    finish()


def finish() -> None:
    print("\nAll good, you're ready!" if not failures else f"\n{failures} problem(s) to fix.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
