from fastapi import APIRouter, Depends, HTTPException
from returns.result import Failure, Success

from app.api.v0.utils import verify_password
from app.dependencies import get_db_client
from app.services.db import DBClient, Index

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/{season_id}")
async def get_index(
    season_id: int,
    db_client: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
) -> Index:
    wrapped_index = await db_client.get_index(season_id)
    match wrapped_index:
        case Failure(e):
            raise HTTPException(status_code=404, detail=f"Index not found: {e}")
        case Success(index):
            return index
    raise HTTPException(status_code=404, detail="Index not found")
