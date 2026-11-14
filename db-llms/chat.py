"""Chat with a local model that can call the MCP tools in server.py.

    python chat.py [--no-tools] [--show-json] [--model NAME] [--server FILE]

In the chat: /tools, /reset, /quit. The agent loop is answer(): the model only
*asks* for a tool call; this file runs it through MCP and sends back the result.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from contextlib import AsyncExitStack

import ollama
import psycopg
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import DATABASE_URL, OLLAMA_MODEL, ROOT

MAX_TOOL_ROUNDS = 5
SYSTEM_PROMPT = ("You are the Telemetry assistant for Cornell Electric Vehicles (CEV). For any question "
                 "about runs, laps, drivers or sensor data, call a tool to get the data. Never make up "
                 "numbers. Always give units. Keep answers short.")
NO_TOOLS_PROMPT = ("You are the Telemetry assistant for Cornell Electric Vehicles (CEV). Answer questions "
                   "about the car's runs, laps and sensor data. Always give units. Keep answers short.")
COLORS = ("\033[36m", "\033[2m", "\033[33m", "\033[31m", "\033[1m", "\033[0m")
CYAN, DIM, YELLOW, RED, BOLD, RESET = COLORS if sys.stdout.isatty() else [""] * 6


def fail(problem: str, fix: str) -> None:
    sys.exit(f"{RED}✗ {problem}{RESET}\n  Fix: {BOLD}{fix}{RESET}")


def preflight(model: str, server: str | None) -> bool:
    """Check Ollama, the model, the DB and server.py. Returns True if the model has a
    thinking mode (we turn it off so replies are fast on a laptop CPU)."""
    try:
        pulled = {m.model for m in ollama.list().models}
    except Exception:
        fail("Can't reach Ollama.", "brew services start ollama" if sys.platform == "darwin"
             else "ollama serve   (in a second terminal, leave it open)")
    if model not in pulled and f"{model}:latest" not in pulled:
        fail(f"Model '{model}' isn't downloaded.", f"ollama pull {model}")
    if server:
        try:
            psycopg.connect(DATABASE_URL, connect_timeout=3).close()
        except psycopg.OperationalError as e:
            if "authentication failed" in str(e) or "does not exist" in str(e):
                fail("The database wasn't seeded.", "docker compose down -v && docker compose up -d")
            fail("Can't reach the database.", "docker compose up -d   (is Docker Desktop running?)")
        # Import server.py on its own first, so a typo shows a normal Python traceback.
        if subprocess.run([sys.executable, "-c", f"import runpy; runpy.run_path({server!r})"],
                          env={**os.environ, "PYTHONPATH": str(ROOT)}).returncode:
            fail(f"{server} has an error (see above).", "fix that line, save, and rerun chat.py")
    return "thinking" in (ollama.show(model).capabilities or [])


def to_ollama_tool(tool) -> dict:
    """MCP tool -> Ollama tool format. Optional args (anyOf[int, null]) become plain types."""
    props = {}
    for name, prop in tool.inputSchema.get("properties", {}).items():
        types = [p["type"] for p in prop.get("anyOf", [prop]) if p.get("type") not in (None, "null")]
        props[name] = {"type": types[0] if types else "string"}
    params = {"type": "object", "properties": props, "required": tool.inputSchema.get("required", [])}
    return {"type": "function", "function": {"name": tool.name, "description": tool.description or "",
                                             "parameters": params}}


def coerce_args(args: dict, params: dict) -> dict:
    """Small models often send "3" instead of 3, or make up arguments. Fix what we can."""
    fixed = {}
    for key, value in (args or {}).items():
        if key not in params["properties"] or str(value).lower() in ("", "null", "none"):
            continue
        if params["properties"][key]["type"] == "integer":
            try:
                value = int(float(value))
            except (TypeError, ValueError):
                pass  # the tool will report the bad value
        fixed[key] = value
    return fixed


async def call_tool(session: ClientSession, name: str, args: dict) -> str:
    result = await session.call_tool(name, args)
    data = result.structuredContent
    if data is not None:
        text = json.dumps(data["result"] if list(data) == ["result"] else data)
    else:
        text = "\n".join(c.text for c in result.content if c.type == "text")
    return f"Error: {text}" if result.isError else text


def warm_up(model: str, system: dict, tools: list, think) -> None:
    """Load the model and pre-read the system prompt + tools while you type your question."""
    ollama.chat(model=model, messages=[system, {"role": "user", "content": "hi"}],
                tools=tools or None, think=think, options={"num_predict": 1})


async def answer(model, messages, session, tools, think, show_json=False):
    """Ask the model; run any tool calls it proposes; repeat. Returns (answer, calls)."""
    params = {t["function"]["name"]: t["function"]["parameters"] for t in tools}
    calls = []
    for _ in range(MAX_TOOL_ROUNDS):
        reply = ollama.chat(model=model, messages=messages, tools=tools or None, think=think).message
        messages.append(reply)
        if not reply.tool_calls:
            return reply.content, calls
        for call in reply.tool_calls:
            name, raw = call.function.name, dict(call.function.arguments or {})
            if show_json:
                print(f"{DIM}  model wrote: {json.dumps({'name': name, 'arguments': raw})}{RESET}")
            if name in params:
                args = coerce_args(raw, params[name])
                print(f"{CYAN}→ calling {name}({', '.join(f'{k}={v!r}' for k, v in args.items())}){RESET}")
                result = await call_tool(session, name, args)
            else:
                result = f"Error: no tool called {name}. Tools: {', '.join(params)}"
            print(f"{DIM}  ← {result[:110]}{'…' if len(result) > 110 else ''}{RESET}")
            calls.append((name, raw))
            messages.append({"role": "tool", "content": result, "tool_name": name})
    print(f"{YELLOW}(hit {MAX_TOOL_ROUNDS} tool rounds, asking for a final answer){RESET}")
    reply = ollama.chat(model=model, messages=messages, think=think).message
    messages.append(reply)
    return reply.content, calls


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=OLLAMA_MODEL)
    parser.add_argument("--no-tools", action="store_true", help="give the model no tools")
    parser.add_argument("--show-json", action="store_true", help="print the raw tool-call JSON")
    parser.add_argument("--server", default="server.py", help="MCP server file to run")
    args = parser.parse_args()
    server = None if args.no_tools else str((ROOT / args.server).resolve())
    think = False if preflight(args.model, server) else None

    async with AsyncExitStack() as stack:
        session, tools = None, []
        if server:  # run server.py as a subprocess; talk MCP over its stdin/stdout
            params = StdioServerParameters(command=sys.executable, args=[server], cwd=str(ROOT),
                                           env={**os.environ, "PYTHONPATH": str(ROOT)})
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            tools = [to_ollama_tool(t) for t in (await session.list_tools()).tools]

        system = {"role": "system", "content": SYSTEM_PROMPT if tools else NO_TOOLS_PROMPT}
        messages = [system]
        warmup = asyncio.create_task(asyncio.to_thread(warm_up, args.model, system, tools, think))
        names = ", ".join(t["function"]["name"] for t in tools) or "none"
        print(f"{BOLD}CEV Telemetry chat{RESET}  model={args.model}  tools: {names}")
        while True:
            try:
                text = (await asyncio.to_thread(input, f"\n{BOLD}you>{RESET} ")).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if text in ("/quit", "/exit"):
                break
            elif text == "/reset":
                messages = [system]
            elif text == "/tools":
                for t in tools:
                    print(f"  {CYAN}{t['function']['name']}{RESET}: {' '.join(t['function']['description'].split())[:80]}")
            elif text:
                messages.append({"role": "user", "content": text})
                await warmup
                reply, _ = await answer(args.model, messages, session, tools, think, args.show_json)
                print(f"{BOLD}model>{RESET} {reply}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
