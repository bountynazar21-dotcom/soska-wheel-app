import random

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import SessionLocal, Spin
from config import PRIZES

router = APIRouter()


@router.post("/spin")
async def spin(request: Request):
    data = await request.json()

    username = data.get("username") or "unknown"
    user_id = data.get("user_id")
    check_number = data.get("check") or "no-check"

    db = SessionLocal()
    try:
        existing = (
            db.query(Spin)
            .filter(Spin.check_number == check_number)
            .first()
        )
        if existing:
            return JSONResponse(
                {
                    "prize": existing.prize,
                    "repeat": True,
                    "message": "Цей чек уже брав участь у розіграші.",
                }
            )

        prize = random.choice(PRIZES)

        row = Spin(
            username=str(username),
            user_id=str(user_id),
            check_number=str(check_number),
            prize=prize,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return JSONResponse({"prize": prize})

    finally:
        db.close()


@router.get("/ping")
async def ping():
    return {"status": "ok"}
