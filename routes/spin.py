import random
import datetime
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from database import SessionLocal, Spin, Lead, PrizeStock
from config import (
    PRIZES_,
    ADMINS,
    SPIN_COOLDOWN_DAYS,
    PRANK_USER_IDS,
    PRANK_TEXT,
    PRANK_SECTOR_INDEX,
)
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


async def notify_admins(
    lead: Lead,
    prize: str,
    user_id_str: str,
    is_admin: bool,
    is_prank: bool,
):
    bot, _ = get_bot_and_dispatcher()

    notes = []
    if is_admin:
        notes.append("🧪 ТЕСТ АДМІНА")
    if is_prank:
        notes.append("🤣 PRANK USER")

    admin_note = f" {' | '.join(notes)}" if notes else ""

    caption = "\n".join(
        [
            f"Нова заявка №{lead.id}{admin_note}",
            "",
            f"Імʼя: {lead.name}",
            f"Телефон: {lead.phone}",
            f"Telegram: @{lead.username}" if not lead.username.isdigit() else f"User ID: {lead.user_id}",
            "",
            f"🎁 Результат: {prize}",
            "",
            "⏳ Наступна прокрутка: без обмежень для адміна"
            if is_admin
            else f"⏳ Наступна прокрутка через: {SPIN_COOLDOWN_DAYS} днів",
            "",
            f"(внутрішній ID: {user_id_str}_{lead.id})",
        ]
    )

    for admin_id in ADMINS:
        await bot.send_message(
            chat_id=admin_id,
            text=caption,
        )


async def notify_user_win(
    user_id_str: str,
    prize: str,
    sector_index: int,
    is_prank: bool,
):
    if is_prank:
        return

    if sector_index == 3 or prize == "Нічого":
        return

    try:
        bot, _ = get_bot_and_dispatcher()

        await bot.send_message(
            chat_id=int(user_id_str),
            text=(
                "🎉 Вітаємо!\n\n"
                f"Твій виграш: {prize}\n\n"
            ),
        )

    except Exception as e:
        logging.error(f"Failed to send win message to user {user_id_str}: {e}")


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
        is_prank_user = int(user_id_str) in PRANK_USER_IDS if user_id_str.isdigit() else False

        now = datetime.datetime.utcnow()

        lead = db.query(Lead).filter(Lead.user_id == user_id_str).first()

        if not lead:
            return JSONResponse(
                {
                    "prize": "Нічого",
                    "sector_index": 3,
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
            cooldown_until = last_spin.datetime + datetime.timedelta(
                days=SPIN_COOLDOWN_DAYS
            )

            if now < cooldown_until:
                time_left = cooldown_until - now

                return JSONResponse(
                    {
                        "prize": last_spin.prize,
                        "sector_index": PRANK_SECTOR_INDEX if is_prank_user else 3,
                        "repeat": True,
                        "message": f"Ви вже крутили колесо. Наступна спроба через {format_time_left(time_left)}.",
                    }
                )

        if is_prank_user and not is_admin:
            row = Spin(
                username=str(username),
                user_id=user_id_str,
                prize=PRANK_TEXT,
            )

            db.add(row)
            db.commit()
            db.refresh(row)

            await notify_admins(
                lead=lead,
                prize=PRANK_TEXT,
                user_id_str=user_id_str,
                is_admin=False,
                is_prank=True,
            )

            return JSONResponse(
                {
                    "prize": PRANK_TEXT,
                    "sector_index": PRANK_SECTOR_INDEX,
                    "repeat": False,
                    "message": "",
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
                    "sector_index": 3,
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

        await notify_admins(
            lead=lead,
            prize=prize,
            user_id_str=user_id_str,
            is_admin=is_admin,
            is_prank=False,
        )

        await notify_user_win(
            user_id_str=user_id_str,
            prize=prize,
            sector_index=sector_index,
            is_prank=False,
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