import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bot.bot import bot, dp
from bot.handlers import router as bot_router
from bot import handlers
from app.api import router as api_router
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

# Добавляем все роутеры
app.include_router(api_router)
app.include_router(bot_router)

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting application")
    # Установите вебхук при запуске
    WEBHOOK_URL = "https://yourdomain.com/webhook"
    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )
    yield
    logger.info("👋 Shutting down")
    await bot.delete_webhook()
    await bot.session.close()

async def start_bot():
    dp.include_router(bot_router)
    await dp.start_polling(bot)  # Только для разработки

async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_certfile="/path/to/cert.pem",
        ssl_keyfile="/path/to/key.pem"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Для продакшена используйте только start_fastapi()
    await start_fastapi()
    # Для разработки: await asyncio.gather(start_bot(), start_fastapi())

if __name__ == "__main__":
    asyncio.run(main())