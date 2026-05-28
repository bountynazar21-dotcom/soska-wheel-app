import os

APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://soska-wheel-app-production.up.railway.app",
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html?v=20",
)

ADMINS: set[int] = {
    5480082089,
}

# Telegram канал
CHANNEL_USERNAME = "@soska_bar"
CHANNEL_URL = "https://t.me/soska_bar"

# Через скільки днів можна крутити знову
SPIN_COOLDOWN_DAYS = 6

# ПОРЯДОК СЕКТОРІВ = ЯК НА КОЛЕСІ
# ВІД ВЕРХУ ЗА ГОДИННИКОВОЮ
PRIZES_ = [
    {
        "sector_index": 0,
        "prize": "iPhone 17",
        "stock": 0,   # ніколи не випадає
        "weight": 0,
    },
    {
        "sector_index": 1,
        "prize": "Pod Xlim GO Lite",
        "stock": 1,
        "weight": 10,
    },
    {
        "sector_index": 2,
        "prize": "Нічого",
        "stock": None,  # безлімітно
        "weight": 50,
    },
    {
        "sector_index": 3,
        "prize": "Pod Xlim GO Lite",
        "stock": 1,
        "weight": 10,
    },
    {
        "sector_index": 4,
        "prize": "Pod Xlim GO Lite",
        "stock": 1,
        "weight": 10,
    },
    {
        "sector_index": 5,
        "prize": "Pod Xlim Pro 2",
        "stock": 1,
        "weight": 10,
    },
]