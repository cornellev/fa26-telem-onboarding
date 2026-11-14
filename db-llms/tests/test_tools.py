"""Every tool vs known seed values, no LLM. Needs the DB up:  pip install pytest && pytest
Task/stretch tools are tested from the solution (server.py's are unfinished on purpose)."""

import runpy
import sys
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATABASE_URL, ROOT  # noqa: E402
import server  # noqa: E402

solution = runpy.run_path(str(ROOT / "solutions" / "server_solution.py"))


def test_seed_row_counts():
    with psycopg.connect(DATABASE_URL) as conn:
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                  for t in ("runs", "laps", "samples", "pit_wall_notes")}
    assert counts == {"runs": 4, "laps": 20, "samples": 12037, "pit_wall_notes": 1}


def test_db_user_is_read_only():
    with psycopg.connect(DATABASE_URL) as conn, pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
        conn.execute("DELETE FROM runs")


@pytest.mark.parametrize("module", [vars(server), solution], ids=["server", "solution"])
def test_list_runs(module):
    runs = module["list_runs"]()
    assert [r["run_id"] for r in runs] == [1, 2, 3, 4]
    assert runs[2] == {
        "run_id": 3, "run_date": "2026-10-24", "track": "Indianapolis Motor Speedway",
        "run_type": "competition", "driver": "Driver C", "laps": 5,
        "notes": "Pit stop after lap 4 to let the battery cool down.",
    }


@pytest.mark.parametrize("module", [vars(server), solution], ids=["server", "solution"])
def test_get_lap_summary(module):
    assert module["get_lap_summary"](2, 3) == {
        "run_id": 2, "lap_number": 3, "lap_time_s": 56.52, "max_speed_mps": 19.43,
        "avg_speed_mps": 15.93, "max_battery_temp_c": 32.73, "avg_throttle_pct": 54.97,
    }


def test_get_lap_summary_errors_are_text():
    assert server.get_lap_summary(2, 9) == "No lap 9 in run 2; run 2 has laps 1 to 5."
    assert server.get_lap_summary(7, 1) == "No run 7. Valid run_ids: [1, 2, 3, 4]"


def test_get_fastest_laps():
    assert solution["get_fastest_laps"]() == [
        {"run_id": 2, "lap_number": 5, "driver": "Driver B", "lap_time_s": 54.11},
        {"run_id": 2, "lap_number": 2, "driver": "Driver B", "lap_time_s": 54.26},
        {"run_id": 2, "lap_number": 4, "driver": "Driver B", "lap_time_s": 56.08},
    ]
    assert len(solution["get_fastest_laps"](limit=100)) == 20


def test_get_signal_peak_finds_battery_spike():
    assert solution["get_signal_peak"](3, "battery_temp_c") == {
        "run_id": 3, "signal": "battery_temp_c", "units": "degrees C", "lap_number": 4, "peak": 50.3}
    assert solution["get_signal_peak"](2, "speed_mps")["peak"] == 20.29


def test_get_signal_peak_errors_are_text():
    assert solution["get_signal_peak"](1, "speed; DROP TABLE runs").startswith("Unknown signal")
    assert solution["get_signal_peak"](9, "speed_mps") == "No run 9. Use list_runs to see valid run_ids."


def test_hidden_table_is_discoverable():
    tables = [t["table_name"] for t in solution["list_tables"]()]
    assert tables == ["laps", "pit_wall_notes", "runs", "samples"]
    table = solution["describe_table"]("pit_wall_notes")
    assert [c["column_name"] for c in table["columns"]] == ["note_id", "run_id", "message"]
    assert "REGEN" in table["first_rows"][0]["message"]
    assert solution["describe_table"]("nope; DROP TABLE runs").startswith("No table named")
    rows = solution["run_sql"]("SELECT message FROM pit_wall_notes")
    assert "REGEN" in rows[0]["message"]


def test_run_sql_guards():
    assert solution["run_sql"]("DELETE FROM runs") == "Only a single SELECT statement is allowed."
    assert solution["run_sql"]("SELECT 1; SELECT 2") == "Only a single SELECT statement is allowed."
    assert solution["run_sql"]("SELECT nope FROM runs").startswith("SQL error:")
    assert len(solution["run_sql"]("SELECT * FROM samples")) == 20
