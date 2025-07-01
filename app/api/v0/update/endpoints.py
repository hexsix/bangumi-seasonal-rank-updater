import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from app.api.v0.update import models
from app.api.v0.utils import (
    ancient_season_ids,
    future_season_ids,
    get_subject_detail,
    older_season_ids,
    recent_season_ids,
    search_subjects_by_yucwiki,
    verify_password,
)
from app.services import bgmtv, db, yucwiki
from app.services.db.client import db_client

router = APIRouter(prefix="/update", tags=["update"])


@router.post("/index")
async def update_season2index(
    request: models.Season2IndexRequest,
    _: bool = Depends(verify_password),
):
    index = db_client.get_index(request.season_id)
    if index is None:
        paged_index_subject = await bgmtv.get_index(request.index_id, 2, 100, 0)
        subject_ids = [subject.id for subject in paged_index_subject.data]
        db_client.insert_index(
            db.Index(
                season_id=request.season_id,
                index_id=request.index_id,
                subject_ids=json.dumps(subject_ids),
            )
        )
        logger.info(f"未找到 {request.season_id} 索引，已创建")
        return "created"
    elif index.index_id == request.index_id:
        paged_index_subject = await bgmtv.get_index(request.index_id, 2, 100, 0)
        subject_ids = [subject.id for subject in paged_index_subject.data]
        db_client.upgrade_index(
            db.Index(
                season_id=request.season_id,
                index_id=request.index_id,
                subject_ids=json.dumps(subject_ids),
            )
        )
        logger.info(f"{request.season_id} 索引已存在，已更新")
        return "updated"
    else:
        logger.error(
            f"索引已存在，但 index_id 不一致: {index.index_id} != {request.index_id}"
        )
        raise HTTPException(
            status_code=409, detail="Conflict: 索引已存在，但 index_id 不一致"
        )


@router.post("/index/from_yucwiki")
async def update_from_yucwiki(
    request: models.Season2IndexRequest,
    _: bool = Depends(verify_password),
):
    index = db_client.get_index(request.season_id)
    if index is None or index.index_id == request.index_id:
        yucwiki_list = await yucwiki.get_anime_list(request.season_id)
        subject_ids_from_yucwiki = await search_subjects_by_yucwiki(yucwiki_list)
        subject_ids_from_bgm = await bgmtv.get_index(request.index_id, 2, 100, 0)
        subject_to_delete = [
            subject.id
            for subject in subject_ids_from_bgm.data
            if subject.id not in subject_ids_from_yucwiki
        ]
        for subject_id in subject_to_delete:
            await bgmtv.remove_subject_from_index(request.index_id, subject_id)
        subject_to_add = [
            subject_id
            for subject_id in subject_ids_from_yucwiki
            if subject_id not in subject_ids_from_bgm.data
        ]
        for subject_id in subject_to_add:
            await bgmtv.add_subject_to_index(request.index_id, subject_id)
        if index is None:
            db_client.insert_index(
                db.Index(
                    season_id=request.season_id,
                    index_id=request.index_id,
                    subject_ids=json.dumps(subject_ids_from_yucwiki),
                )
            )
            logger.info(f"未找到 {request.season_id} 索引，已创建")
            return "created"
        elif index.index_id == request.index_id:
            db_client.upgrade_index(
                db.Index(
                    season_id=request.season_id,
                    index_id=request.index_id,
                    subject_ids=json.dumps(subject_ids_from_yucwiki),
                )
            )
            logger.info(f"{request.season_id} 索引已存在，已更新")
            return "updated"
    else:
        logger.error(
            f"索引已存在，但 index_id 不一致: {index.index_id} != {request.index_id}"
        )
        raise HTTPException(
            status_code=409, detail="Conflict: 索引已存在，但 index_id 不一致"
        )


