"""Cola de borradores persistida en SQLite.

Es el punto de control humano: nada llega a una API de red social sin haber
pasado por el estado APPROVED.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from social_agent.models import Draft, DraftStatus, Platform

_SCHEMA = """
CREATE TABLE IF NOT EXISTS drafts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    platform       TEXT    NOT NULL,
    topic          TEXT    NOT NULL,
    body           TEXT    NOT NULL,
    hashtags       TEXT    NOT NULL DEFAULT '[]',
    image_url      TEXT,
    status         TEXT    NOT NULL,
    scheduled_for  TEXT,
    created_at     TEXT    NOT NULL,
    published_at   TEXT,
    remote_id      TEXT,
    error          TEXT
);
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
"""


class DraftQueue:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, detect_types=0)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DraftQueue":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- escritura ---

    def add(self, draft: Draft) -> Draft:
        cur = self._conn.execute(
            """INSERT INTO drafts
               (platform, topic, body, hashtags, image_url, status,
                scheduled_for, created_at, published_at, remote_id, error)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                draft.platform.value,
                draft.topic,
                draft.body,
                json.dumps(draft.hashtags, ensure_ascii=False),
                draft.image_url,
                draft.status.value,
                _iso(draft.scheduled_for),
                _iso(draft.created_at),
                _iso(draft.published_at),
                draft.remote_id,
                draft.error,
            ),
        )
        self._conn.commit()
        draft.id = cur.lastrowid
        return draft

    def set_status(
        self,
        draft_id: int,
        status: DraftStatus,
        *,
        remote_id: str | None = None,
        error: str | None = None,
    ) -> None:
        published_at = (
            _iso(datetime.now()) if status is DraftStatus.PUBLISHED else None
        )
        self._conn.execute(
            """UPDATE drafts
               SET status = ?,
                   remote_id = COALESCE(?, remote_id),
                   error = ?,
                   published_at = COALESCE(?, published_at)
               WHERE id = ?""",
            (status.value, remote_id, error, published_at, draft_id),
        )
        self._conn.commit()

    def set_image(self, draft_id: int, image_url: str) -> None:
        self._conn.execute(
            "UPDATE drafts SET image_url = ? WHERE id = ?", (image_url, draft_id)
        )
        self._conn.commit()

    def update_body(self, draft_id: int, body: str) -> None:
        self._conn.execute(
            "UPDATE drafts SET body = ? WHERE id = ?", (body, draft_id)
        )
        self._conn.commit()

    # --- lectura ---

    def get(self, draft_id: int) -> Draft | None:
        row = self._conn.execute(
            "SELECT * FROM drafts WHERE id = ?", (draft_id,)
        ).fetchone()
        return _to_draft(row) if row else None

    def list(
        self,
        *,
        status: DraftStatus | None = None,
        platform: Platform | None = None,
        limit: int = 50,
    ) -> list[Draft]:
        sql = "SELECT * FROM drafts"
        clauses, params = [], []
        if status:
            clauses.append("status = ?")
            params.append(status.value)
        if platform:
            clauses.append("platform = ?")
            params.append(platform.value)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return [_to_draft(r) for r in self._conn.execute(sql, params)]

    def counts_by_status(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) AS n FROM drafts GROUP BY status"
        )
        return {r["status"]: r["n"] for r in rows}


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _to_draft(row: sqlite3.Row) -> Draft:
    return Draft(
        id=row["id"],
        platform=Platform(row["platform"]),
        topic=row["topic"],
        body=row["body"],
        hashtags=json.loads(row["hashtags"]),
        image_url=row["image_url"],
        status=DraftStatus(row["status"]),
        scheduled_for=_dt(row["scheduled_for"]),
        created_at=_dt(row["created_at"]) or datetime.now(),
        published_at=_dt(row["published_at"]),
        remote_id=row["remote_id"],
        error=row["error"],
    )
