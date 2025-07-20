from fastapi import APIRouter, Depends, FastAPI, HTTPException

from app.api.v0.utils import verify_password

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/{season_id}")
async def get_index(
    app: FastAPI,
    season_id: int,
    _: bool = Depends(verify_password),
):
    index = app.state.db_client.get_index(season_id)
    if index:
        return index  # index已经是字典
    else:
        raise HTTPException(status_code=404, detail="Index not found")
