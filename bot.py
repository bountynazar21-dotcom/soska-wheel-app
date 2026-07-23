import logging
import datetime

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

from database import (
    SessionLocal,
    Lead,
    Spin,
    add_referral_bonus,
    get_unused_referral_spins_count,
)
from config import (
    BOT_TOKEN,
    WEBAPP_URL,
    CHANNEL_USERNAME,
    CHANNEL_URL,
    SPIN_COOLDOWN_DAYS,
    ADMINS,
)

bot: Bot | None = None
dp: Dispatcher | None = None

router = Router()


class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()


def is_admin_user(user_id: int | str | None) -> bool:
    if user_id is None:
        return False

    user_id_str = str(user_id)

    if not user_id_str.isdigit():
        return False

    return int(user_id_str) in ADMINS


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


def get_referral_link(user_id: str | int) -> str:
    return f"https://t.me/s0ska_bar_bot?start=ref_{user_id}"


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
    if is_admin_user(user_id):
        return True

    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)

        return member.status in (
            "member",
            "administrator",
            "creator",
            "restricted",
        )

    except TelegramAPIError as e:
        logging.error(f"Subscription check failed for user {user_id}: {e}")
        return False


def get_active_cooldown(user_id: str | int | None):
    if is_admin_user(user_id):
        return None

    user_id_str = str(user_id)

    db = SessionLocal()

    try:
        last_spin = (
            db.query(Spin)
            .filter(Spin.user_id == user_id_str)
            .order_by(Spin.datetime.desc())
            .first()
        )

        if not last_spin:
            return None

        now = datetime.datetime.utcnow()
        cooldown_until = last_spin.datetime + datetime.timedelta(
            days=SPIN_COOLDOWN_DAYS
        )

        if now >= cooldown_until:
            return None

        return cooldown_until - now

    finally:
        db.close()


def has_bonus_spin(user_id: str | int | None) -> bool:
    if user_id is None:
        return False

    db = SessionLocal()

    try:
        return get_unused_referral_spins_count(db, str(user_id)) > 0
    finally:
        db.close()


def can_user_try_spin(user_id: str | int | None) -> tuple[bool, datetime.timedelta | None]:
    """
    True — користувач може перейти до колеса.
    False — активний cooldown і немає бонусного спіну.
    """

    cooldown_left = get_active_cooldown(user_id)

    if cooldown_left is None:
        return True, None

    if has_bonus_spin(user_id):
        return True, None

    return False, cooldown_left


def parse_referrer_id(message: Message) -> str | None:
    """
    Парсить deep-link:
    /start ref_5480082089
    """

    text = message.text or ""
    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        return None

    payload = parts[1].strip()

    if not payload.startswith("ref_"):
        return None

    referrer_id = payload.replace("ref_", "", 1).strip()

    if not referrer_id.isdigit():
        return None

    return referrer_id


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()

    user_id = str(message.from_user.id)
    referrer_id = parse_referrer_id(message)

    if referrer_id and referrer_id != user_id:
        await state.update_data(referrer_id=referrer_id)

    can_try, cooldown_left = can_user_try_spin(user_id)

    if not can_try and cooldown_left:
        referral_link = get_referral_link(user_id)

        await message.answer(
            "Ти вже крутив колесо 🎡\n"
            f"Наступна спроба буде доступна через {format_time_left(cooldown_left)}.\n\n"
            "Але ти можеш отримати додатковий спін 👇\n"
            "Запроси друга за своїм посиланням. Коли він пройде реєстрацію, "
            "тобі автоматично додасться ще одна спроба.\n\n"
            f"🔗 Твоє посилання:\n{referral_link}"
        )
        return

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

    user_id = str(message.from_user.id)

    can_try, cooldown_left = can_user_try_spin(user_id)

    if not can_try and cooldown_left:
        await state.clear()

        referral_link = get_referral_link(user_id)

        await message.answer(
            "Ти вже крутив колесо 🎡\n"
            f"Наступна спроба буде доступна через {format_time_left(cooldown_left)}.\n\n"
            "Але ти можеш отримати додатковий спін за запрошеного друга 👇\n"
            f"🔗 Твоє посилання:\n{referral_link}"
        )
        return

    data = await state.get_data()
    name = data.get("name") or "-"
    referrer_id = data.get("referrer_id")

    username = (
        message.from_user.username
        or f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        or "user"
    )

    db = SessionLocal()
    referral_bonus_added = False

    try:
        existing_lead = (
            db.query(Lead)
            .filter(Lead.user_id == user_id)
            .first()
        )

        is_new_lead = existing_lead is None

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

        # Бонус нараховується тільки якщо це новий користувач,
        # який прийшов по реферальному посиланню.
        if is_new_lead and referrer_id:
            referral_bonus_added = add_referral_bonus(
                db=db,
                referrer_user_id=str(referrer_id),
                invited_user_id=user_id,
            )

    except Exception as e:
        logging.error(f"Failed to save lead or referral bonus: {e}")
        await message.answer("Сталася помилка. Спробуй ще раз /start")
        return

    finally:
        db.close()

    if referral_bonus_added and referrer_id:
        try:
            await bot.send_message(
                chat_id=int(referrer_id),
                text=(
                    "🎁 Тобі нараховано +1 додатковий спін!\n\n"
                    "Твій друг пройшов реєстрацію за твоїм посиланням. "
                    "Можеш знову випробувати удачу в Колесі Фортуни 🎡"
                ),
            )
        except TelegramAPIError as e:
            logging.error(f"Failed to notify referrer {referrer_id}: {e}")

    await state.clear()

    subscribed = await is_user_subscribed(bot, message.from_user.id)

    referral_link = get_referral_link(user_id)
    bonus_count = 0

    db = SessionLocal()
    try:
        bonus_count = get_unused_referral_spins_count(db, user_id)
    finally:
        db.close()

    if subscribed:
        await message.answer(
            "Все готово! 🎉\n"
            "Натискай кнопку нижче, щоб відкрити колесо фортуни:\n\n"
            f"🎁 Твої бонусні спіни: {bonus_count}\n\n"
            "Хочеш ще одну спробу? Запроси друга 👇\n"
            f"🔗 {referral_link}",
            reply_markup=build_webapp_keyboard(),
        )
    else:
        await message.answer(
            "Щоб крутити колесо, спочатку підпишись на наш Telegram-канал 👇",
            reply_markup=build_subscribe_keyboard(),
        )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, bot: Bot) -> None:
    user_id = str(callback.from_user.id)

    can_try, cooldown_left = can_user_try_spin(user_id)

    if not can_try and cooldown_left:
        if callback.message:
            referral_link = get_referral_link(user_id)

            await callback.message.answer(
                "Ти вже крутив колесо 🎡\n"
                f"Наступна спроба буде доступна через {format_time_left(cooldown_left)}.\n\n"
                "Але ти можеш отримати додатковий спін за запрошеного друга 👇\n"
                f"🔗 Твоє посилання:\n{referral_link}"
            )
        return

    subscribed = await is_user_subscribed(bot, callback.from_user.id)

    if subscribed:
        await callback.answer("Підписку підтверджено ✅")

        referral_link = get_referral_link(user_id)

        db = SessionLocal()
        try:
            bonus_count = get_unused_referral_spins_count(db, user_id)
        finally:
            db.close()

        if callback.message:
            await callback.message.answer(
                "Підписку підтверджено ✅\n"
                "Тепер можеш крутити колесо:\n\n"
                f"🎁 Твої бонусні спіни: {bonus_count}\n\n"
                "Хочеш ще одну спробу? Запроси друга 👇\n"
                f"🔗 {referral_link}",
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