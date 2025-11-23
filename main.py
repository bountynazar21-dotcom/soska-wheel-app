import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse

from database import Base, engine
from routes.spin import router as spin_router
from routes.admin import router as admin_router
from bot import run_bot, shutdown_bot

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")

# Створення таблиць БД
Base.metadata.create_all(bind=engine)

# Маршрути
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


# ======== HEALTHCHECK ========

@app.get("/ping")
async def ping():
    return JSONResponse({"status": "ok"})


# ======== ROOT → STATIC ========

@app.get("/")
async def root():
    # щоб при вході на домен відкривалось колесо
    return RedirectResponse(url="/static/assets/index.html?v=1")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  # Railway підставляє свій PORT

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
