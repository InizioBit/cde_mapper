from __future__ import annotations

from datetime import timedelta
from typing import Any
import unittest

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
    def __init__(self) -> None:
        self.calls = 0

    async def search(self, params: AthenaSearchParams) -> dict[str, Any]:
        self.calls += 1
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


class SearchServiceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await init_db()

    async def test_search_saves_and_reads_cache(self) -> None:
        adapter = FakeSuccessAdapter()
        query = "unit service cache"

        async with AsyncSessionLocal() as session:
            service = AthenaSearchService(session, adapter=adapter)
            first = await service.search(
                query=query,
                domain="Condition",
                refresh=True,
            )
            second = await service.search(query=query, domain="Condition")

        self.assertFalse(first["cache"]["hit"])
        self.assertFalse(first["cache"]["stale"])
        self.assertTrue(second["cache"]["hit"])
        self.assertFalse(second["cache"]["stale"])
        self.assertEqual(adapter.calls, 1)

    async def test_blank_query_raises_validation_error(self) -> None:
        async with AsyncSessionLocal() as session:
            service = AthenaSearchService(session, adapter=FakeSuccessAdapter())

            with self.assertRaises(AthenaSearchValidationError):
                await service.search(query="   ")

    async def test_timeout_without_cache_raises_timeout_error(self) -> None:
        async with AsyncSessionLocal() as session:
            service = AthenaSearchService(session, adapter=FakeTimeoutAdapter())

            with self.assertRaises(AthenaSearchTimeoutError):
                await service.search(query="unit timeout no cache", domain="Condition")

    async def test_timeout_with_expired_cache_returns_stale_response(self) -> None:
        query = "unit stale fallback format-aware"
        cache_key = build_cache_key(
            query,
            domain="Condition",
            page=1,
            filters={"format": "local"},
        )

        async with AsyncSessionLocal() as session:
            service = AthenaSearchService(session, adapter=FakeSuccessAdapter())
            await service.search(query=query, domain="Condition", refresh=True)

        async with AsyncSessionLocal() as session:
            row = await session.scalar(
                select(SearchCache).where(SearchCache.cache_key == cache_key)
            )
            self.assertIsNotNone(row)
            row.expires_at = utc_now() - timedelta(days=1)
            await session.commit()

        async with AsyncSessionLocal() as session:
            service = AthenaSearchService(session, adapter=FakeTimeoutAdapter())
            response = await service.search(query=query, domain="Condition")

        self.assertTrue(response["cache"]["hit"])
        self.assertTrue(response["cache"]["stale"])
        self.assertEqual(response["cache"]["upstream_error"], "Simulated Athena timeout.")

    async def test_athena_response_format_adds_legacy_content(self) -> None:
        async with AsyncSessionLocal() as session:
            service = AthenaSearchService(session, adapter=FakeSuccessAdapter())
            response = await service.search(
                query="unit athena format",
                domain=["Condition"],
                vocabulary=["SNOMED"],
                standard_concept=["Standard", "Classification"],
                page_size=15,
                response_format="athena",
                refresh=True,
            )

        self.assertIn("content", response)
        self.assertEqual(response["pageSize"], 15)
        self.assertEqual(response["content"][0]["id"], 201826)
        self.assertEqual(response["content"][0]["code"], "44054006")
        self.assertEqual(response["content"][0]["name"], "Type 2 diabetes mellitus")
        self.assertEqual(response["content"][0]["domain"], "Condition")
        self.assertEqual(response["content"][0]["vocabulary"], "SNOMED")
        self.assertEqual(response["content"][0]["standardConcept"], "Standard")
        self.assertEqual(response["content"][0]["className"], "Disorder")
