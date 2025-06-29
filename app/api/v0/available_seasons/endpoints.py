from fastapi import APIRouter

router = APIRouter(prefix="/available_seasons", tags=["available-seasons"])


@router.get("")
async def get_available_seasons():
    raise NotImplementedError("Not implemented")
