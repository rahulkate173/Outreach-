"""Parse CSV, JSON, and PDF into a unified profile structure for the LLM."""
import csv
import io
import json
from typing import Any

from PyPDF2 import PdfReader


def parse_csv(content: bytes | str) -> dict[str, Any]:
    """Parse CSV (first row as headers) into a profile dict. Single profile = first row."""
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return {"raw": text, "source": "csv"}
    # Use first row as the main profile; include all rows if multiple
    profile = dict(rows[0])
    if len(rows) > 1:
        profile["_other_rows"] = rows[1:]
    return {"profile": profile, "source": "csv", "raw_preview": text[:2000]}


def parse_json(content: bytes | str) -> dict[str, Any]:
    """Parse JSON into a profile structure (object or list of objects)."""
    text = content.decode("utf-8") if isinstance(content, bytes) else content
    data = json.loads(text)
    if isinstance(data, list) and data:
        return {"profile": data[0], "all_profiles": data, "source": "json", "raw_preview": text[:2000]}
    if isinstance(data, dict):
        return {"profile": data, "source": "json", "raw_preview": text[:2000]}
    return {"raw": data, "source": "json"}


def parse_pdf(content: bytes) -> dict[str, Any]:
    """Extract text from PDF and treat as raw profile text for the LLM."""
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    full_text = "\n\n".join(parts).strip()
    return {"raw": full_text, "source": "pdf", "raw_preview": full_text[:2000]}


def profile_to_prompt_string(data: dict[str, Any]) -> str:
    """Turn parsed data into a single string for the LLM prompt."""
    if "profile" in data:
        p = data["profile"]
        if isinstance(p, dict):
            lines = [f"{k}: {v}" for k, v in p.items() if not k.startswith("_")]
            return "\n".join(lines)
        return str(p)
    return data.get("raw", "") or data.get("raw_preview", "")
