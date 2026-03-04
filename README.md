# Outreach Engine 

**Offline LLM-powered hyper-personalized cold outreach.**  
One script starts everything: model is pulled from the web (runs on **&lt;8GB RAM**), server starts, and the frontend lets you upload CSV/JSON/PDF and view **chat history** (past outreach). Runs locally or via **Docker**.

## Run with one script (local)

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Linux / macOS:**
```bash
chmod +x start.sh && ./start.sh
```

The script will:
1. **Find Ollama** — checks PATH and common install folders (`%LOCALAPPDATA%\Programs\Ollama`, `Program Files\Ollama`).
2. **Start Ollama** — if not already running, runs `ollama serve` in the background (no second terminal needed).
3. **Pull the model** from the web: runs `ollama pull phi3:mini` (small, fast download).
4. Start the server. Open **http://localhost:8000**.

**If Ollama is “not running”:** install from [ollama.com](https://ollama.com), then **restart your terminal** (so PATH is updated) and run `.\start.ps1` again. If you see "Ollama not found", answer **Y** when asked to download the installer from the web; after install, run `.\start.ps1` again.

## Run with Docker (one command)

**Windows:**
```powershell
.\run-docker.ps1
```

**Linux / macOS:**
```bash
chmod +x run-docker.sh && ./run-docker.sh
```

Or:
```bash
docker compose up --build
```

On first run, the app container waits for Ollama, pulls `phi3:mini` from the web, then starts the server. Open **http://localhost:8000**. Chat history is stored in a Docker volume.

## Frontend (user-friendly)

- **Upload** CSV, JSON, or PDF (LinkedIn-style profile), or paste raw text/JSON.
- Click **Generate outreach** → cold email, WhatsApp, and LinkedIn DM appear on screen.
- **Past outreach** (chat history) is listed in the **sidebar**. Click any entry to go back and view that chat.
- All history is stored so you can return anytime to check past outreach.

## Model (&lt;8GB RAM)

Default model: **`phi3:mini`** (Microsoft Phi-3 Mini). Small and fast to download; good quality. Pulled when you run the start script or Docker. No API keys; runs fully offline after the first pull.

## Input formats

- **CSV**: First row = headers; first data row = one profile (e.g. `name`, `role`, `company`, `bio`).
- **JSON**: Object or array of objects with profile fields (e.g. `name`, `role`, `company`, `about`).
- **PDF**: Plain text extracted from the PDF (e.g. exported LinkedIn profile or notes).

## API (optional)

- `GET /health` — Server and Ollama status.
- `GET /api/history` — List past outreach (chat history).
- `GET /api/history/{id}` — Get one past chat by id.
- `POST /api/parse` — Parse file or `raw_text` only (no generation).
- `POST /api/generate` — Parse + generate outreach (saved to history); multipart `file` and/or `raw_text`, optional `model` (default `phi3:mini`).

## Tech stack

- **Backend**: FastAPI, CSV/JSON/PDF parsing, SQLite chat history, Ollama API.
- **Frontend**: Static HTML/JS, sidebar with past outreach, one-click view of any previous chat.
- **LLM**: Ollama + `phi3:mini` — offline, small & fast.

## Problem statement

SMB 02: Offline LLM-Powered Hyper-Personalized Cold Outreach Engine — ingest data about a person (e.g. LinkedIn profile), infer tone/context, and generate personalized cold email, WhatsApp, and LinkedIn DM using a local LLM only.
