import re
from datetime import date, datetime

from loguru import logger
from returns.result import Failure, Result, Success

from app.services.bgmtv.api import get_episodes, get_index, get_subject
from app.services.bgmtv.models import PagedEpisode, PagedIndexSubject
from app.services.bgmtv.models import Subject as BGMTVSubject
from app.services.db import Subject as DBSubject


class BGMTVClient:
    def __init__(self) -> None:
        pass

    def _parse_image(self, subject: BGMTVSubject) -> tuple[str | None, str | None]:
        if subject.images:
            grid = subject.images.grid
            large = subject.images.large
        else:
            grid = None
            large = None
        return grid, large

    def _parse_rating(self, subject: BGMTVSubject) -> tuple[int | None, float | None]:
        if subject.rating:
            rank = subject.rating.rank
            if (
                subject.rating.count
                and subject.rating.total
                and subject.rating.total > 0
            ):
                total_score = 0
                for key, value in subject.rating.count.items():
                    total_score += key * value
                score = total_score / subject.rating.total
            elif subject.rating.score:
                score = subject.rating.score
            else:
                score = None
        else:
            rank = None
            score = None
        return rank, score

    def _parse_collection(
        self, subject: BGMTVSubject
    ) -> tuple[int | None, float | None]:
        if subject.collection:
            total = (
                subject.collection.collect
                + subject.collection.wish
                + subject.collection.doing
                + subject.collection.on_hold
                + subject.collection.dropped
            )
            if total > 0:
                drop_rate = subject.collection.dropped / total
            else:
                drop_rate = None
        else:
            total = None
            drop_rate = None
        return total, drop_rate

    def _parse_air_weekday(self, subject: BGMTVSubject) -> str | None:
        if subject.infobox:
            for item in subject.infobox:
                if item.key == "放送星期":
                    return item.value
        return None

    def _parse_episodes(self, episodes: PagedEpisode) -> float:
        if not episodes or not episodes.data:
            return 0.0

        current_date = datetime.now().date()
        total_aired = 0.0
        total_comments = 0.0
        for episode in episodes.data:
            if episode.airdate:
                wrapped_airdate = self._parse_airdate(episode.airdate)
                match wrapped_airdate:
                    case Failure(e):
                        logger.warning(f"无效的播出日期格式: {episode.airdate}, {e}")
                        continue
                    case Success(airdate):
                        if airdate <= current_date and episode.comment:
                            total_aired += 1.0
                            total_comments += float(episode.comment)
            else:
                continue
        if total_aired > 0:
            return total_comments / total_aired
        else:
            return 0.0

    async def _parse_average_comment(self, subject: BGMTVSubject) -> float:
        # cuz redirect, use subject.id instead of subject_id
        wrapped_episodes = await get_episodes(subject.id, 0, 100, 0)
        match wrapped_episodes:
            case Failure(e):
                logger.warning(f"获取 {subject.id} 集数失败: {e}")
                average_comment = 0.0
            case Success(episodes):
                average_comment = self._parse_episodes(episodes)
        return average_comment

    async def get_subject_details(
        self, subject_id: int
    ) -> Result[DBSubject, Exception]:
        wrapped_subject = await get_subject(subject_id)
        match wrapped_subject:
            case Failure(e):
                return Failure(e)
            case Success(_subject):
                subject: BGMTVSubject = _subject

        grid, large = self._parse_image(subject)
        rank, score = self._parse_rating(subject)
        total, drop_rate = self._parse_collection(subject)
        air_weekday = self._parse_air_weekday(subject)
        average_comment = await self._parse_average_comment(subject)

        return Success(
            DBSubject(
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
                meta_tags=subject.meta_tags,
                updated_at=datetime.now(),
            )
        )

    def _parse_airdate(self, airdate_str: str) -> Result[date, Exception]:
        """解析各种格式的播出日期"""
        if not airdate_str:
            return Failure(Exception("Invalid airdate"))

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
                return Success(datetime.strptime(cleaned, fmt).date())
            except ValueError:
                continue

        # 处理不规范的格式，如 "2013/6/8"，"2013-6-8"，"2013年6月8日"
        slash_match = re.match(
            r"^(\d{4})[/-年](\d{1,2})[/-月](\d{1,2})[/-日]?$", cleaned
        )
        if slash_match:
            try:
                year, month, day = map(int, slash_match.groups())
                return Success(datetime(year, month, day).date())
            except ValueError:
                pass

        return Failure(Exception("Invalid airdate"))

    async def get_index_subject_ids(
        self, index_id: int
    ) -> Result[list[int], Exception]:
        wrapped_index = await get_index(
            index_id=index_id, subject_type=2, limit=100, offset=0
        )
        match wrapped_index:
            case Failure(e):
                return Failure(e)
            case Success(_index):
                index: PagedIndexSubject = _index

        return Success([subject.id for subject in index.data])
