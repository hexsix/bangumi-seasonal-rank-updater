from datetime import datetime

from fastapi import APIRouter
from loguru import logger

from app.api.v0.season import models
from app.api.v0.utils import current_season_id
from app.services import db
from app.services.db.client import db_client

router = APIRouter(prefix="/season", tags=["season"])


@router.get("/available")
async def available_seasons() -> models.AvailableSeasonsResponse:
    logger.info("available_seasons")
    available_seasons = db_client.get_available_seasons()
    available_seasons = sorted(
        available_seasons,
        reverse=True,
    )
    return models.AvailableSeasonsResponse(
        current_season_id=current_season_id(),
        available_seasons=available_seasons,
    )


@router.get("/{season_id}")
async def get_season(season_id: int) -> models.SeasonResponse:
    logger.info(f"get_season {season_id}")
    subjects = db_client.get_season_subjects(season_id)
    subjects = [db.Subject.to_dict(subject) for subject in subjects]
    updated_at = max(
        (subject["updated_at"] for subject in subjects),
        default=datetime(2010, 1, 1),
    )

    return models.SeasonResponse(
        season_id=season_id,
        subjects=subjects,
        updated_at=updated_at,
    )
