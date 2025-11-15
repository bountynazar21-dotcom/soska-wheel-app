import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN, WEBAPP_URL, ADMINS

logger = logging.getLogger(__name__)

bot: Bot | None = None
dp: Dispatcher | None = None

router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎡 Відкрити колесо",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ]
    )

    await message.answer(
        "Натисни кнопку, щоб відкрити колесо фортуни.",
        reply_markup=kb
    )


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    """
    /admin — тільки для адмінів.
    Даємо лінк на веб-адмінку з підставленим user_id.
    """
    uid = message.from_user.id

    if uid not in ADMINS:
        return await message.answer("⛔ У вас немає доступу до адмін-панелі.")

    from config import APP_BASE_URL  # щоб уникнути циклічного імпорту
    admin_url = f"{APP_BASE_URL}/admin?user_id={uid}"
    text = (
        "🛠 Адмін-панель активна.\n\n"
        f"Перейди в браузері за посиланням:\n{admin_url}"
    )
    await message.answer(text)


async def run_bot():
    """
    Запустити polling — викликається з FastAPI startup.
    """
    global bot, dp

    if bot is None or dp is None:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)

    try:
        await dp.start_polling(bot)
    except TelegramAPIError as e:
        logger.error(f"Polling error: {e}")


async def shutdown_bot():
    """
    Акуратно закрити сесію бота на shutdown FastAPI.
    """
    global bot
    if bot:
        await bot.session.close()
        bot = None
