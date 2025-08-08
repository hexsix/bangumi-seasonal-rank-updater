from datetime import datetime
from typing import List, Sequence

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from returns.result import Failure, Success

from app.api.v0.season import models
from app.api.v0.utils import current_season_id
from app.dependencies import get_db_client
from app.services.db import DBClient, Subject

router = APIRouter(prefix="/season", tags=["season"])


@router.get("/available")
async def get_available_seasons(
    db: DBClient = Depends(get_db_client),
) -> models.AvailableSeasonsResponse:
    logger.info("available_seasons")
    wrapped_available_seasons = await db.get_available_season_ids()
    match wrapped_available_seasons:
        case Failure(e):
            raise HTTPException(
                status_code=500, detail=f"Failed to get available seasons: {e}"
            )
        case Success(available_seasons):
            available_seasons = sorted(
                available_seasons,
                reverse=True,
            )
    return models.AvailableSeasonsResponse(
        current_season_id=current_season_id(),
        available_seasons=available_seasons,
    )


@router.get("/{season_id}")
async def get_season_subjects(
    season_id: int,
    db: DBClient = Depends(get_db_client),
) -> models.SeasonResponse:
    logger.info(f"get_season {season_id}")
    wrapped_subjects = await db.get_season_subjects(season_id)
    match wrapped_subjects:
        case Failure(e):
            raise HTTPException(
                status_code=500, detail=f"Failed to get season subjects: {e}"
            )
        case Success(_db_subjects):
            db_subjects: Sequence[Subject] = _db_subjects
    subjects: List[Subject] = [subject for subject in db_subjects]

    # make meta_tags unique (stable, case-sensitive) and normalize rank for frontend sorting
    for subject in subjects:
        # stable de-dup for meta_tags while preserving original order
        if subject.meta_tags is not None:
            try:
                seen_tags: set[str] = set()
                unique_tags: list[str] = []
                for tag in subject.meta_tags:
                    if tag not in seen_tags:
                        unique_tags.append(tag)
                        seen_tags.add(tag)
                subject.meta_tags = unique_tags
            except Exception:
                # if meta_tags is malformed, keep as-is to avoid breaking the response
                pass

        # normalize rank: treat None or 0 as a large number so frontend can sort
        if subject.rank is None or subject.rank == 0:
            subject.rank = 999_999

    # sort by rank ascending, then by id ascending
    subjects.sort(key=lambda s: (s.rank if s.rank is not None else 999_999, s.id))
    updated_at = max(
        (subject.updated_at for subject in subjects),
        default=datetime(2010, 1, 1),
    )

    return models.SeasonResponse(
        season_id=season_id,
        subjects=subjects,
        updated_at=updated_at,
    )
