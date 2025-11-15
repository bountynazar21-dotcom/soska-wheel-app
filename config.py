import os

# Токен бота (краще тримати в env, а не хардкодити)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8302313515:AAG9hG6lAxhkiERKqNF5rINL2fuIiIz2Bb0")

# Базовий URL твого Railway-деплою
APP_BASE_URL = os.environ.get(
    "APP_BASE_URL",
    "https://soska-wheel-app-production.up.railway.app"
)

# URL WebApp
WEBAPP_URL = os.environ.get(
    "WEBAPP_URL",
    f"{APP_BASE_URL}/static/index.html"
)

# Адміни
ADMINS: set[int] = {
    769431786,
    5480082089,
}

# Список призів
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
