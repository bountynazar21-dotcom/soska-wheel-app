import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardRemove,
)
from aiogram.exceptions import TelegramAPIError

from database import SessionLocal, Lead
from config import BOT_TOKEN, WEBAPP_URL

bot: Bot | None = None
dp: Dispatcher | None = None

router = Router()


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


class Registration(StatesGroup):
    waiting_for_check_photo = State()
    waiting_for_name = State()
    waiting_for_phone = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привіт! 👋\n\nНадішли, будь ласка, *фото чеку*.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    await state.set_state(Registration.waiting_for_check_photo)


@router.message(Registration.waiting_for_check_photo, F.photo)
async def process_check_photo(message: Message, state: FSMContext) -> None:
    file_id = message.photo[-1].file_id
    await state.update_data(check_photo_id=file_id)

    await message.answer(
        "Дякую! 🙌\nТепер напиши, будь ласка, *своє імʼя*.",
        parse_mode="Markdown",
    )
    await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_check_photo)
async def no_photo_warning(message: Message) -> None:
    await message.answer(
        "Будь ласка, надішли саме *фото чеку* 📸",
        parse_mode="Markdown",
    )


@router.message(Registration.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await state.update_data(name=name)

    await message.answer(
        "Супер! ✨\nТепер напиши, будь ласка, *номер телефону* у форматі +380...",
        parse_mode="Markdown",
    )
    await state.set_state(Registration.waiting_for_phone)


@router.message(Registration.waiting_for_phone, F.text)
async def process_phone(message: Message, state: FSMContext, bot: Bot) -> None:
    phone = message.text.strip()
    await state.update_data(phone=phone)

    data = await state.get_data()
    check_photo_id = data.get("check_photo_id")
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
            existing_lead.check_photo_id = str(check_photo_id)
        else:
            lead = Lead(
                username=str(username),
                user_id=user_id,
                name=str(name),
                phone=str(phone),
                check_photo_id=str(check_photo_id),
            )
            db.add(lead)

        db.commit()

    except Exception as e:
        logging.error(f"Failed to save lead: {e}")
        await message.answer(
            "Сталася помилка під час збереження заявки. Спробуй ще раз /start"
        )
        return

    finally:
        db.close()

    await message.answer(
        "Все, ти в грі! 🎉\nНатискай кнопку нижче, щоб відкрити колесо фортуни:",
        reply_markup=build_webapp_keyboard(),
    )

    await state.clear()


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