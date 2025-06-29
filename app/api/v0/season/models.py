from datetime import datetime

from pydantic import BaseModel

from app.services.redis_client import Subject


class AvailableSeasonsResponse(BaseModel):
    current_season_id: int
    available_seasons: list[int]


class SeasonResponse(BaseModel):
    season_id: int
    subjects: list[Subject]
    updated_at: datetime
