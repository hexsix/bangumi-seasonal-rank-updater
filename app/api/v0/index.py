from fastapi import APIRouter, Depends, HTTPException

from app.api.v0.utils import verify_password
from app.services.db.client import db_client

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/{season_id}")
async def get_index(
    season_id: int,
    _: bool = Depends(verify_password),
):
    index = db_client.get_index(season_id)
    if index:
        return index.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Index not found")
