import asyncio

import httpx
from curl_cffi.requests import AsyncSession as CurlSession

from src.config import DEFAULT_HEADERS, MAX_RETRIES, RATE_LIMIT_DELAY, REQUEST_TIMEOUT


async def fetch_page(
    url: str, headers: dict | None = None, params: dict | None = None
) -> str:
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        http2=True,
    ) as client:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(url, headers=merged_headers, params=params)
                resp.raise_for_status()
                return resp.text
            except (httpx.HTTPStatusError, httpx.TransportError):
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    raise
    return ""


async def fetch_json(
    url: str, headers: dict | None = None, params: dict | None = None
) -> dict:
    merged_headers = {
        **DEFAULT_HEADERS,
        **(headers or {}),
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        http2=True,
    ) as client:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.get(url, headers=merged_headers, params=params)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.TransportError):
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    raise
    return {}


async def post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    merged_headers = {
        **DEFAULT_HEADERS,
        **(headers or {}),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        http2=True,
    ) as client:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await client.post(url, json=payload, headers=merged_headers)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPStatusError, httpx.TransportError):
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    raise
    return {}


async def fetch_with_curl(url: str, headers: dict | None = None, verify: bool = True) -> str:
    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}
    async with CurlSession(impersonate="chrome") as session:
        for attempt in range(MAX_RETRIES):
            try:
                resp = await session.get(
                    url, headers=merged_headers, timeout=REQUEST_TIMEOUT, verify=verify
                )
                resp.raise_for_status()
                return resp.text
            except Exception:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    raise
    return ""
