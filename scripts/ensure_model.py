"""Ensure Ollama is reachable and the small model is pulled (from web). Run before starting server."""
import os
import sys
import time

# Allow running as script from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx

OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
if not OLLAMA_BASE.startswith("http"):
    OLLAMA_BASE = "http://" + OLLAMA_BASE
MODEL = os.environ.get("OLLAMA_MODEL", "phi3:mini")


def wait_for_ollama(max_wait_sec: int = 60) -> bool:
    for _ in range(max_wait_sec):
        try:
            r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def model_exists() -> bool:
    try:
        r = httpx.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        if r.status_code != 200:
            return False
        data = r.json()
        models = data.get("models") or []
        base = (MODEL.split(":")[0]).split("/")[0]
        return any((m.get("name") or "").startswith(base) for m in models)
    except Exception:
        return False


def pull_model() -> bool:
    try:
        with httpx.Client(timeout=600) as client:
            with client.stream("POST", f"{OLLAMA_BASE}/api/pull", json={"name": MODEL}) as resp:
                for _ in resp.iter_lines():
                    pass
        return True
    except Exception as e:
        print(f"Pull failed: {e}", file=sys.stderr)
        return False


def main():
    print(f"Checking Ollama at {OLLAMA_BASE}...")
    if not wait_for_ollama():
        print("Ollama is not running. Start it first (e.g. run 'ollama serve' or use Docker).", file=sys.stderr)
        sys.exit(1)
    print("Ollama is up.")
    if model_exists():
        print(f"Model {MODEL} already present.")
        return
    print(f"Pulling model {MODEL} from web (this may take a few minutes)...")
    if not pull_model():
        print("Failed to pull model.", file=sys.stderr)
        sys.exit(1)
    print(f"Model {MODEL} ready.")


if __name__ == "__main__":
    main()
