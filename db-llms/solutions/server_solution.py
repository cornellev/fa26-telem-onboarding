"""SOLUTION: server.py with both tasks done, plus the stretch-goal tools.

Use it with:  python chat.py --server solutions/server_solution.py
or copy it:   cp solutions/server_solution.py server.py

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
# Task 1 (solution)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_fastest_laps(limit: int = 3) -> list[dict]:
    """Find the fastest laps across ALL runs (run_id, lap_number, driver,
    lap_time_s in seconds), fastest first. Use for "who was fastest" questions.

    Args:
        limit: how many laps to return, 1 to 20 (default 3).
    """
    return query("""
        SELECT l.run_id, l.lap_number, r.driver, l.lap_time_s
        FROM laps l
        JOIN runs r ON r.run_id = l.run_id
        ORDER BY l.lap_time_s
        LIMIT %s
    """, (min(limit, 20),))


# ---------------------------------------------------------------------------
# Task 2 (solution)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_signal_peak(run_id: int, signal: str) -> dict | str:
    """Find the highest value of one sensor signal in a run, and which lap it
    happened on. Use for "peak", "highest" or "max ... in run N" questions.

    Args:
        run_id: the run's id, e.g. 3 (see list_runs).
        signal: one of speed_mps (m/s), throttle_pct (%), brake_pct (%),
            battery_v (volts), battery_temp_c (degrees C), motor_current_a (amps).
    """
    # `signal` is a column name, and column names can't be %s parameters, so it goes
    # into the SQL string directly. Checking it against SIGNALS first is what keeps
    # that safe: without this, the model could inject any SQL it wanted.
    if signal not in SIGNALS:
        return f"Unknown signal '{signal}'. Valid signals: {', '.join(SIGNALS)}"
    rows = query(f"""
        SELECT l.lap_number, MAX(s.{signal}) AS peak
        FROM samples s
        JOIN laps l ON l.lap_id = s.lap_id
        WHERE l.run_id = %s
        GROUP BY l.lap_number
        ORDER BY peak DESC
        LIMIT 1
    """, (run_id,))
    if not rows:
        return f"No run {run_id}. Use list_runs to see valid run_ids."
    return {"run_id": run_id, "signal": signal, "units": SIGNALS[signal], **rows[0]}


# ---------------------------------------------------------------------------
# Stretch: let the model explore the schema itself
# ---------------------------------------------------------------------------

@mcp.tool()
def list_tables() -> list[dict]:
    """List every table in the database with its approximate row count, including
    tables no other tool covers. Call this first when asked what is in the
    database or to explore it, then call describe_table on any table you
    don't recognize to see what's inside."""
    return query("""
        SELECT c.relname AS table_name, c.reltuples::bigint AS approx_rows
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind = 'r'
        ORDER BY c.relname
    """)


@mcp.tool()
def describe_table(name: str) -> dict | str:
    """Show one table's columns (name and data type) and its first 3 rows.

    Args:
        name: table name exactly as list_tables shows it, e.g. "laps".
    """
    tables = [t["table_name"] for t in list_tables()]
    # A table name can't be a %s parameter either, so check it against the real list.
    if name not in tables:
        return f"No table named '{name}'. Tables: {', '.join(tables)}"
    columns = query("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (name,))
    return {"table": name, "columns": columns, "first_rows": query(f"SELECT * FROM {name} LIMIT 3")}


@mcp.tool()
def run_sql(sql: str) -> list[dict] | str:
    """Run one read-only SQL SELECT against the Postgres telemetry database and
    return up to 20 rows. Call list_tables/describe_table first so you use real
    column names.

    Args:
        sql: a single SELECT (or WITH ... SELECT) statement.
    """
    # Defense in depth: the DB user is read-only anyway, but reject obvious non-SELECTs
    # with a helpful message instead of a database error.
    statement = sql.strip().rstrip(";")
    if ";" in statement or statement.split(None, 1)[0].lower() not in ("select", "with"):
        return "Only a single SELECT statement is allowed."
    try:
        return query(statement)
    except psycopg.Error as e:
        return f"SQL error: {str(e).strip()}"


if __name__ == "__main__":
    mcp.run()  # stdio transport: chat.py talks to this process over stdin/stdout
