from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models import SearchCache
from app.services.athena_browser_adapter import AthenaSearchParams, AthenaTimeoutError
from app.services.cache_service import build_cache_key, utc_now
from app.services.search_service import (
    AthenaSearchService,
    AthenaSearchTimeoutError,
    AthenaSearchValidationError,
)


class FakeSuccessAdapter:
    async def search(self, params: AthenaSearchParams) -> dict[str, Any]:
        return {
            "query": params.query,
            "domain": params.domain,
            "page": params.page,
            "source": "fake_adapter",
            "result_count": 1,
            "results": [
                {
                    "concept_id": 201826,
                    "concept_name": "Type 2 diabetes mellitus",
                    "domain_id": "Condition",
                    "vocabulary_id": "SNOMED",
                    "concept_class_id": "Disorder",
                    "standard_concept": "Standard",
                    "concept_code": "44054006",
                    "valid_start_date": None,
                    "valid_end_date": None,
                    "invalid_reason": "Valid",
                }
            ],
        }


class FakeTimeoutAdapter:
    async def search(self, params: AthenaSearchParams) -> dict[str, Any]:
        raise AthenaTimeoutError("Simulated Athena timeout.")


async def expire_search_cache(cache_key: str) -> None:
    async with AsyncSessionLocal() as session:
        row = await session.scalar(
            select(SearchCache).where(SearchCache.cache_key == cache_key)
        )
        if row is None:
            raise RuntimeError(f"Search cache not found: {cache_key}")
        row.expires_at = utc_now() - timedelta(days=1)
        await session.commit()


async def main() -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        service = AthenaSearchService(session, adapter=FakeSuccessAdapter())
        try:
            await service.search(query="   ")
        except AthenaSearchValidationError as exc:
            print(type(exc).__name__, str(exc))

    async with AsyncSessionLocal() as session:
        service = AthenaSearchService(session, adapter=FakeTimeoutAdapter())
        try:
            await service.search(query="smoke timeout no cache", domain="Condition")
        except AthenaSearchTimeoutError as exc:
            print(type(exc).__name__, str(exc))

    stale_query = "smoke stale fallback"
    cache_key = build_cache_key(stale_query, domain="Condition", page=1, filters={})
    async with AsyncSessionLocal() as session:
        service = AthenaSearchService(session, adapter=FakeSuccessAdapter())
        await service.search(query=stale_query, domain="Condition", refresh=True)

    await expire_search_cache(cache_key)

    async with AsyncSessionLocal() as session:
        service = AthenaSearchService(session, adapter=FakeTimeoutAdapter())
        response = await service.search(query=stale_query, domain="Condition")
        print(response["cache"]["hit"], response["cache"]["stale"])
        print(response["cache"]["upstream_error"])


if __name__ == "__main__":
    asyncio.run(main())
