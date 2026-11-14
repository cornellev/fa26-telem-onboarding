# CEV Databases & LLMs Workshop

Chat with a small local LLM that answers questions about car run data by calling
MCP tools that query Postgres. A tiny version of EVIL.

```
you ─> chat.py ─> Ollama (local model)
          │  model replies: "call get_lap_summary(run_id=2, lap_number=3)"
          ▼
       server.py (MCP tools) ─SQL─> Postgres in Docker
```

You only edit `server.py`. `chat.py` is the agent loop (worth a read, no need to edit).

## Before the workshop

Docker Desktop should already be installed from the fullstack workshop.

**Mac**

```bash
brew install python ollama
brew services start ollama
ollama pull llama3.2:3b
```

**Windows: everything in your WSL terminal**

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip zstd
curl -fsSL https://ollama.com/install.sh | sh    # install Ollama inside WSL, not the Windows app
ollama pull llama3.2:3b                          # "can't connect"? run `ollama serve` in a 2nd terminal
docker ps                                        # fails? Docker Desktop → Settings → Resources → WSL integration → Ubuntu on
```

**Then (both)**

```bash
git clone git@github.com:cornellev/fa26-telem-onboarding.git    # WSL: clone into ~, not /mnt/c
cd fa26-telem-onboarding/db-llms
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d
python scripts/check_setup.py
```

Each ✗ that `check_setup.py` prints comes with the command that fixes it.

## At the workshop

In every new terminal, run `cd fa26-telem-onboarding/db-llms && source .venv/bin/activate` first.

**1. It works.** Run `python chat.py` and ask *What runs are in the database?*
The `→ calling list_runs()` line is the model asking for a tool, and chat.py running it.

**2. Guessing vs grounded.** Run `python chat.py --no-tools` and ask *What was the max
speed on lap 3 of run 2?* Then ask again in plain `python chat.py`. Add `--show-json`
to see the raw tool call the model wrote.

**3. Write your own tools** in `server.py`. Each task is two `____` blanks in the SQL,
a docstring, and uncommenting `@mcp.tool()` so the model can see it. Rerun
`python chat.py` after each change. The tables:

```
runs     (run_id, run_date, track, run_type, driver, notes)
laps     (lap_id, run_id, lap_number, lap_time_s)
samples  (lap_id, t_ms, speed_mps, throttle_pct, brake_pct, battery_v, battery_temp_c, motor_current_a)
```

- **Task 1: `get_fastest_laps`.** Ask: *Who set the fastest lap, and in which run?*
- **Task 2: `get_signal_peak`.** Ask: *What was the peak battery temperature in run 3, and on which lap?* Then figure out why.

The model only sees each tool's name, docstring and argument types, so write the
docstring for the model.

Stuck? Run `python chat.py --server solutions/server_solution.py`.

**Stretch**

1. Change Task 1's docstring to `"""Gets laps."""` and ask again. Does the model still use it?
2. Add `list_tables()` and `describe_table(name)` (columns + first few rows), then ask
   *Explore the tables in the database and tell me anything interesting you find.*
   Small models often stop after one tool call, so ask a follow-up about anything unfamiliar.
3. Add `run_sql(sql)` for any read-only SELECT. How often does the model get the SQL right?

## Take it home (optional)

- **Your own tool:** `compare_laps(run_id, lap_a, lap_b)`, or one that finds where the driver brakes hardest.
- **A bigger model:** `ollama pull llama3.1:8b` (needs ~8 GB free RAM) and retry the stretch goals. What gets better?
- **Another MCP client:** `server.py` is a standard MCP server. Point Claude Desktop, VS Code or Cursor
  at it (command: full path to `.venv/bin/python`, arg: full path to `server.py`) and use the same tools there.
- **Your own data:** add a table to `db/init.sql` (`docker compose down -v && docker compose up -d` to reload)
  with something you care about, and write tools for it.

## Troubleshooting

- **Port 5432 already in use:** `cp .env.example .env`, set `DB_PORT=5433`, then `docker compose up -d`.
- **Wrong or missing data:** `docker compose down -v && docker compose up -d` (the data only loads on first start).
- **`No module named 'mcp'` / `externally-managed-environment`:** you forgot `source .venv/bin/activate`.
- **Slow answers:** laptop CPUs take 10 to 60 s. Try `ollama pull llama3.2:1b` then `python chat.py --model llama3.2:1b`.
