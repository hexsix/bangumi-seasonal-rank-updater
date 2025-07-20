from typing import AsyncGenerator

from fastapi import Request

from app.services import BGMTVClient, DBClient


async def get_db_client(request: Request) -> AsyncGenerator[DBClient, None]:
    """
    从应用状态获取DBClient
    使用方式: db: DBClient = Depends(get_db_client)
    """
    db_client = request.app.state.db_client

    try:
        yield db_client
    finally:
        pass


async def get_bgmtv_client(request: Request) -> AsyncGenerator[BGMTVClient, None]:
    """
    从应用状态获取BGMTVClient
    使用方式: bgmtv: BGMTVClient = Depends(get_bgmtv_client)
    """
    bgmtv_client = request.app.state.bgmtv_client

    try:
        yield bgmtv_client
    finally:
        pass
