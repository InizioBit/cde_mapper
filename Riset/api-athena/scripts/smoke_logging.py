from __future__ import annotations

import asyncio
from typing import Any

from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.logging_config import configure_logging
from app.services.athena_browser_adapter import AthenaSearchParams
from app.services.search_service import AthenaSearchService


class FakeAthenaAdapter:
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


async def main() -> None:
    configure_logging()
    await init_db()

    async with AsyncSessionLocal() as session:
        service = AthenaSearchService(session, adapter=FakeAthenaAdapter())
        await service.search(
            query="smoke logging",
            domain="Condition",
            refresh=True,
        )
        await service.search(
            query="smoke logging",
            domain="Condition",
        )

    settings = get_settings()
    lines = settings.log_path.read_text(encoding="utf-8").splitlines()
    print(settings.log_path)
    for line in lines[-6:]:
        print(line)


if __name__ == "__main__":
    asyncio.run(main())
