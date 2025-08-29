import os
import sys
import json
import asyncio
from datetime import datetime
from typing import List, Tuple

from dotenv import load_dotenv
from loguru import logger

from app.anilist.client import fetch_season_all

SEASON_TO_MONTH = {
    "WINTER": "01",
    "SPRING": "04",
    "SUMMER": "07",
    "FALL": "10",
}

MONTH_TO_SEASON = {v: k for k, v in SEASON_TO_MONTH.items()}


def iter_seasons(start_ym: str, end_ym: str) -> List[Tuple[int, str, str]]:
    """Yield (year, season, yyyymm) from start_ym to end_ym inclusive.

    Args:
        start_ym: 'YYYYMM' (e.g., '200107')
        end_ym: 'YYYYMM' (e.g., '201201')
    """
    sy = int(start_ym[:4])
    sm = start_ym[4:6]
    ey = int(end_ym[:4])
    em = end_ym[4:6]

    # Validate months map to seasons
    if sm not in MONTH_TO_SEASON or em not in MONTH_TO_SEASON:
        raise ValueError("start_ym or end_ym month is not aligned to a known season (01/04/07/10)")

    year = sy
    month = sm
    items: List[Tuple[int, str, str]] = []
    while True:
        season = MONTH_TO_SEASON[month]
        yyyymm = f"{year}{month}"
        items.append((year, season, yyyymm))
        if year == ey and month == em:
            break
        # advance by quarter
        if month == "01":
            month = "04"
        elif month == "04":
            month = "07"
        elif month == "07":
            month = "10"
        else:  # "10"
            month = "01"
            year += 1
    return items


async def fetch_and_save_range(start_ym: str = "200107", end_ym: str = "201201") -> None:
    """Fetch AniList seasonal data for a range and write JSON files to ./data.

    - Uses filters: type=ANIME, format=TV.
    - Saves to data/YYYYMM.json with structure matching app/main.py expectations.
    """
    root_dir = os.path.dirname(os.path.dirname(__file__))
    logs_dir = os.path.join(root_dir, "logs")
    data_dir = os.path.join(root_dir, "data")

    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # Configure logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    logger.add(os.path.join(logs_dir, "run.log"), level="DEBUG", encoding="utf-8", rotation="1 MB", enqueue=True)

    seasons = iter_seasons(start_ym, end_ym)
    logger.info(f"Planned fetch for {len(seasons)} seasons from {start_ym} to {end_ym}")

    for year, season, yyyymm in seasons:
        out_path = os.path.join(data_dir, f"{yyyymm}.json")
        if os.path.exists(out_path):
            logger.info(f"Skip {yyyymm}: file already exists")
            continue

        try:
            logger.info(f"Fetching {year} {season} (AniList)")
            media = await fetch_season_all(year, season)
            # Build payload consistent with existing data files
            payload = {
                "data": {
                    "Page": {
                        "pageInfo": {"hasNextPage": False},
                        "media": media,
                    }
                }
            }
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(media)} items -> {out_path}")
        except Exception as e:
            logger.error(f"Failed to fetch/save {year} {season}: {e}")


async def main():
    load_dotenv()
    await fetch_and_save_range("200107", "201201")


if __name__ == "__main__":
    asyncio.run(main())
