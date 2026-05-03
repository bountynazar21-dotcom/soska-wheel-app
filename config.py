import os

APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://soska-wheel-app-production.up.railway.app",
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html?v=4",
)

ADMINS: set[int] = {
    5480082089,
}

# ПОРЯДОК ПРЕЗІВ = ЯК НА КОЛЕСІ ПО КОЛУ,
# ПОЧИНАЮЧИ З ВЕРХУ (12:00) І ДАЛІ ЗА ГОДИННИКОВОЮ
PRIZES_WEIGHTS = [
    ("Відкривачок x10", 5),
    ("Ланцюжок + кліп-холдер x6", 8),
    ("Стікери + ручка x20", 12),
    ("Стрічки + пахучки x30", 25),
    ("Павучки x45", 10),
    ("Стрічки x55", 10),
    ("Стікери x70", 25),
    ("Аромакомпозиції x5", 5),
]

PRIZES = [p for p, _ in PRIZES_WEIGHTS]
WEIGHTS = [w for _, w in PRIZES_WEIGHTS]


