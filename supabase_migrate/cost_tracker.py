"""
cost_tracker.py
Logs token usage and estimated cost for every AI-generated explanation,
one row per call, to a local SQLite file.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "cost_log.sqlite3"

PRICING = {
    ("gemini", "gemini-2.0-flash"): {"input": 0.10, "output": 0.40},
    ("groq", "openai/gpt-oss-120b"): {"input": 0.15, "output": 0.75},
}


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            estimated_cost_usd REAL NOT NULL
        )
    """)


def log_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICING.get((provider, model))
    cost = 0.0 if prices is None else (
        (input_tokens / 1_000_000) * prices["input"] + (output_tokens / 1_000_000) * prices["output"]
    )
    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_table(conn)
        conn.execute(
            "INSERT INTO ai_calls (timestamp, provider, model, input_tokens, output_tokens, estimated_cost_usd) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (time.time(), provider, model, input_tokens, output_tokens, cost),
        )
        conn.commit()
    finally:
        conn.close()
    return cost


def report(since_hours: float | None = None) -> dict:
    conn = sqlite3.connect(DB_PATH)
    try:
        _ensure_table(conn)
        query = "SELECT provider, model, input_tokens, output_tokens, estimated_cost_usd FROM ai_calls"
        params = ()
        if since_hours is not None:
            query += " WHERE timestamp >= ?"
            params = (time.time() - since_hours * 3600,)
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    total_cost = sum(r[4] for r in rows)
    by_provider: dict[str, dict] = {}
    for provider, model, in_tok, out_tok, cost in rows:
        key = f"{provider}/{model}"
        entry = by_provider.setdefault(key, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        entry["calls"] += 1
        entry["input_tokens"] += in_tok
        entry["output_tokens"] += out_tok
        entry["cost_usd"] += cost

    return {"total_calls": len(rows), "total_cost_usd": round(total_cost, 6), "by_provider": by_provider}
