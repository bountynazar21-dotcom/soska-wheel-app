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
    check_number = data.get("check") or "no-check"

    db = SessionLocal()

    try:
        user_id_str = str(user_id) if user_id is not None else "unknown"

        existing_spin = (
            db.query(Spin)
            .filter(Spin.user_id == user_id_str)
            .first()
        )

        if existing_spin:
            prize = existing_spin.prize

            if prize in PRIZES:
                sector_index = PRIZES.index(prize)
            else:
                sector_index = 0

            return JSONResponse(
                {
                    "prize": prize,
                    "sector_index": sector_index,
                    "repeat": True,
                    "message": "Ви вже крутили колесо.",
                }
            )

        prize = random.choices(PRIZES, weights=WEIGHTS, k=1)[0]
        sector_index = PRIZES.index(prize)

        row = Spin(
            username=str(username),
            user_id=user_id_str,
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

