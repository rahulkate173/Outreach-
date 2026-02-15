"""SQLite-backed chat history for past outreach."""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "outreach.db"


def _ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            profile_preview TEXT NOT NULL,
            outreach_json TEXT NOT NULL,
            raw_llm_output TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_entry(profile_preview: str, outreach: dict[str, Any], raw_llm_output: str = "") -> int:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute(
        "INSERT INTO history (created_at, profile_preview, outreach_json, raw_llm_output) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat() + "Z", profile_preview, json.dumps(outreach), raw_llm_output or ""),
    )
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def list_entries(limit: int = 100) -> list[dict[str, Any]]:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT id, created_at, profile_preview, outreach_json FROM history ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "created_at": r[1],
            "profile_preview": (r[2] or "")[:300],
            "outreach": json.loads(r[3]) if r[3] else {},
        }
        for r in rows
    ]


def get_entry(entry_id: int) -> dict[str, Any] | None:
    _ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT id, created_at, profile_preview, outreach_json, raw_llm_output FROM history WHERE id = ?",
        (entry_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "created_at": row[1],
        "profile_preview": row[2],
        "outreach": json.loads(row[3]) if row[3] else {},
        "raw_llm_output": row[4] or "",
    }
