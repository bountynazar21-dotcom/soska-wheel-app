import os
import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///wheel.db")

# Railway / Heroku інколи дають postgres://, а SQLAlchemy хоче postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_kwargs = {
    "echo": False,
}

# connect_args потрібен тільки для SQLite
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# =========================
# КОРИСТУВАЧІ / ЗАЯВКИ
# =========================

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, nullable=False)
    user_id = Column(String, unique=True, index=True, nullable=False)

    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    datetime = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )


# =========================
# СПІНИ
# =========================

class Spin(Base):
    __tablename__ = "spins"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, nullable=False)
    user_id = Column(String, index=True, nullable=False)

    prize = Column(String, nullable=False)

    # коли був spin
    datetime = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )


# =========================
# БОНУСНІ СПІНИ ЗА РЕФЕРАЛІВ
# =========================

class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"

    id = Column(Integer, primary_key=True, index=True)

    # Хто запросив
    referrer_user_id = Column(String, index=True, nullable=False)

    # Кого запросив
    invited_user_id = Column(String, unique=True, index=True, nullable=False)

    # Використаний чи ні бонусний спін
    is_used = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False,
    )

    used_at = Column(
        DateTime,
        nullable=True,
    )


# =========================
# STOCK ПРИЗІВ
# =========================

class PrizeStock(Base):
    __tablename__ = "prize_stock"

    id = Column(Integer, primary_key=True, index=True)

    sector_index = Column(Integer, unique=True, nullable=False)

    prize = Column(String, nullable=False)

    # None = безлімітно
    stock = Column(Integer, nullable=True)

    weight = Column(Integer, nullable=False)


# =========================
# НАЛАШТУВАННЯ СИСТЕМИ
# =========================

class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)

    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


# =========================
# ІНІЦІАЛІЗАЦІЯ БАЗИ
# =========================

def init_db() -> None:
    Base.metadata.create_all(bind=engine)


# =========================
# СИНХРОНІЗАЦІЯ ПРИЗОВОГО ФОНДУ
# =========================

def ensure_prize_stock(db) -> None:
    """
    Синхронізує призовий фонд з config.py.

    Важливо:
    - якщо PRIZE_POOL_VERSION змінився — оновлюємо призи, stock і weight;
    - якщо PRIZE_POOL_VERSION такий самий — НЕ скидаємо залишки призів,
      щоб після рестарту Railway подарунки не повертались назад.
    """

    from config import PRIZES_, PRIZE_POOL_VERSION

    setting_key = "prize_pool_version"

    current_version = (
        db.query(AppSetting)
        .filter(AppSetting.key == setting_key)
        .first()
    )

    # Якщо версія вже актуальна — нічого не скидаємо
    if current_version and current_version.value == PRIZE_POOL_VERSION:
        return

    config_sector_indexes = {item["sector_index"] for item in PRIZES_}

    # Видаляємо старі сектори, яких більше немає в config.py
    old_prizes = db.query(PrizeStock).all()
    for old_prize in old_prizes:
        if old_prize.sector_index not in config_sector_indexes:
            db.delete(old_prize)

    # Оновлюємо або створюємо актуальні сектори
    for item in PRIZES_:
        prize_stock = (
            db.query(PrizeStock)
            .filter(PrizeStock.sector_index == item["sector_index"])
            .first()
        )

        if prize_stock is None:
            prize_stock = PrizeStock(
                sector_index=item["sector_index"],
                prize=item["prize"],
                stock=item["stock"],
                weight=item["weight"],
            )
            db.add(prize_stock)
        else:
            prize_stock.prize = item["prize"]
            prize_stock.stock = item["stock"]
            prize_stock.weight = item["weight"]

    # Записуємо нову версію призового фонду
    if current_version is None:
        current_version = AppSetting(
            key=setting_key,
            value=PRIZE_POOL_VERSION,
        )
        db.add(current_version)
    else:
        current_version.value = PRIZE_POOL_VERSION

    db.commit()


# =========================
# РЕФЕРАЛЬНА СИСТЕМА
# =========================

def get_referral_day_bounds() -> tuple[datetime.datetime, datetime.datetime]:
    """
    Межі поточного дня по UTC.

    Для ліміту 5 друзів на день цього достатньо.
    Якщо треба буде чітко по Києву — можна буде переробити під timezone.
    """

    now = datetime.datetime.utcnow()

    day_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    day_end = day_start + datetime.timedelta(days=1)

    return day_start, day_end


