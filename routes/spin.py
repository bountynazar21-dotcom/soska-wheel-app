from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import SessionLocal, Spin
from config import PRIZES

router = APIRouter()


@router.post("/spin")
async def spin(request: Request):
    """
    Ендпоінт, куди стукає фронт (wheel.js).
    Приймає username, user_id, check; повертає prize.
    """
    data = await request.json()

    username = data.get("username") or "unknown"
    user_id = data.get("user_id")
    check_number = data.get("check") or "no-check"

    db = SessionLocal()
    try:
        # Якщо цей чек уже брав участь — повертаємо той самий приз
        existing = (
            db.query(Spin)
            .filter(Spin.check_number == check_number)
            .first()
        )
        if existing:
            return JSONResponse({
                "prize": existing.prize,
                "repeat": True,
                "message": "Цей чек уже брав участь у розіграші."
            })

        # Рандомний приз
        import random
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
