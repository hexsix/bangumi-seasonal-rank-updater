from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Index(BaseModel):
    season_id: int
    index_id: int


class Subject(BaseModel):
    id: int
    name: Optional[str]
    name_cn: Optional[str]
    images_grid: Optional[str]
    images_large: Optional[str]
    rank: Optional[int]
    score: Optional[float]
    collection_total: Optional[int]
    average_comment: Optional[float]
    drop_rate: Optional[float]
    air_weekday: Optional[str]
    meta_tags: Optional[list[str]]
    updated_at: datetime
