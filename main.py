import asyncio
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routes.spin import router as spin_router
from routes.admin import router as admin_router
from bot import run_bot, shutdown_bot

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")

# Створення таблиць БД (на всякий випадок)
Base.metadata.create_all(bind=engine)

# Підключаємо маршрути
app.include_router(spin_router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    asyncio.create_task(run_bot())
    logging.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown():
    await shutdown_bot()
    logging.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
