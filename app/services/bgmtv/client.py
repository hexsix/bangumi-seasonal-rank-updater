import re
from datetime import date, datetime

from loguru import logger
from returns.result import Failure, Result, Success

from app.services import bgmtv, db
from app.services.bgmtv.api import get_episodes, get_subject


class BGMTVClient:
    def __init__(self) -> None:
        pass

    async def get_subject_details(
        self, subject_id: int
    ) -> Result[db.Subject, Exception]:
        wrapped_subject = await get_subject(subject_id)
        match wrapped_subject:
            case Failure(e):
                return Failure(e)
            case Success(subject):
                subject: bgmtv.Subject = subject

        if subject.images:
            grid = subject.images.grid
            large = subject.images.large
        else:
            grid = None
            large = None

        if subject.rating:
            rank = subject.rating.rank
            if subject.rating.count and subject.rating.total:
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
        else:
            air_weekday = None

        # cuz redirect, use subject.id instead of subject_id
        wrapped_episodes = await get_episodes(subject.id, 0, 100, 0)
        match wrapped_episodes:
            case Failure(e):
                average_comment = 0.0
            case Success(episodes):
                if not episodes or not episodes.data:
                    average_comment = 0.0
                else:
                    current_date = datetime.now().date()
                    aired_episodes = []
                    total_comments = 0.0

                    for episode in episodes.data:
                        # 检查是否有播出日期
                        if episode.airdate:
                            try:
                                wrapped_airdate = self._parse_airdate(episode.airdate)
                                match wrapped_airdate:
                                    case Failure(e):
                                        logger.warning(
                                            f"无效的播出日期格式: {episode.airdate}, {e}"
                                        )
                                        continue
                                    case Success(airdate):
                                        if airdate and airdate <= current_date:
                                            episode_info = {
                                                "ep": episode.ep,
                                                "comments": episode.comment,
                                            }
                                            aired_episodes.append(episode_info)
                                            if episode.comment:
                                                total_comments += float(episode.comment)
                            except Exception as e:
                                logger.warning(
                                    f"无效的播出日期格式: {episode.airdate}, {e}"
                                )
                                if airdate and airdate <= current_date:
                                    episode_info = {
                                        "ep": episode.ep,
                                        "comments": episode.comment,
                                    }
                                    aired_episodes.append(episode_info)
                                    if episode.comment:
                                        total_comments += float(episode.comment)

                    if aired_episodes:
                        average_comment = total_comments / float(len(aired_episodes))
                    else:
                        average_comment = 0.0

        return Success(
            db.Subject(
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
