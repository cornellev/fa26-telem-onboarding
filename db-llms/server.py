"""MCP server: the tools the model can call. THIS IS THE FILE YOU EDIT.

chat.py starts this file for you, so just save your changes and rerun chat.py.

The model only sees each tool's NAME, DOCSTRING and TYPE HINTS, never the code,
so the docstring is the interface. The model only *proposes* a call; chat.py runs
the function and sends the result back.

Rules: parameterized SQL (%s), small outputs (2 decimals, max 20 rows), and
return errors as text so the model can fix its call.
"""

from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from mcp.server.fastmcp import FastMCP

from config import DATABASE_URL

mcp = FastMCP("cev-telemetry", log_level="WARNING")

# Columns of the samples table that tools may read, with their units.
SIGNALS = {
    "speed_mps": "m/s",
    "throttle_pct": "%",
    "brake_pct": "%",
    "battery_v": "V",
    "battery_temp_c": "degrees C",
    "motor_current_a": "A",
}


def query(sql: str, params=()) -> list[dict]:
    """Run one SELECT as the read-only workshop user. Returns at most 20 rows."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        rows = conn.execute(sql, params).fetchmany(20)
    return [{key: clean(value) for key, value in row.items()} for row in rows]


def clean(value):
    """Make a database value small and JSON-friendly."""
    if isinstance(value, (Decimal, float)):
        return round(float(value), 2)
    if hasattr(value, "isoformat"):  # dates and times
        return value.isoformat()
    return value


def lap_not_found(run_id: int, lap_number: int) -> str:
    """Error text for a run/lap that doesn't exist, listing what does."""
    laps = query("SELECT lap_number FROM laps WHERE run_id = %s ORDER BY lap_number", (run_id,))
    if not laps:
        runs = query("SELECT run_id FROM runs ORDER BY run_id")
        return f"No run {run_id}. Valid run_ids: {[r['run_id'] for r in runs]}"
    numbers = [lap["lap_number"] for lap in laps]
    return f"No lap {lap_number} in run {run_id}; run {run_id} has laps {numbers[0]} to {numbers[-1]}."


# ---------------------------------------------------------------------------
# Working tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_runs() -> list[dict]:
    """List every run in the database: run_id, date, track, run_type (test or
    competition), driver, number of laps and notes. Use this first to find run_ids."""
    return query("""
        SELECT r.run_id, r.run_date, r.track, r.run_type, r.driver,
               COUNT(l.lap_id) AS laps, r.notes
        FROM runs r
        LEFT JOIN laps l ON l.run_id = r.run_id
        GROUP BY r.run_id
        ORDER BY r.run_id
    """)


@mcp.tool()
def get_lap_summary(run_id: int, lap_number: int) -> dict | str:
    """Summarize one lap of one run: lap time (seconds), max and average speed (m/s),
    max battery temperature (degrees C) and average throttle (%).

    Args:
        run_id: the run's id, e.g. 2 (see list_runs).
        lap_number: lap within that run, starting at 1.
    """
    rows = query("""
        SELECT l.lap_time_s,
               MAX(s.speed_mps)      AS max_speed_mps,
               AVG(s.speed_mps)      AS avg_speed_mps,
               MAX(s.battery_temp_c) AS max_battery_temp_c,
               AVG(s.throttle_pct)   AS avg_throttle_pct
        FROM laps l
        JOIN samples s ON s.lap_id = l.lap_id
        WHERE l.run_id = %s AND l.lap_number = %s
        GROUP BY l.lap_id
    """, (run_id, lap_number))
    if not rows:
        return lap_not_found(run_id, lap_number)
    return {"run_id": run_id, "lap_number": lap_number, **rows[0]}


# ---------------------------------------------------------------------------
# TASK 1: get_fastest_laps
#   1. Fill in the two ____ blanks in the SQL. JOIN ... ON says which column two
#      tables share; get_lap_summary above has an example (ON s.lap_id = l.lap_id).
#   2. Replace the docstring: say what question this answers and what `limit` is.
#   3. Uncomment @mcp.tool() so the model can see it. Rerun chat.py and ask:
#        Who set the fastest lap, and in which run?
# ---------------------------------------------------------------------------

# @mcp.tool()
def get_fastest_laps(limit: int = 3) -> list[dict]:
    """TODO: write this docstring."""
    return query("""
        SELECT l.run_id, l.lap_number, r.driver, l.lap_time_s
        FROM laps l
        JOIN runs r ON ____     -- TODO: which column links a lap to its run?
        ORDER BY ____           -- TODO: fastest lap first
        LIMIT %s
    """, (min(limit, 20),))


# ---------------------------------------------------------------------------
# TASK 2: get_signal_peak
#   1. Fill in the two ____ blanks in the SQL.
#   2. Replace the docstring: say what it answers, and list the valid signal
#      names WITH units (see SIGNALS at the top of this file).
#   3. Uncomment @mcp.tool(), rerun chat.py and ask:
#        What was the peak battery temperature in run 3, and on which lap?
# ---------------------------------------------------------------------------

# @mcp.tool()
def get_signal_peak(run_id: int, signal: str) -> dict | str:
    """TODO: write this docstring."""
    # `signal` is a column name, and column names can't be %s parameters, so it goes
    # into the SQL string directly. Checking it against SIGNALS first is what keeps
    # that safe: without this, the model could inject any SQL it wanted.
    if signal not in SIGNALS:
        return f"Unknown signal '{signal}'. Valid signals: {', '.join(SIGNALS)}"
    rows = query(f"""
        SELECT l.lap_number, MAX(s.{signal}) AS peak
        FROM samples s
        JOIN laps l ON ____     -- TODO: which column links a sample to its lap?
        WHERE l.run_id = %s
        GROUP BY l.lap_number
        ORDER BY ____           -- TODO: highest peak first
        LIMIT 1
    """, (run_id,))
    if not rows:
        return f"No run {run_id}. Use list_runs to see valid run_ids."
    return {"run_id": run_id, "signal": signal, "units": SIGNALS[signal], **rows[0]}


if __name__ == "__main__":
    mcp.run()  # stdio transport: chat.py talks to this process over stdin/stdout
