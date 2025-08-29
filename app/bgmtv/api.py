import asyncio
import functools
import os
import random
import re
from datetime import datetime
from typing import Any, Callable, Coroutine, TypeVar

import httpx
from dotenv import load_dotenv
from loguru import logger

from app.bgmtv.models import (
    AddSubjectToIndexRequest,
    Index,
    IndexBasicInfo,
    IndexSubject,
    PagedEpisode,
    PagedIndexSubject,
    PagedSubject,
    SearchFilter,
    SearchRequest,
    Subject,
)

load_dotenv()

DEFAULT_USER_AGENT = (
    "rinshankaiho.fun (https://github.com/hexsix/bangumi-seasonal-rank-updater)"
)

BASE_URL = "https://api.bgm.tv"

BGM_TOKEN = os.getenv("BGM_TOKEN", "")

T = TypeVar("T")


def _extract_subject_id_from_redirect_url(redirect_url: str) -> int:
    """
    从重定向URL中提取subject_id

    Args:
        redirect_url: 重定向的URL

    Returns:
        int: 提取的subject_id

    Raises:
        ValueError: 当无法从URL中提取subject_id时
    """
    # 匹配 /v0/subjects/{subject_id} 模式
    match = re.search(r"/v0/subjects/(\d+)", redirect_url)
    if match:
        return int(match.group(1))

    # 如果是完整URL，尝试匹配完整路径
    match = re.search(r"https?://[^/]+/v0/subjects/(\d+)", redirect_url)
    if match:
        return int(match.group(1))

    raise ValueError(f"无法从重定向URL中提取subject_id: {redirect_url}")


def retry_on_failure(max_retries: int = 3):
    """
    重试装饰器，在API调用失败时重试指定次数

    Args:
        max_retries: 最大重试次数，默认3次
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, T]],
    ) -> Callable[..., Coroutine[Any, Any, T]]:
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

            # 这行代码理论上不会执行，但为了类型检查需要加上
            raise RuntimeError("未知错误")

        return wrapper

    return decorator


def _get_headers() -> dict:
    """获取请求头"""
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
    }

    if BGM_TOKEN:
        headers["Authorization"] = f"Bearer {BGM_TOKEN}"

    return headers


@retry_on_failure(max_retries=3)
async def get_episodes(
    subject_id: int,
    episode_type: int,
    limit: int,
    offset: int,
    _redirect_count: int = 0,
) -> PagedEpisode:
    """
    获取剧集信息

    GET /v0/episodes

    Args:
        subject_id: 条目ID
        episode_type: 剧集类型 (本篇=0 特别篇=1 OP=2 ED=3 预告/宣传/广告=4 MAD=5 其他=6)
        limit: 每页数量
        offset: 偏移量
        _redirect_count: 内部重定向计数，用于防止无限重定向

    Returns:
        PagedEpisode: 分页剧集数据

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败或重定向次数过多时
    """
    # 防止无限重定向
    if _redirect_count > 5:
        raise ValueError(f"重定向次数过多，已达到最大限制: {_redirect_count}")

    logger.info(f"正在获取条目 {subject_id} 的剧集信息")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/episodes"
    params = {
        "subject_id": subject_id,
        "type": episode_type,
        "limit": limit,
        "offset": offset,
    }

    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(
            url,
            params=params,
            headers=_get_headers(),
        )

        # 处理302重定向
        if response.status_code == 302:
            location = response.headers.get("location")
            if location:
                logger.info(
                    f"检测到302重定向，从条目 {subject_id} 重定向到: {location}"
                )
                try:
                    new_subject_id = _extract_subject_id_from_redirect_url(location)
                    logger.info(f"提取到新的subject_id: {new_subject_id}")
                    # 递归调用处理重定向
                    return await get_episodes(
                        new_subject_id, episode_type, limit, offset, _redirect_count + 1
                    )
                except ValueError as e:
                    logger.error(f"处理重定向失败: {e}")
                    raise ValueError(f"处理重定向失败: {e}")
            else:
                logger.error("收到302状态码但没有Location头部")
                raise ValueError("收到302状态码但没有Location头部")

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
async def get_subject(subject_id: int, _redirect_count: int = 0) -> Subject:
    """
    获取条目详细信息

    GET /v0/subjects/{subject_id}

    Args:
        subject_id: 条目ID
        _redirect_count: 内部重定向计数，用于防止无限重定向

    Returns:
        Subject: 条目详细信息

    Raises:
        httpx.HTTPStatusError: 当API返回错误状态码时
        ValueError: 当响应数据解析失败或重定向次数过多时
    """
    # 防止无限重定向
    if _redirect_count > 5:
        raise ValueError(f"重定向次数过多，已达到最大限制: {_redirect_count}")

    logger.info(f"正在获取条目 {subject_id} 的详细信息")
    await asyncio.sleep(0.2)

    url = f"{BASE_URL}/v0/subjects/{subject_id}"

    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(
            url,
            headers=_get_headers(),
        )

        # 处理302重定向
        if response.status_code == 302:
            location = response.headers.get("location")
            if location:
                logger.info(
                    f"检测到302重定向，从条目 {subject_id} 重定向到: {location}"
                )
                try:
                    new_subject_id = _extract_subject_id_from_redirect_url(location)
                    logger.info(f"提取到新的subject_id: {new_subject_id}")
                    # 递归调用处理重定向
                    return await get_subject(new_subject_id, _redirect_count + 1)
                except ValueError as e:
                    logger.error(f"处理重定向失败: {e}")
                    raise ValueError(f"处理重定向失败: {e}")
            else:
                logger.error("收到302状态码但没有Location头部")
                raise ValueError("收到302状态码但没有Location头部")

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


async def search_anime(keyword: str) -> PagedSubject:
    return await search_subjects(
        SearchRequest(
            keyword=keyword,
            filter=SearchFilter.from_type(2),
        )
    )


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
async def _add_subject_to_index(
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


async def add_subject_to_index(index_id: int, subject_id: int) -> IndexSubject:
    """
    向目录添加条目
    """
    return await _add_subject_to_index(
        index_id,
        AddSubjectToIndexRequest(subject_id=subject_id, sort=0, comment="auto updated"),
    )


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


async def create_index_and_info(year: int, season: str) -> int:
    index = await create_index()
    await update_index(
        index.id,
        IndexBasicInfo(
            title=f"{year} {season}",
            description=f"https://anilist.co/search/anime?year={year}&season={season}&format=TV",
        ),
    )
    return index.id


async def search_subject_by_name(name: str) -> PagedSubject:
    paged_subject = await search_subjects(
        SearchRequest(
            keyword=name,
            filter=SearchFilter.from_type(2),
        )
    )
    return paged_subject


def test_search_subject_by_name():
    import asyncio

    from app.bgmtv.models import SearchFilter

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


async def test_redirect():
    response = await get_subject(174544)
    logger.info(response)

    response = await get_episodes(203861, 0, 10, 0)
    logger.info(response)


if __name__ == "__main__":
    asyncio.run(test_redirect())
