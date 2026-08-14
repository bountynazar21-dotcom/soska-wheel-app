import os

APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://soska-wheel-newtt-production.up.railway.app",
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html?v=38",
)

ADMINS: set[int] = {
    5480082089,
}

CHANNEL_USERNAME = "@soska_bar"
CHANNEL_URL = "https://t.me/soska_bar"

SPIN_COOLDOWN_DAYS = 7

# Ліміт друзів, за яких можна отримати бонусні спіни за день
REFERRAL_DAILY_LIMIT = int(os.getenv("REFERRAL_DAILY_LIMIT", "5"))

# Максимальна очікувана кількість учасників
EXPECTED_PARTICIPANTS = 850

# Режим видачі подарунків:
# controlled = подарунки відкриваються на конкретних прокрутках
PRIZE_MODE = os.getenv("PRIZE_MODE", "controlled").strip().lower()

# У controlled-режимі випадковий шанс не використовується
WIN_CHANCE_PERCENT = float(
    os.getenv("WIN_CHANCE_PERCENT", "0")
)

# Версія призового фонду
PRIZE_POOL_VERSION = os.getenv(
    "PRIZE_POOL_VERSION",
    "five-prizes-850-participants-v5",
)

# 5 подарунків на 850 учасників
PRIZE_UNLOCK_SPINS = [
    130,
    300,
    400,
    560,
    730,
]

# Старт розіграшу:
# 14 серпня 2026 року о 09:00 за Києвом
CAMPAIGN_START_AT_UTC = "2026-08-14T06:00:00"

# Завершення розіграшу:
# 14 серпня 2026 року о 21:00 за Києвом
CAMPAIGN_END_AT_UTC = "2026-08-14T18:00:00"

# ПОРЯДОК СЕКТОРІВ — ЯК У wheel.js
#
# 0 — Vaporesso XROS Mini
# 1 — OXVA XLIM GO KIT
# 2 — POD Система IBAR Smart Pod Carbon
# 3 — Нічого
# 4 — Vaporesso XROS 5 MINI
# 5 — OXVA XLIM GO Lite

PRIZES = [
    {
        "sector_index": 0,
        "prize": "Vaporesso XROS Mini",
        "stock": 3,
        "weight": 1,
    },
    {
        "sector_index": 1,
        "prize": "OXVA XLIM GO KIT",
        "stock": 0,
        "weight": 1,
    },
    {
        "sector_index": 2,
        "prize": "POD Система IBAR Smart Pod Carbon",
        "stock": 0,
        "weight": 1,
    },
    {
        "sector_index": 3,
        "prize": "Нічого",
        "stock": None,
        "weight": 50,
    },
    {
        "sector_index": 4,
        "prize": "Vaporesso XROS 5 MINI",
        "stock": 0,
        "weight": 1,
    },
    {
        "sector_index": 5,
        "prize": "OXVA XLIM GO Lite",
        "stock": 2,
        "weight": 1,
    },
]

# Список prank-користувачів очищений
PRANK_USER_IDS: set[int] = set()

PRANK_TEXT = "Хахах, попався шпіоніро ))"

# Сектор «Нічого» має індекс 3
PRANK_SECTOR_INDEX = 3