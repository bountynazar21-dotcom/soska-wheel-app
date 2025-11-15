import os
import asyncio
import random
import logging

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    FileResponse,
    PlainTextResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command

from database import SessionLocal, Base, engine, Spin


# ======================================
# CONFIG
# ======================================

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://soska-wheel-app-production.up.railway.app")

WEBAPP_URL = os.environ.get(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html",
)

ADMINS: set[int] = {
    769431786,
    5480082089,
}

PRIZES = [
    "Знижка 10%",
    "Знижка 15%",
    "Знижка 20%",
    "Подарунок від Punch",
    "Подарунок від Soska Bar",
    "Рідина 30 мл",
    "Картридж",
    "Мерч Soska Bar x Punch",
]


# ======================================
# FASTAPI
# ======================================

app = FastAPI()

# Статика + шаблони
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Створення таблиць БД
Base.metadata.create_all(bind=engine)


# --- СЕРВІСНІ РОУТИ ДЛЯ ПЕРЕВІРКИ ---

@app.get("/ping", response_class=PlainTextResponse)
async def ping():
    # дуже простий хелсчек
    return "pong"


@app.get("/", response_class=HTMLResponse)
async def root():
    # просто віддаємо index.html з папки static
    return FileResponse("static/index.html")


# --- API для колеса ---

@app.post("/spin")
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
            return JSONResponse({
                "prize": existing.prize,
                "repeat": True,
                "message": "Цей чек уже брав участь у розіграші."
            })

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


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user_id: int | None = None):
    if user_id is None or user_id not in ADMINS:
        return HTMLResponse(
            "<h2 style='color:red'>ACCESS DENIED</h2>"
            "<p>У вас немає прав доступу.</p>",
            status_code=403
        )

    db = SessionLocal()
    try:
        spins = db.query(Spin).order_by(Spin.id.desc()).all()
        return templates.TemplateResponse(
            "admin.html",
            {"request": request, "spins": spins}
        )
    finally:
        db.close()


# ======================================
# TELEGRAM BOT
# ======================================

bot: Bot | None = None
dp: Dispatcher | None = None


def setup_bot():
    global bot, dp

    if bot is not None and dp is not None:
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    router = Router()

    @router.message(Command("start"))
    async def start_cmd(message: Message):
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎡 Відкрити колесо",
                        web_app=WebAppInfo(url=WEBAPP_URL),
                    )
                ]
            ]
        )

        await message.answer(
            "Натисни кнопку, щоб відкрити колесо фортуни.",
            reply_markup=kb,
        )

    @router.message(Command("admin"))
    async def admin_cmd(message: Message):
        uid = message.from_user.id

        if uid not in ADMINS:
            return await message.answer("⛔ У вас немає доступу до адмін-панелі.")

        admin_url = f"{APP_BASE_URL}/admin?user_id={uid}"
        text = (
            "🛠 Адмін-панель активна.\n\n"
            f"Перейди в браузері за посиланням:\n{admin_url}"
        )
        await message.answer(text)

    dp.include_router(router)


async def run_bot():
    global bot, dp

    setup_bot()

    try:
        await dp.start_polling(bot)
    except TelegramAPIError as e:
        logging.error(f"Polling error: {e}")


# ======================================
# FASTAPI lifecycle
# ======================================

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(run_bot())
    logging.info(
        f"Application startup complete. BASE_URL={APP_BASE_URL}, WEBAPP_URL={WEBAPP_URL}"
    )


@app.on_event("shutdown")
async def shutdown():
    global bot
    if bot:
        await bot.session.close()
    logging.info("Application shutdown complete")


# ======================================
# LOCAL RUN
# ======================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
