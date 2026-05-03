import os

APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://soska-wheel-app-production.up.railway.app",
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html?v=10",
)

ADMINS: set[int] = {
    5480082089,
}

# ПОРЯДОК ПРЕЗІВ = ЯК НА КОЛЕСІ
# ВІД ВЕРХУ (12:00) ПО ГОДИННИКОВІЙ
PRIZES_WEIGHTS = [
    ("Смартфон", 5),
    ("Ноутбук", 5),
    ("Навушники", 10),
    ("Велосипед", 5),
    ("Годинник", 10),
    ("Книга", 20),
    ("Кава", 25),
    ("Торт", 20),
]

PRIZES = [p for p, _ in PRIZES_WEIGHTS]
WEIGHTS = [w for _, w in PRIZES_WEIGHTS]
