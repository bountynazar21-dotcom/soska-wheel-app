import random

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import SessionLocal, Spin
from config import PRIZES, WEIGHTS

router = APIRouter()


@router.post("/spin")
async def spin(request: Request):
    data = await request.json()

    username = data.get("username") or "unknown"
    user_id = data.get("user_id")
    # якщо колись захочеш знову чек — можна брати з data.get("check")
    check_number = "no-check"

    db = SessionLocal()
    try:
        # Вибір призу з урахуванням ваг
        prize = random.choices(PRIZES, weights=WEIGHTS, k=1)[0]
        sector_index = PRIZES.index(prize)  # індекс сектора для фронта

        row = Spin(
            username=str(username),
            user_id=str(user_id),
            check_number=str(check_number),
            prize=prize,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return JSONResponse(
            {
                "prize": prize,
                "sector_index": sector_index,
                "repeat": False,
                "message": "",
            }
        )
    finally:
        db.close()

