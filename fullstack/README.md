# Pocket Pokédex

A small Pokémon lookup app built with plain React, CSS, and a Python FastAPI backend. Search by name or Pokédex number to see official artwork, types, height, weight, abilities, and base stats. Bulbasaur loads on startup.

## Run with Docker

Install and start Docker Desktop (or Docker Engine with Compose). From this `fullstack` directory:

```bash
docker compose up --build
```

Open http://localhost:5173. Backend API docs are at http://localhost:8000/docs. Docker installs Python, Node, and the dependencies inside the containers; no local virtual environment is needed.

Each Dockerfile selects a runtime, copies the dependency list, installs it, copies the code, and starts the app. `compose.yaml` runs both containers and maps their ports to your computer. `BACKEND_URL` tells Vite to forward API requests to the `backend` container. The `.dockerignore` files keep local dependencies and build output out of the images.

This workshop setup runs the Vite development server. After editing code, stop with Ctrl+C and rerun `docker compose up --build` to include the changes. To remove the containers:

```bash
docker compose down
```

## Run locally without Docker

Requires Node.js 18+ and Python 3.10+. Run these commands from this `fullstack` directory in two terminals.

**Terminal 1 — backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The virtual environment keeps this project's Python packages in its own folder. Create it and install dependencies once; in a new terminal, activate it again before starting the backend. These commands use macOS/Linux shell syntax.

**Terminal 2 — frontend**

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://localhost:5173). Vite forwards `/api` requests to FastAPI on port 8000, so no CORS configuration or API keys are needed. Internet access is required for PokéAPI data and artwork.

## How it works

`frontend/src/App.jsx` submits searches to `GET /api/pokemon/{name}`. `backend/main.py` normalizes the name, fetches from [PokéAPI](https://pokeapi.co/docs/v2#pokemon), converts measurements to meters/kilograms, and returns just the card data. Each search makes one GET request to PokéAPI and returns a plain dictionary, without caching or custom Pydantic models. Missing Pokémon return 404; upstream failures return 502.

Interactive endpoint documentation: http://127.0.0.1:8000/docs.

## Verify

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests -v
```

```bash
cd frontend
npm run build
```

The frontend build is written to `frontend/dist`. For deployment, serve it behind a web server that forwards `/api` to FastAPI; Vite's development proxy does not apply to a static production build or `vite preview`.
