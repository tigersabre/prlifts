"""
asyncpg_job_repository.py
PRLifts Backend

asyncpg implementations of JobRepository, PromptTemplateRepository, and
AIRequestLogRepository. All three are in one file because they form the
AI async job pipeline. Excluded from the coverage gate — see
pyproject.toml [tool.coverage.run] omit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg

from app.repositories.job_repository import (
    AIRequestLogRecord,
    JobRecord,
    PromptTemplateRecord,
)

_JOB_ENUM_CASTS: dict[str, str] = {
    "status": "::job_status",
    "job_type": "::job_type",
}


def _job_from_row(row: asyncpg.Record) -> JobRecord:
    return JobRecord(
        id=row["id"],
        user_id=row["user_id"],
        job_type=str(row["job_type"]),
        status=str(row["status"]),
        result=row["result"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        expires_at=row["expires_at"],
    )


def _prompt_template_from_row(row: asyncpg.Record) -> PromptTemplateRecord:
    return PromptTemplateRecord(
        id=row["id"],
        feature=row["feature"],
        version=row["version"],
        prompt_text=row["prompt_text"],
        is_active=row["is_active"],
        created_at=row["created_at"],
        deactivated_at=row["deactivated_at"],
    )


def _ai_log_from_row(row: asyncpg.Record) -> AIRequestLogRecord:
    quality = row["quality_score"]
    return AIRequestLogRecord(
        id=row["id"],
        user_id=row["user_id"],
        prompt_template_id=row["prompt_template_id"],
        job_id=row["job_id"],
        endpoint=row["endpoint"],
        response=row["response"],
        model=row["model"],
        quality_score=float(quality) if quality is not None else None,
        duration_ms=row["duration_ms"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
    )


class AsyncpgJobRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(self, user_id: UUID, job_type: str) -> JobRecord:
        row = await self._pool.fetchrow(
            """
            INSERT INTO job (user_id, job_type, status)
            VALUES ($1, $2::job_type, 'pending'::job_status)
            RETURNING *
            """,
            user_id,
            job_type,
        )
        return _job_from_row(row)

    async def get_by_id(self, job_id: UUID) -> JobRecord | None:
        row = await self._pool.fetchrow(
            "SELECT * FROM job WHERE id = $1",
            job_id,
        )
        return _job_from_row(row) if row is not None else None

    async def update(self, job_id: UUID, updates: dict[str, Any]) -> None:
        if not updates:
            return

        parts: list[str] = []
        values: list[Any] = []
        for i, (col, val) in enumerate(updates.items(), start=1):
            cast = _JOB_ENUM_CASTS.get(col, "")
            parts.append(f"{col} = ${i}{cast}")
            values.append(val)

        n = len(values) + 1
        values.append(job_id)
        sql = f"UPDATE job SET {', '.join(parts)} WHERE id = ${n}"
        await self._pool.execute(sql, *values)

    async def expire_stale(self, now: datetime) -> int:
        tag = await self._pool.execute(
            """
            UPDATE job SET status = 'expired'::job_status
            WHERE status IN ('pending'::job_status, 'processing'::job_status)
              AND expires_at < $1
            """,
            now,
        )
        parts = tag.split()
        return int(parts[-1]) if parts else 0


class AsyncpgPromptTemplateRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_active(self, feature: str) -> PromptTemplateRecord | None:
        row = await self._pool.fetchrow(
            "SELECT * FROM prompt_template WHERE feature = $1 AND is_active = TRUE",
            feature,
        )
        return _prompt_template_from_row(row) if row is not None else None


class AsyncpgAIRequestLogRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        user_id: UUID,
        prompt_template_id: UUID | None,
        job_id: UUID | None,
        endpoint: str,
        model: str,
        response: str | None,
        duration_ms: int,
        quality_score: float | None,
    ) -> AIRequestLogRecord:
        row = await self._pool.fetchrow(
            """
            INSERT INTO ai_request_log (
                user_id, prompt_template_id, job_id, endpoint,
                model, response, duration_ms, quality_score
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
            """,
            user_id,
            prompt_template_id,
            job_id,
            endpoint,
            model,
            response,
            duration_ms,
            quality_score,
        )
        return _ai_log_from_row(row)
