from datetime import datetime
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger

from app.config import config

security = HTTPBasic()


def verify_password(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """验证API密码的依赖项"""
    if credentials.password != config.app_api_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def current_season_id() -> int:
    now = datetime.now()
    if now.month >= 10:
        return int(f"{now.year}10")
    elif now.month >= 7:
        return int(f"{now.year}07")
    elif now.month >= 4:
        return int(f"{now.year}04")
    else:
        return int(f"{now.year}01")


def recent_season_ids() -> set[int]:
    now = datetime.now()
    years = [now.year - 1, now.year]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month > now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons[-4:])


def older_season_ids() -> set[int]:
    now = datetime.now()
    years = [year for year in range(now.year - 4, now.year + 1, 1)]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month > now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons[-16:]) - set(recent_season_ids())


def ancient_season_ids() -> set[int]:
    now = datetime.now()
    years = [year for year in range(now.year, 2011, -1)]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month > now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons) - set(recent_season_ids()) - set(older_season_ids()) - {201201}


def future_season_ids() -> set[int]:
    now = datetime.now()
    years = [year for year in range(now.year, now.year + 2)]
    months = [1, 4, 7, 10]
    seasons = []
    for year in years:
        for month in months:
            if month <= now.month and year == now.year:
                continue
            seasons.append(int(f"{year}{month:02d}"))
    return set(seasons[:1])


async def trigger_deploy_hooks() -> None:
    """触发Cloudflare Pages的部署hooks"""
    if not config.cf_pages_hooks:
        logger.info("未配置Cloudflare Pages deploy hooks，跳过触发")
        return

    async with httpx.AsyncClient() as client:
        payload: dict[str, Any] = {}
        results = await client.post(config.cf_pages_hooks, json=payload)

        if results.is_success:
            logger.success(f"成功触发hook, 状态码: {results.status_code}")
        else:
            logger.error(
                f"触发hook失败, 状态码: {results.status_code}, 响应: {results.text}"
            )


if __name__ == "__main__":
    print(current_season_id())
    print(sorted(list(future_season_ids())))
    print(sorted(list(recent_season_ids())))
    print(sorted(list(older_season_ids())))
    print(sorted(list(ancient_season_ids())))
