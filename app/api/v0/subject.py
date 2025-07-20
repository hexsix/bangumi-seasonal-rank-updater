from fastapi import APIRouter, Depends, HTTPException
from returns.result import Failure, Success

from app.api.v0.utils import verify_password
from app.dependencies import get_db_client
from app.services.db import DBClient, Subject

router = APIRouter(prefix="/subject", tags=["subject"])


@router.get("/{subject_id}")
async def get_subject(
    subject_id: int,
    db_client: DBClient = Depends(get_db_client),
    _: bool = Depends(verify_password),
) -> Subject:
    wrapped_subject = await db_client.get_subject(subject_id)
    match wrapped_subject:
        case Failure(e):
            raise HTTPException(status_code=404, detail=f"Subject not found: {e}")
        case Success(subject):
            return subject
    raise HTTPException(status_code=404, detail="Subject not found")
