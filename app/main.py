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
import logging

logger = logging.getLogger(__name__)

origins = ["*"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск приложения")
    # Регистрируем хэндлеры
    dp.include_router(command_start_handler.router)
    dp.include_router(on_pre_checkout.router)
    dp.include_router(on_message.router)
    dp.include_router(check_payment_status.router)
    dp.include_router(process_refund.router)

    # Запускаем бота в фоне
    asyncio.create_task(run_polling())
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


async def run_polling():
    """Запуск long polling"""
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        logger.info("Bot polling stopped")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)