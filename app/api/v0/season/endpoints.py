import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from app.api.v0.season import models
from app.api.v0.utils import get_subject_detail
from app.services import db
from app.services.bgmtv import get_index
from app.utils import current_season_id

router = APIRouter(prefix="/season", tags=["season"])


async def get_db_conn(request: Request) -> sqlite3.Connection:
    return request.app.state.db_conn


@router.get("/available")
async def available_seasons(
    db_conn: sqlite3.Connection = Depends(get_db_conn),
) -> models.AvailableSeasonsResponse:
    logger.info("available_seasons")
    available_seasons = db.get_available_seasons(db_conn)
    return models.AvailableSeasonsResponse(
        current_season_id=current_season_id(),
        available_seasons=available_seasons,
    )


@router.get("/{season_id}")
async def get_season(
    season_id: int, db_conn: sqlite3.Connection = Depends(get_db_conn)
) -> models.SeasonResponse:
    logger.info(f"get_season {season_id}")
    index = db.get_index(db_conn, int(season_id))
    if index is None:
        raise HTTPException(status_code=404, detail="Season not found")
    paged_index_subject = await get_index(index.index_id, 2, 100, 0)
    subjects = []
    updated_at = datetime(2010, 1, 1)
    for subject in paged_index_subject.data:
        if subject_data := db.get_subject(db_conn, subject.id):
            subjects.append(subject_data)
            if updated_at is None or updated_at < subject_data.updated_at:
                updated_at = subject_data.updated_at
        else:
            subject_data = await get_subject_detail(subject.id)
            db.insert_subject(db_conn, subject_data)
            subjects.append(subject_data)
            if updated_at is None or updated_at < subject_data.updated_at:
                updated_at = subject_data.updated_at

    return models.SeasonResponse(
        season_id=season_id,
        subjects=subjects,
        updated_at=updated_at,
    )
