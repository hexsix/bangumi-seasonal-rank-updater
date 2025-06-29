import asyncio
import functools
import random
from typing import Callable, TypeVar

import httpx
from loguru import logger

from app.config import config
from app.services.bgmtv.models import (
    AddSubjectToIndexRequest,
    Index,
    IndexBasicInfo,
    IndexSubject,
    PagedEpisode,
    PagedIndexSubject,
    PagedSubject,
    SearchRequest,
    Subject,
)

DEFAULT_USER_AGENT = (
    "rinshankaiho.fun (https://github.com/hexsix/bangumi-seasonal-rank-updater)"
)

BASE_URL = "https://api.bgm.tv"

T = TypeVar("T")


def retry_on_failure(max_retries: int = 3):
    """
    重试装饰器，在API调用失败时重试指定次数

    Args:
        max_retries: 最大重试次数，默认3次
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):  # +1 因为第一次不算重试
                try:
                    return await func(*args, **kwargs)
                except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:
                    last_exception = e

                    if attempt < max_retries:
                        # 指数退避，增加随机性避免雷群效应
                        delay = (2**attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"API调用失败，第 {attempt + 1} 次重试，{delay:.2f}秒后重试: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"API调用失败，已达到最大重试次数 {max_retries}")

            # 如果所有重试都失败了，抛出最后一个异常
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def _get_headers() -> dict:
    """获取请求头"""
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
    }

    if config.bgmtv_token:
        headers["Authorization"] = f"Bearer {config.bgmtv_token}"

    return headers


@retry_on_failure(max_retries=3)
async def get_episodes(
    subject_id: int,
    episode_type: int,
    limit: int,
    offset: int,
) -> PagedEpisode:
    """
    获取剧集信息

    GET /v0/episodes

    Args:
        subject_id: 条目ID
        episode_type: 剧集类型 (本篇=0 特别篇=1 OP=2 ED=3 预告/宣传/广告=4 MAD=5 其他=6)
        limit: 每页数量
        offset: 偏移量

    Returns:
        PagedEpisode: 分页剧集数据

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info(f"正在获取条目 {subject_id} 的剧集信息")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/episodes"
    params = {
        "subject_id": subject_id,
        "type": episode_type,
        "limit": limit,
        "offset": offset,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        try:
            data = response.json()
            return PagedEpisode(**data)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"响应内容: {response.text}")
            raise ValueError(f"解析JSON失败: {e}")


@retry_on_failure(max_retries=3)
async def get_index(
    index_id: int,
    subject_type: int,
    limit: int,
    offset: int,
) -> PagedIndexSubject:
    """
    获取索引中的条目

    GET /v0/indices/{index_id}/subjects

    Args:
        index_id: 索引ID
        subject_type: 条目类型 (1=book, 2=anime, 3=music, 4=game, 6=real)
        limit: 每页数量
        offset: 偏移量

    Returns:
        PagedIndexSubject: 分页索引条目数据

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info(f"正在获取索引 {index_id} 的条目信息")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/indices/{index_id}/subjects"
    params = {
        "type": subject_type,
        "limit": limit,
        "offset": offset,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params=params,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        try:
            data = response.json()
            return PagedIndexSubject(**data)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"响应内容: {response.text}")
            raise ValueError(f"解析JSON失败: {e}")


@retry_on_failure(max_retries=3)
async def get_subject(subject_id: int) -> Subject:
    """
    获取条目详细信息

    GET /v0/subjects/{subject_id}

    Args:
        subject_id: 条目ID

    Returns:
        Subject: 条目详细信息

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info(f"正在获取条目 {subject_id} 的详细信息")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/subjects/{subject_id}"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        try:
            data = response.json()
            return Subject(**data)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"响应内容: {response.text}")
            raise ValueError(f"解析JSON失败: {e}")


@retry_on_failure(max_retries=3)
async def search_subjects(
    search_request: SearchRequest,
    limit: int = 10,
    offset: int = 0,
) -> PagedSubject:
    """
    搜索条目

    POST /v0/search/subjects

    实验性 API，本 schema 和实际的 API 行为都可能随时发生改动

    Args:
        search_request: 搜索请求，包含关键字、排序和筛选条件
        limit: 每页数量，默认25
        offset: 偏移量，默认0

    Returns:
        PagedSubject: 分页条目搜索结果

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info(f"正在搜索条目，关键字: {search_request.keyword}")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/search/subjects"
    params = {
        "limit": limit,
        "offset": offset,
    }

    # 构建请求体
    request_body = search_request.model_dump(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            params=params,
            json=request_body,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        try:
            data = response.json()
            return PagedSubject(**data)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"响应内容: {response.text}")
            raise ValueError(f"解析JSON失败: {e}")


@retry_on_failure(max_retries=3)
async def create_index() -> Index:
    """
    创建新目录

    POST /v0/indices

    Returns:
        Index: 创建的目录信息

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info("正在创建新目录")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/indices"

    # 构建请求体
    request_body = {}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=request_body,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        try:
            data = response.json()
            return Index(**data)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"响应内容: {response.text}")
            raise ValueError(f"解析JSON失败: {e}")


@retry_on_failure(max_retries=3)
async def update_index(index_id: int, basic_info: IndexBasicInfo) -> None:
    """
    修改目录信息

    PUT /v0/indices/{index_id}

    Args:
        index_id: 目录ID
        basic_info: 目录基本信息，包含标题和描述

    Returns:
        None

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info(f"正在修改目录 {index_id} 的信息")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/indices/{index_id}"

    # 构建请求体
    request_body = basic_info.model_dump(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.put(
            url,
            json=request_body,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        return None


@retry_on_failure(max_retries=3)
async def add_subject_to_index(
    index_id: int, request: AddSubjectToIndexRequest
) -> IndexSubject:
    """
    向目录添加条目

    POST /v0/indices/{index_id}/subjects

    Args:
        index_id: 目录ID
        request: 添加条目请求，包含条目ID、排序和评论

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败时
    """
    logger.info(f"正在向目录 {index_id} 添加条目 {request.subject_id}")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/indices/{index_id}/subjects"

    # 构建请求体
    request_body = request.model_dump(exclude_none=True)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=request_body,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        try:
            data = response.json()
            return IndexSubject(**data)
        except Exception as e:
            logger.error(f"解析JSON失败: {e}")
            logger.error(f"响应内容: {response.text}")
            raise ValueError(f"解析JSON失败: {e}")


@retry_on_failure(max_retries=3)
async def remove_subject_from_index(index_id: int, subject_id: int) -> None:
    """
    从目录删除条目

    DELETE /v0/indices/{index_id}/subjects/{subject_id}

    Args:
        index_id: 目录ID
        subject_id: 条目ID

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
    """
    logger.info(f"正在从目录 {index_id} 删除条目 {subject_id}")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/indices/{index_id}/subjects/{subject_id}"

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            url,
            headers=_get_headers(),
        )

        if not response.is_success:
            logger.error(f"BGM API 返回状态码: {response.status_code}")
            response.raise_for_status()

        return None


if __name__ == "__main__":
    import asyncio
    import json

    from app.services.bgmtv.models import SearchFilter

    keyword = "よふかしのうた 第2期"

    response = asyncio.run(
        search_subjects(
            SearchRequest(
                keyword=keyword,
                filter=SearchFilter.from_type(2),
            )
        )
    )

    logger.info(response)
    json.dump(
        response.model_dump(),
        open("response.json", "w", encoding="utf-8"),
        ensure_ascii=False,
    )
