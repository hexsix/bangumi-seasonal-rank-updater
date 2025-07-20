from fastapi import APIRouter, Depends, FastAPI, HTTPException

from app.api.v0.utils import verify_password
from app.services import db

router = APIRouter(prefix="/subject", tags=["subject"])


@router.get("/{subject_id}")
async def get_subject(
    app: FastAPI,
    subject_id: int,
    _: bool = Depends(verify_password),
) -> db.Subject:
    subject = app.state.db_client.get_subject(subject_id)
    if subject:
        return subject
    else:
        raise HTTPException(status_code=404, detail="Subject not found")
