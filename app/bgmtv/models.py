from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Collection(BaseModel):
    """收藏统计信息"""

    wish: int = Field(description="想看")
    collect: int = Field(description="看过")
    doing: int = Field(description="在看")
    on_hold: int = Field(description="搁置")
    dropped: int = Field(description="抛弃")


class Episode(BaseModel):
    """剧集信息"""

    id: int
    type: int = Field(
        description="本篇=0 特别篇=1 OP=2 ED=3 预告/宣传/广告=4 MAD=5 其他=6",
    )
    name: Optional[str] = Field(None, description="剧集名称")
    name_cn: Optional[str] = Field(None, description="剧集中文名称")
    sort: Optional[float] = Field(None, description="同类条目的排序和集数")
    ep: Optional[float] = Field(
        None, description="条目内的集数, 从1开始。非本篇剧集的此字段无意义"
    )
    airdate: Optional[str] = Field(None, description="播出日期 YYYY-MM-DD 格式")
    comment: Optional[int] = Field(None, description="评论")
    duration: Optional[str] = Field(None, description="时长")
    desc: Optional[str] = Field(None, description="简介")
    disc: Optional[int] = Field(None, description="音乐曲目的碟片数")
    duration_seconds: Optional[int] = Field(None, description="时长秒数")
    subject_id: Optional[int] = Field(None, description="条目ID")


class ErrorDetail(BaseModel):
    """错误详情"""

    title: Optional[str] = Field(None, description="错误标题")
    description: Optional[str] = Field(None, description="错误描述")
    details: Optional[str] = Field(None, description="错误详情")


class Images(BaseModel):
    """图片信息"""

    large: Optional[str] = Field(None, description="大图")
    common: Optional[str] = Field(None, description="通用图")
    medium: Optional[str] = Field(None, description="中图")
    small: Optional[str] = Field(None, description="小图")
    grid: Optional[str] = Field(None, description="网格图")


class InfoboxItem(BaseModel):
    """信息框项目"""

    key: Optional[str] = Field(None, description="键")
    value: Optional[Any] = Field(None, description="值")


class IndexSubject(BaseModel):
    """索引条目"""

    id: int = Field(description="条目ID")
    type: Optional[int] = Field(
        None, description="1=book, 2=anime, 3=music, 4=game, 6=real"
    )
    name: Optional[str] = Field(None, description="条目名称")
    name_cn: Optional[str] = Field(None, description="条目中文名称")
    comment: Optional[str] = Field(None, description="评论")
    images: Optional[Images] = Field(None, description="图片")
    infobox: Optional[List[InfoboxItem]] = Field(None, description="信息框")
    date: Optional[str] = Field(None, description="上映日期 YYYY-MM-DD 格式")
    added_at: datetime = Field(description="创建时间")


class PagedEpisode(BaseModel):
    """分页剧集数据"""

    total: int
    limit: int
    offset: int
    data: List[Episode]


class PagedIndexSubject(BaseModel):
    """分页索引条目数据"""

    total: int
    limit: int
    offset: int
    data: List[IndexSubject]


class Rating(BaseModel):
    """评分信息"""

    rank: Optional[int] = Field(None, description="排名")
    total: Optional[int] = Field(None, description="总评分人数")
    count: Optional[Dict[int, int]] = Field(None, description="评分人数")
    score: Optional[float] = Field(None, description="评分")


class Tag(BaseModel):
    """标签"""

    name: Optional[str] = Field(None, description="标签名称")
    count: Optional[int] = Field(None, description="标签数量")


class Subject(BaseModel):
    """条目信息"""

    id: int = Field(description="条目ID")
    type: int = Field(description="1=book, 2=anime, 3=music, 4=game, 6=real")
    name: Optional[str] = Field(None, description="条目名称")
    name_cn: Optional[str] = Field(None, description="条目中文名称")
    summary: Optional[str] = Field(None, description="简介")
    series: Optional[bool] = Field(None, description="是否为系列")
    nsfw: Optional[bool] = Field(None, description="是否包含NSFW内容")
    locked: Optional[bool] = Field(None, description="是否锁定")
    date: Optional[str] = Field(None, description="上映日期 YYYY-MM-DD 格式")
    platform: Optional[str] = Field(
        None, description="播放平台 TV, Web, 欧美剧, DLC..."
    )
    images: Optional[Images] = Field(None, description="图片")
    infobox: Optional[List[InfoboxItem]] = Field(None, description="信息框")
    volumes: Optional[int] = Field(None, description="卷数")
    eps: Optional[int] = Field(None, description="集数")
    total_episodes: Optional[int] = Field(None, description="总集数")
    rating: Optional[Rating] = Field(None, description="评分")
    collection: Optional[Collection] = Field(None, description="收藏")
    meta_tags: Optional[List[str]] = Field(None, description="元标签")
    tags: Optional[List[Tag]] = Field(None, description="标签")


class SearchFilter(BaseModel):
    """搜索筛选器"""

    type: Optional[List[int]] = Field(None, description="条目类型")
    meta_tags: Optional[List[str]] = Field(None, description="元标签")
    tag: Optional[List[str]] = Field(None, description="标签")
    air_date: Optional[List[str]] = Field(None, description="播出日期")
    rating: Optional[List[str]] = Field(None, description="评分")
    rank: Optional[List[str]] = Field(None, description="排名")
    nsfw: Optional[bool] = Field(None, description="是否包含NSFW内容")

    @staticmethod
    def from_type(type: int) -> "SearchFilter":
        return SearchFilter(
            type=[type],
            meta_tags=None,
            tag=None,
            air_date=None,
            rating=None,
            rank=None,
            nsfw=None,
        )


class SearchRequest(BaseModel):
    """搜索请求"""

    keyword: str = Field(description="搜索关键字")
    sort: str = Field(
        default="match",
        description="排序规则：match=匹配度, heat=收藏人数, rank=排名, score=评分",
    )
    filter: Optional[SearchFilter] = Field(None, description="筛选条件")


class PagedSubject(BaseModel):
    """分页条目数据"""

    total: int
    limit: int
    offset: int
    data: List[Subject]


class Stat(BaseModel):
    """目录统计信息"""

    comments: int = Field(description="评论总数")
    collects: int = Field(description="收藏总数")


class Creator(BaseModel):
    """创建者信息"""

    username: str = Field(description="用户名")
    nickname: str = Field(description="昵称")


class Index(BaseModel):
    """目录信息"""

    id: int = Field(description="目录ID")
    title: Optional[str] = Field(None, description="目录标题")
    desc: Optional[str] = Field(None, description="目录描述")
    total: Optional[int] = Field(None, description="收录条目总数")
    stat: Optional[Stat] = Field(None, description="目录评论及收藏数")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    creator: Optional[Creator] = Field(None, description="创建者信息")
    ban: Optional[bool] = Field(
        None, description="已弃用，始终为false", deprecated=True
    )
    nsfw: Optional[bool] = Field(None, description="目录是否包括 nsfw 条目")


class IndexBasicInfo(BaseModel):
    """目录基本信息"""

    title: Optional[str] = Field(None, description="目录标题")
    description: Optional[str] = Field(None, description="目录描述")


class AddSubjectToIndexRequest(BaseModel):
    """向目录添加条目请求"""

    subject_id: int = Field(description="条目ID")
    sort: int = Field(description="排序")
    comment: str = Field(description="评论")
