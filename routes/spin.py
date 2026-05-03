import random

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import SessionLocal, Spin, Lead
from config import PRIZES, WEIGHTS, ADMINS
from bot import get_bot_and_dispatcher

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

        # 🔒 перевірка чи вже крутив
        existing_spin = (
            db.query(Spin)
            .filter(Spin.user_id == user_id_str)
            .first()
        )

        if existing_spin:
            prize = existing_spin.prize
            sector_index = PRIZES.index(prize) if prize in PRIZES else 0

            return JSONResponse(
                {
                    "prize": prize,
                    "sector_index": sector_index,
                    "repeat": True,
                    "message": "Ви вже крутили колесо.",
                }
            )

        # 🎁 визначаємо приз
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

        # 📦 дістаємо заявку
        lead = db.query(Lead).filter(Lead.user_id == user_id_str).first()

        if lead:
            bot, _ = get_bot_and_dispatcher()

            caption = "\n".join(
                [
                    f"Нова заявка №{lead.id}",
                    "",
                    f"Імʼя: {lead.name}",
                    f"Телефон: {lead.phone}",
                    f"Telegram: @{lead.username}" if not lead.username.isdigit() else f"User ID: {lead.user_id}",
                    "",
                    f"🎁 Виграш: {prize}",
                    "",
                    f"(внутрішній ID: {lead.user_id}_{lead.id})",
                ]
            )

            for admin_id in ADMINS:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=lead.check_photo_id,
                    caption=caption,
                )

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