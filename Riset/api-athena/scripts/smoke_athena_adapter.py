from __future__ import annotations

import asyncio

from app.services.athena_browser_adapter import (
    AthenaBrowserAdapter,
    AthenaSearchParams,
)


async def main() -> None:
    adapter = AthenaBrowserAdapter()
    params = AthenaSearchParams(query="diabetes", domain="Condition", page=1)
    print(adapter.build_search_url(params))
    result = await adapter.search(params)
    print(result["source"], result["result_count"])
    print(result["results"][:3])


if __name__ == "__main__":
    asyncio.run(main())
