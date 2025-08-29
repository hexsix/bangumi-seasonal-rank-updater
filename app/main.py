import os
import json
import asyncio
from typing import Dict, Any

from dotenv import load_dotenv
from loguru import logger

from app.bgmtv import (
    create_index,
    update_index,
    add_subject_to_index,
    search_subject_by_name,
    IndexBasicInfo,
)
from app.ds_client import ds_client


SEASON_BY_MONTH = {
    "01": "WINTER",
    "02": "WINTER",
    "03": "WINTER",
    "04": "SPRING",
    "05": "SPRING",
    "06": "SPRING",
    "07": "SUMMER",
    "08": "SUMMER",
    "09": "SUMMER",
    "10": "FALL",
    "11": "FALL",
    "12": "FALL",
}


def _anilist_url(year: int, season: str) -> str:
    return f"https://anilist.co/search/anime?year={year}&season={season}&format=TV"


async def _process_file(filepath: str) -> None:
    filename = os.path.basename(filepath)
    name, _ = os.path.splitext(filename)

    # Expecting name like YYYYMM
    year = int(name[:4])
    month = name[4:6]
    season = SEASON_BY_MONTH.get(month)
    if not season:
        logger.warning(f"Skip {filename}: unknown month {month}")
        return

    logger.info(f"Processing {filename}: year={year}, season={season}")

    # 1) Create bangumi index
    index = await create_index()
    index_id = index.id
    logger.info(f"Created index {index_id} for {year}-{month}")

    # 2) Update index description to AniList search URL
    desc = _anilist_url(year, season)
    try:
        await update_index(index_id, IndexBasicInfo(description=desc))
        logger.info(f"Updated index {index_id} description -> {desc}")
    except Exception as e:
        logger.error(f"Failed to update index {index_id}: {e}")

    # Load data file
    with open(filepath, "r", encoding="utf-8") as f:
        payload: Dict[str, Any] = json.load(f)

    media = payload.get("data", {}).get("Page", {}).get("media", [])
    if not isinstance(media, list):
        logger.warning(f"No media list in {filename}")
        return

    # 3) Iterate items to obtain subject id using DSClient pattern
    added: set[int] = set()
    for item in media:
        native_name = (
            (item.get("title") or {}).get("native") if isinstance(item, dict) else None
        )
        if not native_name:
            continue

        try:
            bgm_info = await search_subject_by_name(native_name)
            subject_id = await ds_client.get_subject_id(native_name, bgm_info)
        except Exception as e:
            logger.error(f"Resolve subject id failed for '{native_name}': {e}")
            continue

        if not isinstance(subject_id, int) or subject_id <= 0:
            logger.info(f"Not found: {native_name}")
            continue

        if subject_id in added:
            logger.debug(f"Duplicate subject {subject_id}, skip")
            continue

        # 4) Add subject to index
        try:
            await add_subject_to_index(index_id, subject_id)
            added.add(subject_id)
            logger.info(f"Added subject {subject_id} -> index {index_id}")
        except Exception as e:
            logger.error(
                f"Add subject failed for '{native_name}' (subject_id={subject_id}): {e}"
            )


async def main():
    load_dotenv()

    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    if not os.path.isdir(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    files = [
        os.path.join(data_dir, f)
        for f in sorted(os.listdir(data_dir))
        if f.endswith(".json")
    ]

    if not files:
        logger.warning("No data files found under data/")
        return

    for fp in files:
        await _process_file(fp)
        break


if __name__ == "__main__":
    asyncio.run(main())
