import json
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
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
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_password),
):
    season_ids = list(future_season_ids())
    background_tasks.add_task(update_multiple_seasons_subjects, season_ids, "future")
    logger.info("未来季度条目更新任务已启动")
    return {"message": "未来季度条目更新任务已在后台启动", "status": "started"}


@router.post("/subjects/recent_seasons")
async def update_recent_season_subjects(
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_password),
):
    season_ids = list(recent_season_ids())
    background_tasks.add_task(update_multiple_seasons_subjects, season_ids, "recent")
    logger.info("近期季度条目更新任务已启动")
    return {"message": "近期季度条目更新任务已在后台启动", "status": "started"}


@router.post("/subjects/older_seasons")
async def update_older_season_subjects(
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_password),
):
    season_ids = list(older_season_ids())
    background_tasks.add_task(update_multiple_seasons_subjects, season_ids, "older")
    logger.info("较旧季度条目更新任务已启动")
    return {"message": "较旧季度条目更新任务已在后台启动", "status": "started"}


@router.post("/subjects/ancient_seasons")
async def update_ancient_season_subjects(
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_password),
):
    season_ids = list(ancient_season_ids())
    background_tasks.add_task(update_multiple_seasons_subjects, season_ids, "ancient")
    logger.info("古老季度条目更新任务已启动")
    return {"message": "古老季度条目更新任务已在后台启动", "status": "started"}


async def update_multiple_seasons_subjects(season_ids: list[int], task_name: str):
    """后台任务：批量更新多个季度的条目"""
    logger.info(f"开始执行 {task_name} 季度条目更新任务，共 {len(season_ids)} 个季度")
    try:
        for season_id in season_ids:
            await update_season_subjects(season_id)
        logger.info(f"{task_name} 季度条目更新任务完成")
    except Exception as e:
        logger.error(f"{task_name} 季度条目更新任务失败: {e}")


async def scheduled_update_all_subjects():
    """供调度器调用的更新所有条目函数"""
    logger.info("定时任务：开始更新所有条目")
    try:
        all_season_ids = list(
            future_season_ids()
            | recent_season_ids()
            | older_season_ids()
            | ancient_season_ids()
        )
        await update_multiple_seasons_subjects(all_season_ids, "scheduled_all")
        logger.info("定时任务：所有条目更新完成")
    except Exception as e:
        logger.error(f"定时任务：更新所有条目失败: {e}")


@router.post("/subjects/all")
async def update_all_subjects(
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_password),
):
    # 将所有季度的更新作为一个后台任务
    all_season_ids = list(
        future_season_ids()
        | recent_season_ids()
        | older_season_ids()
        | ancient_season_ids()
    )
    background_tasks.add_task(update_multiple_seasons_subjects, all_season_ids, "all")
    logger.info("全部条目更新任务已启动")
    return {"message": "全部条目更新任务已在后台启动", "status": "started"}
