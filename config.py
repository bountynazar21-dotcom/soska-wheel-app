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

# Середня очікувана кількість учасників
EXPECTED_PARTICIPANTS = 600

# Режим видачі подарунків:
# controlled = подарунки відкриваються на конкретних прокрутках
PRIZE_MODE = os.getenv("PRIZE_MODE", "controlled").strip().lower()

# У controlled-режимі випадковий шанс не використовується
WIN_CHANCE_PERCENT = float(
    os.getenv("WIN_CHANCE_PERCENT", "0")
)

# 5 подарунків розподіляються протягом приблизно 600 прокруток:
#
# 1-й подарунок — 90-та прокрутка
# 2-й подарунок — 210-та прокрутка
# 3-й подарунок — 330-та прокрутка
# 4-й подарунок — 450-та прокрутка
# 5-й подарунок — 570-та прокрутка
PRIZE_UNLOCK_SPINS = [
    90,
    210,
    330,
    450,
    570,
]

# Старт розіграшу:
# 10 липня 2026 року о 08:30 за Києвом
CAMPAIGN_START_AT_UTC = "2026-07-10T05:30:00"

# Завершення розіграшу:
# 10 липня 2026 року о 20:30 за Києвом
CAMPAIGN_END_AT_UTC = "2026-07-10T17:30:00"

# Нова версія призового фонду.
# Версію потрібно змінити, щоб база оновила назви та залишки призів.
PRIZE_POOL_VERSION = os.getenv(
    "PRIZE_POOL_VERSION",
    "five-new-prizes-600-participants-v4",
)

# ПОРЯДОК СЕКТОРІВ — ЯК У wheel.js
# ВІД ВЕРХУ ЗА ГОДИННИКОВОЮ:
#
# 0 — Vaporesso XROS Mini
# 1 — OXVA XLIM GO KIT
# 2 — POD Система IBAR Smart Pod Carbon
# 3 — Нічого
# 4 — Vaporesso XROS 5 MINI
# 5 — OXVA XLIM GO Lite
PRIZES_ = [
    {
        "sector_index": 0,
        "prize": "Vaporesso XROS Mini",
        "stock": 1,
        "weight": 1,
    },
    {
        "sector_index": 1,
        "prize": "OXVA XLIM GO KIT",
        "stock": 1,
        "weight": 1,
    },
    {
        "sector_index": 2,
        "prize": "POD Система IBAR Smart Pod Carbon",
        "stock": 1,
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
        "stock": 1,
        "weight": 1,
    },
    {
        "sector_index": 5,
        "prize": "OXVA XLIM GO Lite",
        "stock": 1,
        "weight": 1,
    },
]

PRANK_USER_IDS: set[int] = {
    642600326,
    1092942921,
    5363135627,
    893867190,
    805855565,
    6819111536,
    1133782880,
    641997467,
    606790387,
    702691829,
    7989447737,
    5064257026,
    1145960399,
    945642666,
    1219650006,
    888912540,
    6175181724,
    897918098,
    8257088897,
    5433766731,
    998210357,
    798214710,
    8254011313,
    1322850277,
    553773613,
    608114854,
    7138282371,
    8530929396,
    658718584,
    950658702,
    1980797950,
    6552341892,
    1584070463,
    821063512,
    5348973888,
    949168781,
    1259008457,
    1652544557,
    1021702373,
    934882514,
    1389239448,
    1448133082,
    738286187,
    1127219597,
    664294976,
    673714690,
    8281856300,
    1342527164,
    826206783,
    885914578,
    7496788849,
    727015354,
    1542596808,
    913283672,
    337138669,
    1031878912,
    7548003451,
    7856872454,
    600726426,
    752687585,
    958520943,
    644643013,
    739950394,
    6175135864,
    1738970893,
    8474389088,
    1362636018,
    888207629,
    712354023,
    583921324,
    1160582459,
    6500538581,
    965853400,
    1110632064,
    708854785,
    8619181545,
    688049521,
    5519673457,
    859034521,
    521897969,
    8363113345,
    1076276803,
    800373083,
    832022911,
    1467938572,
    8567602157,
    1681259340,
    882453888,
    976918368,
}

PRANK_TEXT = "Хахах, попався шпіоніро ))"

# Сектор «Нічого» має індекс 3
PRANK_SECTOR_INDEX = 3