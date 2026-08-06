"""SQLite persistence layer. No external DB required by default."""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .models import AuditResult, Business, LeadScore

SCHEMA = """
CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT DEFAULT '',
    city TEXT DEFAULT '',
    state TEXT DEFAULT '',
    country TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    website TEXT DEFAULT '',
    rating REAL DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    UNIQUE(name, city, website)
);

CREATE TABLE IF NOT EXISTS audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);
"""


class Store:
    """Thin wrapper around sqlite3 for LeadForge's local database."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    # -- Businesses ---------------------------------------------------
    def upsert_business(self, b: Business) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO businesses (name, category, city, state, country, phone, website, rating, review_count, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(name, city, website) DO UPDATE SET
                     category=excluded.category, state=excluded.state, country=excluded.country,
                     phone=excluded.phone, rating=excluded.rating, review_count=excluded.review_count,
                     notes=excluded.notes
                   """,
                (b.name, b.category, b.city, b.state, b.country, b.phone, b.website, b.rating, b.review_count, b.notes),
            )
            if cur.lastrowid:
                return cur.lastrowid
            row = conn.execute(
                "SELECT id FROM businesses WHERE name=? AND city=? AND website=?",
                (b.name, b.city, b.website),
            ).fetchone()
            return row["id"]

    def list_businesses(self, category: str | None = None, city: str | None = None) -> list[Business]:
        query = "SELECT * FROM businesses WHERE 1=1"
        params: list = []
        if category:
            query += " AND lower(category) = lower(?)"
            params.append(category)
        if city:
            query += " AND lower(city) = lower(?)"
            params.append(city)
        query += " ORDER BY id"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_business(r) for r in rows]

    def get_business(self, business_id: int) -> Business | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM businesses WHERE id=?", (business_id,)).fetchone()
        return self._row_to_business(row) if row else None

    @staticmethod
    def _row_to_business(row: sqlite3.Row) -> Business:
        return Business(
            id=row["id"], name=row["name"], category=row["category"], city=row["city"],
            state=row["state"], country=row["country"], phone=row["phone"], website=row["website"],
            rating=row["rating"], review_count=row["review_count"], notes=row["notes"],
        )

    # -- Audits ---------------------------------------------------------
    def save_audit(self, result: AuditResult) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO audits (business_id, result_json) VALUES (?, ?)",
                (result.business_id, json.dumps(result.to_dict())),
            )
            return cur.lastrowid

    def latest_audit(self, business_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT result_json FROM audits WHERE business_id=? ORDER BY id DESC LIMIT 1",
                (business_id,),
            ).fetchone()
        return json.loads(row["result_json"]) if row else None

    # -- Scores -----------------------------------------------------------
    def save_score(self, score: LeadScore) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO scores (business_id, result_json) VALUES (?, ?)",
                (score.business_id, json.dumps(score.to_dict())),
            )
            return cur.lastrowid

    def latest_score(self, business_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT result_json FROM scores WHERE business_id=? ORDER BY id DESC LIMIT 1",
                (business_id,),
            ).fetchone()
        return json.loads(row["result_json"]) if row else None

    def all_latest_scores(self) -> list[dict]:
        """Return the latest score per business, joined with business info."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT b.*, s.result_json AS score_json, a.result_json AS audit_json
                FROM businesses b
                LEFT JOIN scores s ON s.id = (
                    SELECT id FROM scores WHERE business_id = b.id ORDER BY id DESC LIMIT 1
                )
                LEFT JOIN audits a ON a.id = (
                    SELECT id FROM audits WHERE business_id = b.id ORDER BY id DESC LIMIT 1
                )
                ORDER BY b.id
                """
            ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["score"] = json.loads(row["score_json"]) if row["score_json"] else None
            item["audit"] = json.loads(row["audit_json"]) if row["audit_json"] else None
            del item["score_json"]
            del item["audit_json"]
            results.append(item)
        return results
