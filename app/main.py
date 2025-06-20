import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from bot.bot import bot, dp
from app.api import app as fastapi_app, app
import logging

logger = logging.getLogger(__name__)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск приложения")
    yield
    logger.info("👋 Завершение работы")

async def start_bot():
    await dp.start_polling(bot)

async def start_fastapi():
    config = uvicorn.Config(fastapi_app, host="localhost", port=8001)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(start_bot(), start_fastapi())

if __name__ == "__main__":
    asyncio.run(main())