#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Map month to season name
MONTH_TO_SEASON = {
    1: "WINTER",
    4: "SPRING",
    7: "SUMMER",
    10: "FALL",
}

REPO_ROOT = Path(__file__).resolve().parent.parent
DONE_DIR = REPO_ROOT / "done"
OUTPUT_PATH = REPO_ROOT / "quarter_counts.json"


def infer_year_season_from_filename(p: Path):
    """Infer (year, season) from filename like 200401.json.
    Returns (year:int, season:str) or None if cannot parse/match.
    """
    stem = p.stem  # e.g., '200401'
    if len(stem) != 6 or not stem.isdigit():
        return None
    year = int(stem[:4])
    month = int(stem[4:])
    season = MONTH_TO_SEASON.get(month)
    if season is None:
        return None
    return year, season


def count_media_in_file(p: Path) -> int:
    """Count entries under data.Page.media; return 0 if missing/invalid."""
    try:
        with p.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        media = (((obj or {}).get("data") or {}).get("Page") or {}).get("media")
        if isinstance(media, list):
            return len(media)
        return 0
    except Exception:
        return 0


def main():
    if not DONE_DIR.exists():
        print(f"done directory not found: {DONE_DIR}", file=sys.stderr)
        sys.exit(1)

    counts = {}  # {year: {season: count}}
    totals = {"WINTER": 0, "SPRING": 0, "SUMMER": 0, "FALL": 0}

    files = sorted(DONE_DIR.glob("*.json"))
    for p in files:
        ys = infer_year_season_from_filename(p)
        if ys is None:
            # Skip files that don't map to a season
            continue
        year, season = ys
        n = count_media_in_file(p)
        year_entry = counts.setdefault(str(year), {"WINTER": 0, "SPRING": 0, "SUMMER": 0, "FALL": 0})
        year_entry[season] += n
        totals[season] += n

    output = {
        "by_year": counts,
        "totals": totals,
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
