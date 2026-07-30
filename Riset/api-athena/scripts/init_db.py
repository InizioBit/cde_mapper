from __future__ import annotations

import asyncio

from app.config import get_settings
from app.database import init_db


async def main() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    print(f"Database initialized: {settings.database_url}")


if __name__ == "__main__":
    asyncio.run(main())
