import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import Command
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN, WEBAPP_URL, ADMINS, APP_BASE_URL

bot: Bot | None = None
dp: Dispatcher | None = None


def get_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    global bot, dp

    if bot and dp:
        return bot, dp

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

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
            await message.answer("⛔ У вас немає доступу до адмін-панелі.")
            return

        admin_url = f"{APP_BASE_URL}/admin?user_id={uid}"
        await message.answer(
            "🛠 Адмін-панель активна.\n\n"
            f"Перейди в браузері за посиланням:\n{admin_url}"
        )

    dp.include_router(router)

    return bot, dp


async def run_bot():
    bot_obj, dp_obj = get_bot_and_dispatcher()
    try:
        await dp_obj.start_polling(bot_obj)
    except TelegramAPIError as e:
        logging.error(f"Polling error: {e}")


async def shutdown_bot():
    global bot
    if bot:
        await bot.session.close()
