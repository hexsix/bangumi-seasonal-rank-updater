from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"

QUERY_SEASONAL = (
    """
    query (
      $page: Int = 1,
      $perPage: Int = 50,
      $type: MediaType = ANIME,
      $format: MediaFormat = TV,
      $seasonYear: Int,
      $season: MediaSeason
    ) {
      Page(page: $page, perPage: $perPage) {
        pageInfo { currentPage hasNextPage lastPage total perPage }
        media(
          type: $type,
          format: $format,
          seasonYear: $seasonYear,
          season: $season
        ) {
          id
          title { romaji english native }
        }
      }
    }
    """
    .strip()
)


async def _post_graphql(
    client: httpx.AsyncClient, query: str, variables: Dict[str, Any]
) -> Dict[str, Any]:
    resp = await client.post(
        ANILIST_GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"},
    )
    if not resp.is_success:
        logger.error(f"AniList API status: {resp.status_code} - {resp.text}")
        resp.raise_for_status()
    try:
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}; body={resp.text[:500]}")
        raise


async def fetch_season_page(
    year: int,
    season: str,
    page: int = 1,
    per_page: int = 50,
    media_type: str = "ANIME",
    media_format: str = "TV",
    client: Optional[httpx.AsyncClient] = None,
) -> Dict[str, Any]:
    """Fetch one page of seasonal media from AniList.

    Args:
        year: seasonYear (e.g., 2000)
        season: MediaSeason (WINTER/SPRING/SUMMER/FALL)
        page: Pagination page
        per_page: Items per page (max 50 recommended)
        media_type: MediaType (default ANIME)
        media_format: MediaFormat (default TV)
        client: optional shared AsyncClient
    Returns:
        Parsed JSON dict from AniList
    """
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
    try:
        variables = {
            "page": page,
            "perPage": per_page,
            "type": media_type,
            "format": media_format,
            "seasonYear": year,
            "season": season,
        }
        return await _post_graphql(client, QUERY_SEASONAL, variables)
    finally:
        if owns_client:
            await client.aclose()


async def fetch_season_all(
    year: int,
    season: str,
    per_page: int = 50,
    media_type: str = "ANIME",
    media_format: str = "TV",
) -> List[Dict[str, Any]]:
    """Fetch all seasonal media (all pages) and return concatenated media list."""
    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        page = 1
        while True:
            data = await fetch_season_page(
                year=year,
                season=season,
                page=page,
                per_page=per_page,
                media_type=media_type,
                media_format=media_format,
                client=client,
            )
            page_data = data.get("data", {}).get("Page", {})
            media = page_data.get("media") or []
            results.extend(media)

            page_info = page_data.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            page += 1
            await asyncio.sleep(0.2)
    return results


if __name__ == "__main__":
    # Example manual run: fetch 2000 WINTER anime TV list
    async def _demo():
        items = await fetch_season_all(2000, "WINTER")
        logger.info(f"Fetched {len(items)} items")
        # Show a few sample titles
        for it in items[:5]:
            t = (it.get("title") or {})
            logger.info(f"{it.get('id')} | {t.get('native')} | {t.get('romaji')}")

    asyncio.run(_demo())
