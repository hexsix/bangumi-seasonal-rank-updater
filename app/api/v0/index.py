from fastapi import APIRouter, HTTPException

from app.services.db.client import db_client

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/{season_id}")
async def get_index(
    season_id: int,
):
    index = db_client.get_index(season_id)
    if index:
        return index.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Index not found")
