from __future__ import annotations

import asyncio

from app.database import AsyncSessionLocal, init_db
from app.services.cache_service import (
    build_cache_key,
    clear_cache,
    get_cache_status,
    get_search_cache,
    save_search_cache,
)


async def main() -> None:
    await init_db()

    async with AsyncSessionLocal() as session:
        await clear_cache(session)
        cache_key = build_cache_key(
            "heart rate",
            "Condition",
            1,
            {"vocabulary": "SNOMED"},
        )
        await save_search_cache(
            session,
            cache_key=cache_key,
            query="heart rate",
            domain="Condition",
            page=1,
            filters={"vocabulary": "SNOMED"},
            response={"results": [{"concept_id": 1}], "cached": False},
        )
        payload, valid = await get_search_cache(session, cache_key)
        print(cache_key[:12], valid, payload)
        print(await get_cache_status(session))


if __name__ == "__main__":
    asyncio.run(main())
