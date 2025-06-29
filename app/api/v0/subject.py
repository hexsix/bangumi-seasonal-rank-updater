import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.services import db

router = APIRouter(prefix="/subject", tags=["subject"])


async def get_db_conn(request: Request) -> sqlite3.Connection:
    return request.app.state.db_conn


@router.get("/{subject_id}")
async def get_subject(
    subject_id: int, db_conn: sqlite3.Connection = Depends(get_db_conn)
):
    subject = db.get_subject(db_conn, subject_id)
    if subject:
        return subject.model_dump()
    else:
        raise HTTPException(status_code=404, detail="Subject not found")
