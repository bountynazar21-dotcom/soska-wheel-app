import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardRemove,
)
from aiogram.exceptions import TelegramAPIError

from database import SessionLocal, Lead
from config import BOT_TOKEN, WEBAPP_URL, CHANNEL_USERNAME, CHANNEL_URL

bot: Bot | None = None
dp: Dispatcher | None = None

router = Router()


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


def build_webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎡 Відкрити колесо фортуни",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )


def build_subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Підписатися на канал",
                    url=CHANNEL_URL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я підписався",
                    callback_data="check_subscription",
                )
            ],
        ]
    )


async def is_user_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramAPIError as e:
        logging.error(f"Subscription check failed: {e}")
        return False


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    await message.answer(
        "Привіт! 👋\n\nНапиши, будь ласка, своє імʼя.",
        reply_markup=ReplyKeyboardRemove(),
    )

    await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("Введи, будь ласка, коректне імʼя.")
        return

    await state.update_data(name=name)

    await message.answer(
        "Супер! ✨\nТепер напиши, будь ласка, номер телефону у форматі +380..."
    )

    await state.set_state(Registration.waiting_for_phone)


@router.message(Registration.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext, bot: Bot) -> None:
    phone = message.text.strip()

    if len(phone) < 10:
        await message.answer("Введи, будь ласка, коректний номер телефону.")
        return

    data = await state.get_data()
    name = data.get("name") or "-"

    user_id = str(message.from_user.id)

    username = (
        message.from_user.username
        or f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        or "user"
    )

    db = SessionLocal()

    try:
        existing_lead = db.query(Lead).filter(Lead.user_id == user_id).first()

        if existing_lead:
            existing_lead.username = str(username)
            existing_lead.name = str(name)
            existing_lead.phone = str(phone)
        else:
            lead = Lead(
                username=str(username),
                user_id=user_id,
                name=str(name),
                phone=str(phone),
            )
            db.add(lead)

        db.commit()

    except Exception as e:
        logging.error(f"Failed to save lead: {e}")
        await message.answer("Сталася помилка. Спробуй ще раз /start")
        return

    finally:
        db.close()

    await state.clear()

    subscribed = await is_user_subscribed(bot, message.from_user.id)

    if subscribed:
        await message.answer(
            "Все готово! 🎉\nНатискай кнопку нижче, щоб відкрити колесо фортуни:",
            reply_markup=build_webapp_keyboard(),
        )
    else:
        await message.answer(
            "Щоб крутити колесо, спочатку підпишись на наш Telegram-канал 👇",
            reply_markup=build_subscribe_keyboard(),
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot) -> None:
    subscribed = await is_user_subscribed(bot, callback.from_user.id)

    if subscribed:
        await callback.message.answer(
            "Підписку підтверджено ✅\nТепер можеш крутити колесо:",
            reply_markup=build_webapp_keyboard(),
        )
    else:
        await callback.answer(
            "Підписку ще не знайдено. Підпишись на канал і натисни ще раз.",
            show_alert=True,
        )


@router.message(Registration.waiting_for_phone)
async def phone_required(message: Message) -> None:
    await message.answer("Будь ласка, надішли номер телефону текстом ☎️")


def get_bot_and_dispatcher() -> tuple[Bot, Dispatcher]:
    global bot, dp

    if bot is None or dp is None:
        if not BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN is not set")

        bot = Bot(BOT_TOKEN, parse_mode="HTML")
        dp = Dispatcher()
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