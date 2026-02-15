"""Offline LLM (Ollama) integration for generating personalized outreach."""
import os
import httpx

# Under 8GB RAM: use 1B model. Set OLLAMA_HOST in Docker to http://ollama:11434
OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
if not OLLAMA_BASE.startswith("http"):
    OLLAMA_BASE = "http://" + OLLAMA_BASE
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")


def check_ollama_running() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def generate_outreach(profile_text: str, model: str = DEFAULT_MODEL) -> str:
    """Call local Ollama to generate multi-channel cold outreach from profile text."""
    system = """You are an expert at writing hyper-personalized cold outreach. Given information about a person (LinkedIn-style profile, role, company, interests, etc.), you must generate outreach content in a structured format.

Output ONLY valid JSON with exactly these keys (no markdown, no extra text):
- "cold_email": { "subject": "...", "body": "..." }
- "whatsapp": "..." (short message)
- "linkedin_dm": "..." (concise DM)
- "tone_used": "casual" or "formal" or "mixed" (one word)

Rules:
- Be specific to their role, company, and interests. Sound human, not generic.
- Each message must have a clear call-to-action (e.g., "Would you be open to a 15-min chat?").
- Match tone to how they might communicate (infer from any bio/post style in the data).
- Keep WhatsApp and LinkedIn DM short; email can be a bit longer."""

    user = f"Generate personalized cold outreach for this person:\n\n{profile_text}"

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    with httpx.Client(timeout=120.0) as client:
        r = client.post(f"{OLLAMA_BASE}/api/chat", json=payload)
        r.raise_for_status()
    out = r.json()
    content = (out.get("message") or {}).get("content") or ""
    return content.strip()
