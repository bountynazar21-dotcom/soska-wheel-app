import logging
from itertools import count

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

from config import BOT_TOKEN, WEBAPP_URL, ADMINS

bot: Bot | None = None
dp: Dispatcher | None = None

router = Router()
# простий послідовний номер заявки (починається з 1, при рестарті бота лічильник скинеться)
lead_counter = count(1)


def build_webapp_keyboard() -> InlineKeyboardMarkup:
    """
    Інлайн-клавіатура з кнопкою відкриття WebApp колеса.
    """
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
    """
    Старт: просимо надіслати фото чеку.
    """
    await state.clear()
    await message.answer(
        "Привіт! 👋\n\nНадішли, будь ласка, *фото чеку*.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown",
    )
    await state.set_state(Registration.waiting_for_check_photo)


@router.message(Registration.waiting_for_check_photo, F.photo)
async def process_check_photo(message: Message, state: FSMContext) -> None:
    """
    Отримали фото чеку → зберегли file_id → питаємо імʼя.
    """
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
    """
    Отримали телефон → збираємо всі дані → шлемо адмінам + даємо кнопку WebApp.
    """
    phone = message.text.strip()
    await state.update_data(phone=phone)

    data = await state.get_data()
    check_photo_id = data.get("check_photo_id")
    name = data.get("name")

    # Генеруємо послідовний номер заявки
    lead_no = next(lead_counter)

    # Збираємо текст для адміна
    caption_lines = [
        f"Нова заявка №{lead_no}",
        "",
        f"Імʼя: {name or '-'}",
        f"Телефон: {phone or '-'}",
    ]

    if message.from_user.username:
        caption_lines.append(f"Telegram: @{message.from_user.username}")
    else:
        caption_lines.append(f"User ID: {message.from_user.id}")

    # “Невидимий” внутрішній номер (інвіз)
    caption_lines.extend(
        [
            "",
            f"(внутрішній ID: {message.from_user.id}_{lead_no})",
        ]
    )

    caption = "\n".join(caption_lines)

    # Відправляємо всім адмінам фото + дані
    if check_photo_id:
        for admin_id in ADMINS:
            try:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=check_photo_id,
                    caption=caption,
                )
            except TelegramAPIError as e:
                logging.error(f"Failed to send lead to admin {admin_id}: {e}")

    # Даємо юзеру WebApp-кнопку
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
