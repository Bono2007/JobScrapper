import asyncio
import time
from collections import defaultdict

from src.config import RATE_LIMIT_DELAY

_last_request: dict[str, float] = defaultdict(float)
_lock = asyncio.Lock()


async def wait_for_domain(domain: str) -> None:
    async with _lock:
        elapsed = time.monotonic() - _last_request[domain]
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
        _last_request[domain] = time.monotonic()
