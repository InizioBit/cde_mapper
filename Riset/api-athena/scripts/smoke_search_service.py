from __future__ import annotations

import asyncio
from typing import Any

from app.database import AsyncSessionLocal, init_db
from app.services.athena_browser_adapter import AthenaSearchParams
from app.services.search_service import AthenaSearchService


class FakeAthenaAdapter:
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


async def main() -> None:
    await init_db()
    adapter = FakeAthenaAdapter()

    async with AsyncSessionLocal() as session:
        service = AthenaSearchService(session, adapter=adapter)
        first = await service.search(
            query="smoke search service",
            domain="Condition",
            refresh=True,
        )
        second = await service.search(
            query="smoke search service",
            domain="Condition",
        )

    print(first["cache"]["hit"], first["source"], first["result_count"])
    print(second["cache"]["hit"], second["source"], second["result_count"])
    print(f"adapter_calls={adapter.calls}")


if __name__ == "__main__":
    asyncio.run(main())
