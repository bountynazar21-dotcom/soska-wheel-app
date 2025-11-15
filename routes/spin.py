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

    db = SessionLocal()
    try:
        # Вибираємо випадковий приз
        prize = random.choice(PRIZES)

        # Записуємо результат (без чеків)
        row = Spin(
            username=str(username),
            user_id=str(user_id),
            check_number="none",
            prize=prize,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return JSONResponse({
            "prize": prize,
            "repeat": False
        })

    finally:
        db.close()
