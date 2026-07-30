from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ConceptCache, SearchCache


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    if not filters:
        return {}
    return {key: value for key, value in sorted(filters.items()) if value is not None}


def normalize_cache_value(value: Any) -> Any:
    if isinstance(value, list):
        return sorted(str(item).strip().lower() for item in value if str(item).strip())
    if isinstance(value, str):
        return value.strip().lower()
    return value


def to_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def from_json(raw_value: str) -> Any:
    return json.loads(raw_value)


def build_cache_key(
    query: str,
    domain: Any | None = None,
    page: int = 1,
    filters: dict[str, Any] | None = None,
) -> str:
    normalized = {
        "query": query.strip().lower(),
        "domain": normalize_cache_value(domain or ""),
        "page": page,
        "filters": {
            key: normalize_cache_value(value)
            for key, value in normalize_filters(filters).items()
        },
    }
    raw_key = to_json(normalized)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def expires_at(days: int | None = None) -> datetime:
    settings = get_settings()
    ttl_days = days or settings.cache_ttl_days
    return utc_now() + timedelta(days=ttl_days)


def is_cache_valid(row: SearchCache | ConceptCache | None) -> bool:
    if row is None:
        return False
    row_expires_at = row.expires_at
    if row_expires_at.tzinfo is None:
        row_expires_at = row_expires_at.replace(tzinfo=timezone.utc)
    return row_expires_at > utc_now()


async def get_search_cache(
    session: AsyncSession,
    cache_key: str,
) -> tuple[dict[str, Any] | None, bool]:
    row = await session.scalar(
        select(SearchCache).where(SearchCache.cache_key == cache_key)
    )
    if row is None:
        return None, False
    return from_json(row.response_json), is_cache_valid(row)


async def save_search_cache(
    session: AsyncSession,
    *,
    cache_key: str,
    query: str,
    domain: str | None,
    page: int,
    filters: dict[str, Any] | None,
    response: dict[str, Any],
) -> SearchCache:
    row = await session.scalar(
        select(SearchCache).where(SearchCache.cache_key == cache_key)
    )
    payload = to_json(response)
    filters_payload = to_json(normalize_filters(filters))

    if row is None:
        row = SearchCache(
            cache_key=cache_key,
            query=query,
            domain=domain,
            page=page,
            filters_json=filters_payload,
            response_json=payload,
            expires_at=expires_at(),
        )
        session.add(row)
    else:
        row.query = query
        row.domain = domain
        row.page = page
        row.filters_json = filters_payload
        row.response_json = payload
        row.expires_at = expires_at()

    await session.commit()
    await session.refresh(row)
    return row


async def get_concept_cache(
    session: AsyncSession,
    concept_id: int,
) -> tuple[dict[str, Any] | None, bool]:
    row = await session.scalar(
        select(ConceptCache).where(ConceptCache.concept_id == concept_id)
    )
    if row is None:
        return None, False
    return from_json(row.response_json), is_cache_valid(row)


async def save_concept_cache(
    session: AsyncSession,
    *,
    concept_id: int,
    response: dict[str, Any],
) -> ConceptCache:
    row = await session.scalar(
        select(ConceptCache).where(ConceptCache.concept_id == concept_id)
    )
    payload = to_json(response)

    if row is None:
        row = ConceptCache(
            concept_id=concept_id,
            response_json=payload,
            expires_at=expires_at(),
        )
        session.add(row)
    else:
        row.response_json = payload
        row.expires_at = expires_at()

    await session.commit()
    await session.refresh(row)
    return row


async def get_cache_status(session: AsyncSession) -> dict[str, Any]:
    now = utc_now()
    search_total = await session.scalar(select(func.count()).select_from(SearchCache))
    concept_total = await session.scalar(select(func.count()).select_from(ConceptCache))
    search_expired = await session.scalar(
        select(func.count()).select_from(SearchCache).where(SearchCache.expires_at <= now)
    )
    concept_expired = await session.scalar(
        select(func.count()).select_from(ConceptCache).where(ConceptCache.expires_at <= now)
    )
    latest_search = await session.scalar(select(func.max(SearchCache.updated_at)))
    latest_concept = await session.scalar(select(func.max(ConceptCache.updated_at)))

    return {
        "search_cache": {
            "total": search_total or 0,
            "expired": search_expired or 0,
            "valid": (search_total or 0) - (search_expired or 0),
            "last_updated_at": latest_search,
        },
        "concept_cache": {
            "total": concept_total or 0,
            "expired": concept_expired or 0,
            "valid": (concept_total or 0) - (concept_expired or 0),
            "last_updated_at": latest_concept,
        },
    }


async def clear_cache(session: AsyncSession) -> dict[str, int]:
    search_result = await session.execute(delete(SearchCache))
    concept_result = await session.execute(delete(ConceptCache))
    await session.commit()

    return {
        "search_cache_deleted": search_result.rowcount or 0,
        "concept_cache_deleted": concept_result.rowcount or 0,
    }
