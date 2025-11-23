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
    f"{APP_BASE_URL}/static/assets/index.html?v=1",
)


# Адміни
ADMINS: set[int] = {
    769431786,
    5480082089,
}

# Призи
PRIZES = [
    "Рідина Punch",
    "Знижка 31%",
    "Pod система",
    "Мерч Soska Bar",
    "Дві рідини",
    "Картридж",
    "Нічого 😅",
    "Сюрприз",
]
