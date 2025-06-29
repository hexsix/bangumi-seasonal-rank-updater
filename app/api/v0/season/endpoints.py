from fastapi import APIRouter, Request

from app.api.v0.season import models

router = APIRouter(prefix="/season", tags=["season"])


@router.get("/{season_id}")
async def get_season(request: Request, season_id: str):
    raise NotImplementedError("Not implemented")


@router.post("/{season_id}")
async def update_season(request: Request, season_id: str, body: models.SeasonUpdate):
    raise NotImplementedError("Not implemented")


@router.delete("/{season_id}")
async def delete_season(request: Request, season_id: str):
    raise NotImplementedError("Not implemented")
