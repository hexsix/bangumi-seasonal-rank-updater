from datetime import datetime

from pydantic import BaseModel


class AvailableSeasonsResponse(BaseModel):
    current_season_id: int
    available_seasons: list[int]


class SeasonResponse(BaseModel):
    season_id: int
    subjects: list[dict]
    updated_at: datetime
