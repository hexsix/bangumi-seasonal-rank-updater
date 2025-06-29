from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.api.v0.season import models
from app.api.v0.utils import get_subject_detail
from app.services.bgmtv import get_index
from app.services.redis_client import (
    get_available_seasons,
    get_index_id,
    get_subject,
    update_subject,
)
from app.utils import current_season_id

router = APIRouter(prefix="/season", tags=["season"])


async def get_redis_client(request: Request) -> Redis:
    """获取Redis客户端的依赖注入函数"""
    return request.app.state.redis_client.client


@router.get("/available")
async def available_seasons(
    redis_client: Redis = Depends(get_redis_client),
) -> models.AvailableSeasonsResponse:
    available_seasons = await get_available_seasons(redis_client)
    return models.AvailableSeasonsResponse(
        current_season_id=current_season_id(),
        available_seasons=available_seasons,
    )


@router.get("/{season_id}")
async def get_season(
    season_id: int, redis_client: Redis = Depends(get_redis_client)
) -> models.SeasonResponse:
    index_id = await get_index_id(redis_client, int(season_id))
    if index_id is None:
        raise HTTPException(status_code=404, detail="Season not found")
    paged_index_subject = await get_index(index_id, 2, 100, 0)
    subjects = []
    updated_at = datetime(2010, 1, 1)
    for subject in paged_index_subject.data:
        if subject_data := await get_subject(redis_client, subject.id):
            subjects.append(subject_data)
            if updated_at is None or updated_at < subject_data.updated_at:
                updated_at = subject_data.updated_at
        else:
            subject_data = await get_subject_detail(subject.id)
            await update_subject(redis_client, subject_data)
            subjects.append(subject_data)
            if updated_at is None or updated_at < subject_data.updated_at:
                updated_at = subject_data.updated_at

    return models.SeasonResponse(
        season_id=season_id,
        subjects=subjects,
        updated_at=updated_at,
    )
