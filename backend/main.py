"""FastAPI backend: ingest CSV/JSON/PDF, generate outreach via local Llama (Ollama)."""
import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.history import add_entry, get_entry, list_entries
from backend.llm import check_ollama_running, generate_outreach
from backend.parsers import parse_csv, parse_json, parse_pdf, profile_to_prompt_string

app = FastAPI(title="Cold Outreach Engine (SMB 02)", version="1.0.0")

# Serve frontend (single command = backend + UI)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_json_from_response(text: str) -> dict[str, Any]:
    """Try to parse JSON from LLM output (may be wrapped in markdown)."""
    text = text.strip()
    # Remove markdown code block if present
    if "```json" in text:
        text = text.split("```json", 1)[-1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[-1].split("```", 1)[0].strip()
    # Find first { ... }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())
    return {"raw_response": text}


@app.get("/health")
def health():
    return {"status": "ok", "ollama": check_ollama_running()}


@app.post("/api/parse")
async def parse_input(
    file: UploadFile | None = None,
    raw_text: str | None = None,
):
    """Parse CSV, JSON, or PDF from file upload or raw text (JSON/CSV)."""
    if file:
        content = await file.read()
        name = (file.filename or "").lower()
        if name.endswith(".csv"):
            data = parse_csv(content)
        elif name.endswith(".json"):
            data = parse_json(content)
        elif name.endswith(".pdf"):
            data = parse_pdf(content)
        else:
            raise HTTPException(400, "Unsupported format. Use .csv, .json, or .pdf")
    elif raw_text:
        raw_text = raw_text.strip()
        if raw_text.startswith("{"):
            data = parse_json(raw_text)
        else:
            data = parse_csv(raw_text)
    else:
        raise HTTPException(400, "Provide either a file upload or raw_text")
    prompt_string = profile_to_prompt_string(data)
    return {"parsed": data, "profile_for_llm": prompt_string}


@app.get("/api/history")
def history_list(limit: int = 100):
    """List past outreach chats (id, created_at, profile_preview snippet)."""
    return {"history": list_entries(limit=limit)}


@app.get("/api/history/{entry_id:int}")
def history_get(entry_id: int):
    """Get one past chat by id."""
    entry = get_entry(entry_id)
    if not entry:
        raise HTTPException(404, "Chat not found")
    return entry


@app.post("/api/generate")
async def generate(
    file: UploadFile | None = None,
    raw_text: str | None = None,
    model: str = "phi3:mini",
):
    """Parse input (CSV/JSON/PDF), run local LLM, save to history, return structured outreach."""
    if file:
        content = await file.read()
        name = (file.filename or "").lower()
        if name.endswith(".csv"):
            data = parse_csv(content)
        elif name.endswith(".json"):
            data = parse_json(content)
        elif name.endswith(".pdf"):
            data = parse_pdf(content)
        else:
            raise HTTPException(400, "Unsupported format. Use .csv, .json, or .pdf")
    elif raw_text:
        raw_text = raw_text.strip()
        if raw_text.startswith("{"):
            data = parse_json(raw_text)
        else:
            data = parse_csv(raw_text)
    else:
        raise HTTPException(400, "Provide either a file upload or raw_text")

    profile_str = profile_to_prompt_string(data)
    if not profile_str:
        raise HTTPException(400, "No profile data could be extracted from the input.")

    if not check_ollama_running():
        raise HTTPException(
            503,
            detail={
                "code": "ollama_not_running",
                "message": "Ollama is not running. Generate outreach will work after you start Ollama.",
                "steps": [
                    "Install Ollama from https://ollama.com if you haven't.",
                    "Open a terminal and run: ollama serve",
                    "In another terminal run: ollama pull phi3:mini",
                ],
            },
        )

    raw_out = generate_outreach(profile_str, model=model)
    try:
        structured = extract_json_from_response(raw_out)
    except json.JSONDecodeError:
        structured = {"raw_response": raw_out}

    profile_preview = profile_str[:1500]
    entry_id = add_entry(profile_preview, structured, raw_llm_output=raw_out)

    return {
        "id": entry_id,
        "profile_preview": profile_preview,
        "outreach": structured,
        "raw_llm_output": raw_out,
    }
