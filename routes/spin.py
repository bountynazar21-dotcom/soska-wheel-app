import random
import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import SessionLocal, Spin, Lead, PrizeStock
from config import PRIZES_, ADMINS, SPIN_COOLDOWN_DAYS
from bot import get_bot_and_dispatcher

router = APIRouter()


def format_time_left(delta: datetime.timedelta) -> str:
    total_seconds = int(delta.total_seconds())

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days} дн. {hours} год."
    if hours > 0:
        return f"{hours} год. {minutes} хв."
    return f"{minutes} хв."


def ensure_prize_stock(db):
    existing_count = db.query(PrizeStock).count()

    if existing_count > 0:
        return

    for item in PRIZES_:
        prize_stock = PrizeStock(
            sector_index=item["sector_index"],
            prize=item["prize"],
            stock=item["stock"],
            weight=item["weight"],
        )
        db.add(prize_stock)

    db.commit()


@router.post("/spin")
async def spin(request: Request):
    data = await request.json()

    username = data.get("username") or "unknown"
    user_id = data.get("user_id")

    db = SessionLocal()

    try:
        ensure_prize_stock(db)

        user_id_str = str(user_id) if user_id is not None else "unknown"
        is_admin = int(user_id_str) in ADMINS if user_id_str.isdigit() else False
        now = datetime.datetime.utcnow()

        lead = db.query(Lead).filter(Lead.user_id == user_id_str).first()

        if not lead:
            return JSONResponse(
                {
                    "prize": "Помилка",
                    "sector_index": 2,
                    "repeat": True,
                    "message": "Спочатку пройди реєстрацію в боті.",
                }
            )

        last_spin = (
            db.query(Spin)
            .filter(Spin.user_id == user_id_str)
            .order_by(Spin.datetime.desc())
            .first()
        )

        if last_spin and not is_admin:
            cooldown_until = last_spin.datetime + datetime.timedelta(days=SPIN_COOLDOWN_DAYS)

            if now < cooldown_until:
                time_left = cooldown_until - now
                sector_index = 2

                for item in PRIZES_:
                    if item["prize"] == last_spin.prize:
                        sector_index = item["sector_index"]
                        break

                return JSONResponse(
                    {
                        "prize": last_spin.prize,
                        "sector_index": sector_index,
                        "repeat": True,
                        "message": f"Ви вже крутили колесо. Наступна спроба через {format_time_left(time_left)}.",
                    }
                )

        available_prizes = (
            db.query(PrizeStock)
            .filter(PrizeStock.weight > 0)
            .filter((PrizeStock.stock == None) | (PrizeStock.stock > 0))
            .all()
        )

        if not available_prizes:
            return JSONResponse(
                {
                    "prize": "Нічого",
                    "sector_index": 2,
                    "repeat": False,
                    "message": "Призи закінчились.",
                }
            )

        selected = random.choices(
            available_prizes,
            weights=[p.weight for p in available_prizes],
            k=1,
        )[0]

        prize = selected.prize
        sector_index = selected.sector_index

        if selected.stock is not None and not is_admin:
            selected.stock -= 1

        row = Spin(
            username=str(username),
            user_id=user_id_str,
            prize=prize,
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        bot, _ = get_bot_and_dispatcher()

        admin_note = " 🧪 ТЕСТ АДМІНА" if is_admin else ""

        caption = "\n".join(
            [
                f"Нова заявка №{lead.id}{admin_note}",
                "",
                f"Імʼя: {lead.name}",
                f"Телефон: {lead.phone}",
                f"Telegram: @{lead.username}" if not lead.username.isdigit() else f"User ID: {lead.user_id}",
                "",
                f"🎁 Виграш: {prize}",
                "",
                "⏳ Наступна прокрутка: без обмежень для адміна" if is_admin else f"⏳ Наступна прокрутка через: {SPIN_COOLDOWN_DAYS} днів",
                "",
                f"(внутрішній ID: {lead.user_id}_{lead.id})",
            ]
        )

        for admin_id in ADMINS:
            await bot.send_message(
                chat_id=admin_id,
                text=caption,
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