import json
import re
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger

from app.config import config
from app.services import bgmtv, db, yucwiki
from app.services.bgmtv import get_episodes, get_subject
from app.services.db.client import db_client
from app.services.ds.client import ds_client

security = HTTPBasic()


def parse_airdate(airdate_str: str) -> datetime.date | None:
    """解析各种格式的播出日期"""
    if not airdate_str:
        return None

    # 清理字符串：移除额外空格
    cleaned = airdate_str.strip()

    # 处理包含多个日期的情况，取第一个日期
    if "/" in cleaned and ("(" in cleaned or "（" in cleaned):
        # 格式如: "2015-02-01(一部地域のみ)/2015-02-08"
        cleaned = cleaned.split("(")[0].split("（")[0].strip()

    # 处理空格问题
    cleaned = re.sub(r"\s+", "", cleaned)

    # 尝试各种日期格式
    date_formats = [
        "%Y-%m-%d",  # 2015-02-01
        "%Y/%m/%d",  # 2015/02/01
        "%Y年%m月%d日",  # 2015年02月01日
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    # 处理不规范的格式，如 "2013/6/8"，"2013-6-8"，"2013年6月8日"
    slash_match = re.match(r"^(\d{4})[/-年](\d{1,2})[/-月](\d{1,2})[/-日]?$", cleaned)
    if slash_match:
        try:
            year, month, day = map(int, slash_match.groups())
            return datetime(year, month, day).date()
        except ValueError:
            pass

    return None


def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """验证API密码的依赖项"""
    if credentials.password != config.api_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


async def search_subjects_by_yucwiki(yucwiki_list: list[yucwiki.YucWiki]) -> list[int]:
    subjects = []
    for yuc_info in yucwiki_list:
        # 先检查数据库中是否存在
        db_yucwiki = db_client.get_yucwiki(yuc_info.jp_title)
        if db_yucwiki is not None:
            subjects.append(db_yucwiki.subject_id)
            continue
        # 如果数据库中不存在，则搜索 bangumi 并插入数据库
        paged_subject = await bgmtv.search_subject_by_name(yuc_info.jp_title)
        for subject in paged_subject.data:
            if subject.name == yuc_info.jp_title:
                subjects.append(subject.id)
                db_client.insert_yucwiki(
                    db.YucWiki(
                        jp_title=yuc_info.jp_title,
                        subject_id=subject.id,
                    )
                )
                break
        else:
            # 如果 bangumi 中无法精准匹配，则搜索 ds 并插入数据库
            subject_id = await ds_client.get_subject_id(yuc_info, paged_subject)
            if subject_id != -1:
                subjects.append(subject_id)
                db_client.insert_yucwiki(
                    db.YucWiki(
                        jp_title=yuc_info.jp_title,
                        subject_id=subject_id,
                    )
                )
            else:
                logger.error(
                    f"获取 bangumi subject id 失败，请人工干预处理: {yuc_info}"
                )
    return subjects


async def get_subject_detail(subject_id: int) -> db.Subject:
    """获取条目详情"""
    subject = await get_subject(subject_id)

    if subject.images:
        grid = subject.images.grid
        large = subject.images.large

    if subject.rating:
        rank = subject.rating.rank
        if subject.rating.count and subject.rating.total:
            total_score = 0
            for key, value in subject.rating.count.items():
                total_score += key * value
            score = total_score / subject.rating.total
        else:
            score = subject.rating.score
    else:
        rank = None
        score = None

    if subject.collection:
        total = (
            subject.collection.collect
            + subject.collection.wish
            + subject.collection.doing
            + subject.collection.on_hold
            + subject.collection.dropped
        )
        drop_rate = subject.collection.dropped / total
    else:
        total = None
        drop_rate = None

    # 处理infobox字段，仅保留"放送星期"
    air_weekday = None
    if subject.infobox:
        for item in subject.infobox:
            if item.key == "放送星期":
                air_weekday = item.value

    # cuz redirect, use subject.id instead of subject_id
    episodes = await get_episodes(subject.id, 0, 100, 0)
    if not episodes or not episodes.data:
        average_comment = 0
    else:
        current_date = datetime.now().date()
        aired_episodes = []
        total_comments = 0

        for episode in episodes.data:
            # 检查是否有播出日期
            if episode.airdate:
                try:
                    airdate = parse_airdate(episode.airdate)
                    if airdate and airdate <= current_date:
                        episode_info = {
                            "ep": episode.ep,
                            "comments": episode.comment,
                        }
                        aired_episodes.append(episode_info)
                        if episode.comment:
                            total_comments += episode.comment
                except Exception:
                    logger.warning(f"无效的播出日期格式: {episode.airdate}")

        if aired_episodes:
            average_comment = total_comments / len(aired_episodes)
        else:
            average_comment = 0

    subject = db.Subject(
        id=subject.id,
        name=subject.name,
        name_cn=subject.name_cn,
        images_grid=grid,
        images_large=large,
        rank=rank,
        score=score,
        collection_total=total,
        average_comment=average_comment,
        drop_rate=drop_rate,
        air_weekday=air_weekday,
        meta_tags=json.dumps(subject.meta_tags),
        updated_at=datetime.now(),
    )
    return subject


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
    return (
        set(seasons) - set(recent_season_ids()) - set(older_season_ids()) - {"201201"}
    )


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


if __name__ == "__main__":
    import asyncio

    async def main():
        subject_id = 486347
        subject_data = await get_subject_detail(subject_id)
        print(subject_data)

    asyncio.run(main())

    print(current_season_id())
    print(sorted(list(future_season_ids())))
    print(sorted(list(recent_season_ids())))
    print(sorted(list(older_season_ids())))
    print(sorted(list(ancient_season_ids())))
