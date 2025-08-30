import argparse
import glob
import json
import os
from typing import Dict, List, Optional

import httpx
from loguru import logger

API_BASE = "https://api.rinshankaiho.fun/api/v0/season/"
AVAILABLE_URL = "https://api.rinshankaiho.fun/api/v0/season/available"


def _discover_season_ids_from_done(done_dir: str = "done") -> List[int]:
    pattern = os.path.join(done_dir, "*.json")
    ids: List[int] = []
    for path in sorted(glob.glob(pattern)):
        base = os.path.basename(path)
        name, ext = os.path.splitext(base)
        if name.isdigit() and len(name) == 6:
            try:
                ids.append(int(name))
            except ValueError:
                continue
    return ids


def _fetch_available_season_ids(client: httpx.Client) -> List[int]:
    try:
        r = client.get(AVAILABLE_URL, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f"Failed to fetch available seasons: {e}")
        return []

    seasons = data.get("available_seasons") or []
    ids: List[int] = []
    for s in seasons:
        try:
            i = int(s)
            if 100000 <= i <= 999999:  # six-digit season IDs like 201204
                ids.append(i)
        except Exception:
            continue
    # keep order as provided but ensure uniqueness
    seen = set()
    ordered_unique = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            ordered_unique.append(i)
    return ordered_unique


def _fetch_top_poster(season_id: int, client: httpx.Client) -> Optional[str]:
    url = f"{API_BASE}{season_id}"
    try:
        r = client.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning(f"season {season_id}: request failed: {e}")
        return None

    subjects = data.get("subjects") or []
    if not subjects:
        logger.warning(f"season {season_id}: no subjects in response")
        return None

    top = subjects[0] or {}
    poster = top.get("images_large") or top.get("images_grid")
    if not poster:
        # Some responses may nest images differently; try common alternatives.
        images = top.get("images") or {}
        poster = images.get("large") or images.get("grid")

    if not poster:
        logger.warning(f"season {season_id}: top subject has no poster url")
        return None

    return poster


def build_mapping(season_ids: List[int]) -> Dict[int, str]:
    mapping: Dict[int, str] = {}
    with httpx.Client(follow_redirects=True) as client:
        for sid in season_ids:
            poster = _fetch_top_poster(sid, client)
            if poster:
                mapping[sid] = poster
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Fetch top poster for each season")
    parser.add_argument(
        "season_ids",
        nargs="*",
        type=int,
        help=(
            "Season IDs like 201204 201207. If omitted, fetch from /season/available "
            "(default). Use --source done to discover from done/*.json"
        ),
    )
    parser.add_argument(
        "--source",
        choices=["available", "done"],
        default="available",
        help="Where to get season IDs when not provided (default: available)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="mappings/posters_by_season.json",
        help="Output JSON file path (default: mappings/posters_by_season.json)",
    )
    args = parser.parse_args()

    if args.season_ids:
        season_ids = sorted(set(args.season_ids))
    else:
        with httpx.Client(follow_redirects=True) as client:
            if args.source == "available":
                logger.info("Fetching season IDs from /season/available ...")
                season_ids = _fetch_available_season_ids(client)
            else:
                logger.info("Discovering season IDs from done/*.json ...")
                season_ids = _discover_season_ids_from_done()
        if not season_ids:
            if args.source == "available":
                logger.error(
                    "No season_ids provided and none fetched from /season/available"
                )
            else:
                logger.error(
                    "No season_ids provided and none discovered from done/*.json"
                )
            return 2

    logger.info(f"Fetching top posters for {len(season_ids)} seasons ...")
    mapping = build_mapping(season_ids)

    # Ensure output directory exists
    out_dir = os.path.dirname(args.output)
    if out_dir:
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create output directory '{out_dir}': {e}")
            return 3

    # Save as { 201204: "https://..." }
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(mapping)} entries to {args.output}")
    except Exception as e:
        logger.error(f"Failed to save output file: {e}")
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