@router.post("/index/recent_seasons")
async def update_season(
    _: models.Empty,
    __: bool = Depends(verify_password),
):
    season_ids = recent_season_ids()
    for season_id in season_ids:
        index = db_client.get_index(season_id)
        if index is None:
            logger.error(f"未找到 {season_id} 索引")
            continue
        try:
            paged_index_subject = await bgmtv.get_index(index.index_id, 2, 100, 0)
            subject_ids = [subject.id for subject in paged_index_subject.data]
            db_client.upgrade_index(
                db.Index(
                    season_id=season_id,
                    index_id=index.index_id,
                    subject_ids=json.dumps(subject_ids),
                )
            )
        except Exception as e:
            logger.error(f"获取 {season_id} 索引条目失败: {e}")
            continue
    return "ok"


@router.post("/index/older_seasons")
async def update_older_seasons(
    _: models.Empty,
    __: bool = Depends(verify_password),
):
    season_ids = older_season_ids()
    for season_id in season_ids:
        index = db_client.get_index(season_id)
        if index is None:
            logger.error(f"未找到 {season_id} 索引")
            continue
        try:
            paged_index_subject = await bgmtv.get_index(index.index_id, 2, 100, 0)
            subject_ids = [subject.id for subject in paged_index_subject.data]
            db_client.upgrade_index(
                db.Index(
                    season_id=season_id,
                    index_id=index.index_id,
                    subject_ids=json.dumps(subject_ids),
                )
            )
        except Exception as e:
            logger.error(f"获取 {season_id} 索引条目失败: {e}")
            continue
    return "ok"


@router.post("/index/ancient_seasons")
async def update_ancient_seasons(
    _: models.Empty,
    __: bool = Depends(verify_password),
):
    season_ids = ancient_season_ids()
    for season_id in season_ids:
        index = db_client.get_index(season_id)
        if index is None:
            logger.error(f"未找到 {season_id} 索引")
            continue
        try:
            paged_index_subject = await bgmtv.get_index(index.index_id, 2, 100, 0)
            subject_ids = [subject.id for subject in paged_index_subject.data]
            db_client.upgrade_index(
                db.Index(
                    season_id=season_id,
                    index_id=index.index_id,
                    subject_ids=json.dumps(subject_ids),
                )
            )
        except Exception as e:
            logger.error(f"获取 {season_id} 索引条目失败: {e}")
            continue
    return "ok"


async def update_season_subjects(season_id: int):
    index = db_client.get_index(season_id)
    if index is None or index.subject_ids is None:
        logger.error(f"未找到 {season_id} 索引")
        return
    subject_ids: list[int] = json.loads(index.subject_ids)
    for subject_id in subject_ids:
        subject = db_client.get_subject(subject_id)
        if subject is None:
            subject = await get_subject_detail(subject_id)
            db_client.insert_subject(subject)
            logger.info(f"不存在 {subject_id} 条目，已创建")
        else:
            updated_at = datetime.fromisoformat(subject.updated_at)
            year = season_id // 100
            month = season_id % 100
            days = (datetime.now() - datetime(year, month, 1)).days // 90
            if updated_at < datetime.now() - timedelta(days=days):
                subject = await get_subject_detail(subject_id)
                db_client.upgrade_subject(subject)
                logger.info(f"已更新 {subject_id} 条目")
            else:
                logger.info(f"{subject_id} 条目已是最新")


@router.post("/subjects/future_seasons")
async def update_future_season_subjects(
    _: bool = Depends(verify_password),
):
    season_ids = future_season_ids()
    for season_id in season_ids:
        await update_season_subjects(season_id)


@router.post("/subjects/recent_seasons")
async def update_recent_season_subjects(
    _: bool = Depends(verify_password),
):
    season_ids = recent_season_ids()
    for season_id in season_ids:
        await update_season_subjects(season_id)


@router.post("/subjects/older_seasons")
async def update_older_season_subjects(
    _: bool = Depends(verify_password),
):
    season_ids = older_season_ids()
    for season_id in season_ids:
        await update_season_subjects(season_id)


@router.post("/subjects/ancient_seasons")
async def update_ancient_season_subjects(
    _: bool = Depends(verify_password),
):
    season_ids = ancient_season_ids()
    for season_id in season_ids:
        await update_season_subjects(season_id)


@router.post("/subjects/all")
async def update_all_subjects(
    _: bool = Depends(verify_password),
):
    await update_recent_season_subjects()
    await update_older_season_subjects()
    await update_ancient_season_subjects()
    return "ok"
