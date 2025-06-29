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
    episode_type: int = Field(
        alias="type",
        description="本篇=0 特别篇=1 OP=2 ED=3 预告/宣传/广告=4 MAD=5 其他=6",
    )
    name: str
    name_cn: str
    sort: float = Field(description="同类条目的排序和集数")
    ep: float = Field(description="条目内的集数, 从1开始。非本篇剧集的此字段无意义")
    airdate: str
    comment: int
    duration: str
    desc: str = Field(description="简介")
    disc: int = Field(description="音乐曲目的碟片数")
    duration_seconds: int
    subject_id: int

    class Config:
        populate_by_name = True


class ErrorDetail(BaseModel):
    """错误详情"""

    title: str
    description: str
    details: str


class Images(BaseModel):
    """图片信息"""

    large: str
    common: str
    medium: str
    small: str
    grid: str


class InfoboxItem(BaseModel):
    """信息框项目"""

    key: str
    value: Any


class IndexSubject(BaseModel):
    """索引条目"""

    id: int
    subject_type: int = Field(alias="type")
    name: str
    images: Images
    infobox: List[InfoboxItem]
    date: str
    comment: str
    added_at: str

    class Config:
        populate_by_name = True


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

    rank: int
    total: int
    count: Dict[int, int]
    score: float


class Tag(BaseModel):
    """标签"""

    name: str
    count: int


class Subject(BaseModel):
    """条目信息"""

    id: int
    subject_type: int = Field(
        alias="type", description="1=book, 2=anime, 3=music, 4=game, 6=real"
    )
    name: str
    name_cn: str
    summary: str
    series: bool
    nsfw: bool
    locked: bool
    date: str = Field(description="上映日期 YYYY-MM-DD 格式")
    platform: str = Field(description="播放平台 TV, Web, 欧美剧, DLC...")
    images: Images
    infobox: List[InfoboxItem]
    volumes: int
    eps: int
    total_episodes: int
    rating: Rating
    collection: Collection
    meta_tags: List[str]
    tags: List[Tag]

    class Config:
        populate_by_name = True


class SearchFilter(BaseModel):
    """搜索筛选器"""

    type: Optional[List[int]] = Field(None, description="条目类型")
    meta_tags: Optional[List[str]] = Field(None, description="元标签")
    tag: Optional[List[str]] = Field(None, description="标签")
    air_date: Optional[List[str]] = Field(None, description="播出日期")
    rating: Optional[List[str]] = Field(None, description="评分")
    rank: Optional[List[str]] = Field(None, description="排名")
    nsfw: Optional[bool] = Field(None, description="是否包含NSFW内容")


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


class Comments(BaseModel):
    """评论统计"""

    total: int = Field(description="评论总数")


class Collects(BaseModel):
    """收藏统计"""

    total: int = Field(description="收藏总数")


class Stat(BaseModel):
    """目录统计信息"""

    comments: Comments = Field(description="评论统计")
    collects: Collects = Field(description="收藏统计")


class Creator(BaseModel):
    """创建者信息"""

    username: str = Field(description="用户名")
    nickname: str = Field(description="昵称")


class Index(BaseModel):
    """目录信息"""

    id: int = Field(description="目录ID")
    title: str = Field(description="目录标题")
    desc: str = Field(description="目录描述")
    total: int = Field(default=0, description="收录条目总数")
    stat: Stat = Field(description="目录评论及收藏数")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    creator: Creator = Field(description="创建者信息")
    ban: bool = Field(default=False, description="已弃用，始终为false", deprecated=True)
    nsfw: bool = Field(description="目录是否包括 nsfw 条目")


class IndexBasicInfo(BaseModel):
    """目录基本信息"""

    title: Optional[str] = Field(None, description="目录标题")
    description: Optional[str] = Field(None, description="目录描述")


class AddSubjectToIndexRequest(BaseModel):
    """向目录添加条目请求"""

    subject_id: int = Field(description="条目ID")
    sort: int = Field(description="排序")
    comment: str = Field(description="评论")
