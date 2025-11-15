import os

# Базовий URL твого Railway-домену
APP_BASE_URL = os.getenv(
    "APP_BASE_URL",
    "https://soska-wheel-app-production.up.railway.app",
)

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# WebApp URL (колесо)
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html",
)

# Адміни
ADMINS: set[int] = {
    769431786,
    5480082089,
}

# Призи
PRIZES = [
    "Знижка 10%",
    "Знижка 15%",
    "Знижка 20%",
    "Подарунок від Punch",
    "Подарунок від Soska Bar",
    "Рідина 30 мл",
    "Картридж",
    "Мерч Soska Bar x Punch",
]