def count_today_referral_bonuses(db, referrer_user_id: str) -> int:
    """
    Рахує, скільки бонусів за друзів користувач уже отримав сьогодні.
    """

    day_start, day_end = get_referral_day_bounds()

    return (
        db.query(ReferralBonus)
        .filter(ReferralBonus.referrer_user_id == str(referrer_user_id))
        .filter(ReferralBonus.created_at >= day_start)
        .filter(ReferralBonus.created_at < day_end)
        .count()
    )


def get_unused_referral_spins_count(db, user_id: str) -> int:
    """
    Кількість невикористаних бонусних спінів користувача.
    """

    return (
        db.query(ReferralBonus)
        .filter(ReferralBonus.referrer_user_id == str(user_id))
        .filter(ReferralBonus.is_used == False)  # noqa: E712
        .count()
    )


def add_referral_bonus(db, referrer_user_id: str, invited_user_id: str) -> bool:
    """
    Нараховує +1 бонусний спін за запрошеного друга.

    Повертає:
    True — бонус нараховано
    False — бонус не нараховано
    """

    from config import REFERRAL_DAILY_LIMIT

    referrer_user_id = str(referrer_user_id)
    invited_user_id = str(invited_user_id)

    # Не можна запросити самого себе
    if referrer_user_id == invited_user_id:
        return False

    # Якщо цей запрошений користувач уже давав бонус — повторно не даємо
    existing_bonus = (
        db.query(ReferralBonus)
        .filter(ReferralBonus.invited_user_id == invited_user_id)
        .first()
    )

    if existing_bonus is not None:
        return False

    # Ліміт 5 друзів на день
    today_count = count_today_referral_bonuses(db, referrer_user_id)

    if today_count >= REFERRAL_DAILY_LIMIT:
        return False

    bonus = ReferralBonus(
        referrer_user_id=referrer_user_id,
        invited_user_id=invited_user_id,
        is_used=False,
    )

    db.add(bonus)
    db.commit()

    return True


def use_referral_bonus_spin(db, user_id: str) -> bool:
    """
    Використовує 1 бонусний спін користувача.

    Повертає:
    True — бонусний спін використано
    False — бонусних спінів немає
    """

    user_id = str(user_id)

    bonus = (
        db.query(ReferralBonus)
        .filter(ReferralBonus.referrer_user_id == user_id)
        .filter(ReferralBonus.is_used == False)  # noqa: E712
        .order_by(ReferralBonus.created_at.asc())
        .first()
    )

    if bonus is None:
        return False

    bonus.is_used = True
    bonus.used_at = datetime.datetime.utcnow()

    db.commit()

    return True
# =========================
# АДМІН-СКИДАННЯ
# =========================

def reset_all_registrations(db) -> int:
    """
    Видаляє всі реєстрації користувачів.
    Спіни не чіпає.
    Реферальні бонуси теж не чіпає, щоб один і той самий друг
    не міг давати бонус повторно після скидання реєстрацій.
    """

    deleted_count = db.query(Lead).delete()
    db.commit()

    return deleted_count


def set_spin_blocks_reset_time(db) -> datetime.datetime:
    """
    Ставить системну дату, після якої старі спіни не блокують користувача.
    Тобто всі прокрутки ДО цієї дати більше не враховуються для cooldown.
    """

    reset_time = datetime.datetime.utcnow()
    setting_key = "spin_blocks_reset_at"

    setting = (
        db.query(AppSetting)
        .filter(AppSetting.key == setting_key)
        .first()
    )

    if setting is None:
        setting = AppSetting(
            key=setting_key,
            value=reset_time.isoformat(),
        )
        db.add(setting)
    else:
        setting.value = reset_time.isoformat()

    db.commit()

    return reset_time


def get_spin_blocks_reset_time(db) -> datetime.datetime | None:
    """
    Повертає дату останнього скидання блокувань.
    Усі спіни до цієї дати не враховуються для cooldown.
    """

    setting = (
        db.query(AppSetting)
        .filter(AppSetting.key == "spin_blocks_reset_at")
        .first()
    )

    if setting is None:
        return None

    try:
        return datetime.datetime.fromisoformat(setting.value)
    except Exception:
        return None