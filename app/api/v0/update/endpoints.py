import sqlite3
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from loguru import logger

from app.api.v0.update import models
from app.api.v0.utils import get_subject_detail
from app.services import bgmtv, db, youranimestw
from app.utils import (
    future_season_ids,
    recent_season_ids,
)

router = APIRouter(prefix="/update", tags=["update"])


async def get_db_conn(request: Request) -> sqlite3.Connection:
    """获取Redis客户端的依赖注入函数"""
    return request.app.state.db_conn


@router.post("/future_seasons")
async def update_future_seasons(
    _: models.Empty, db_conn: sqlite3.Connection = Depends(get_db_conn)
):
    season_ids = future_season_ids()
    for season_id in season_ids:
        index = db.get_index(db_conn, season_id)
        if index is None:
            try:
                create_index_response = await bgmtv.create_index()
                index_id = create_index_response.id
                await bgmtv.update_index(
                    create_index_response.id,
                    bgmtv.IndexBasicInfo(
                        title=f"Season {season_id}",
                        description=f"auto updated at {datetime.now().isoformat()}",
                    ),
                )
                db.insert_index(
                    db_conn, db.Index(season_id=season_id, index_id=index_id)
                )
            except Exception as e:
                logger.error(f"创建 {season_id} 索引失败: {e}")
                continue
        try:
            anime_list = await youranimestw.get_anime_list(season_id)
            for anime_name in anime_list:
                target_subject_id = None
                subjects = await bgmtv.search_subjects(
                    bgmtv.SearchRequest(
                        keyword=anime_name, filter=bgmtv.SearchFilter.from_type(2)
                    )
                )
                for subject in subjects.data:
                    if anime_name == subject.name:
                        target_subject_id = subject.id
                        break
                if target_subject_id is None:
                    logger.warning(f"未找到 {anime_name} 的条目")
                    continue
                logger.info(f"找到 {anime_name} 的条目: {target_subject_id}")
                await bgmtv.add_subject_to_index(
                    index_id,
                    bgmtv.AddSubjectToIndexRequest(
                        subject_id=target_subject_id, sort=0, comment=""
                    ),
                )
                if subject_data := db.get_subject(db_conn, target_subject_id):
                    if subject_data.updated_at < datetime.now() - timedelta(days=1):
                        subject_data = await get_subject_detail(target_subject_id)
                        db.update_subject(db_conn, subject_data)
        except Exception as e:
            logger.error(f"获取 {season_id} 动画列表失败: {e}")
            continue
    return "ok"


@router.post("/recent_seasons")
async def update_season(
    _: models.Empty, db_conn: sqlite3.Connection = Depends(get_db_conn)
):
    season_ids = recent_season_ids()
    for season_id in season_ids:
        index = db.get_index(db_conn, season_id)
        if index is None:
            logger.error(f"未找到 {season_id} 索引")
            continue
        try:
            paged_index_subject = await bgmtv.get_index(index.index_id, 2, 100, 0)
            for subject in paged_index_subject.data:
                if subject_data := db.get_subject(db_conn, subject.id):
                    if subject_data.updated_at < datetime.now() - timedelta(days=1):
                        subject_data = await get_subject_detail(subject.id)
                        db.update_subject(db_conn, subject_data)
        except Exception as e:
            logger.error(f"获取 {season_id} 索引条目失败: {e}")
            continue
    return "ok"


@router.post("/older_seasons")
async def update_older_seasons(_: models.Empty):
    raise NotImplementedError("Not implemented")


@router.post("/all_seasons")
async def update_all_seasons(_: models.Empty):
    raise NotImplementedError("Not implemented")


@router.post("/season2index")
async def update_season2index(
    request: models.Season2IndexRequest,
    db_conn: sqlite3.Connection = Depends(get_db_conn),
):
    index = db.get_index(db_conn, request.season_id)
    if index is None:
        logger.error(f"未找到 {request.season_id} 索引")
        db.insert_index(
            db_conn, db.Index(season_id=request.season_id, index_id=request.index_id)
        )
        return "created"
    elif index.index_id == request.index_id:
        return "existed"
    else:
        return f"error exsisted {index.index_id} != request {request.index_id}"
