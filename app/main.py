import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.bot import bot, dp
from bot.handlers import command_start_handler, on_pre_checkout, on_message, check_payment_status, process_refund
from app.api import app as fastapi_app, app
import logging

logger = logging.getLogger(__name__)

origins = ["*"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск приложения")
    # Запускаем бота в фоне
    asyncio.create_task(start_bot())
    yield
    logger.info("👋 Завершение работы")
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def start_bot():
    """Запуск long polling бота"""
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
    finally:
        logger.info("Bot polling stopped")

async def start_fastapi():
    """Запуск FastAPI сервера"""
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000)  # Изменил порт на 8000
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Основная функция запуска"""
    await start_fastapi()  # Запускаем только FastAPI, бот запускается через lifespan

if __name__ == "__main__":
    asyncio.run(main())