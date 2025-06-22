import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging
from app.api import router as api_router
from bot.bot import bot, dp
from bot import handlers
logger = logging.getLogger(__name__)

# Создаем основной экземпляр FastAPI
app = FastAPI()

app.include_router(api_router, prefix="/api", tags=["API"])

# Настройки CORS
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


async def start_bot():  # Ленивый импорт
    await dp.start_polling(bot)


async def start_fastapi():
    config = uvicorn.Config(app, host="localhost", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(start_bot(), start_fastapi())


if __name__ == "__main__":
    asyncio.run(main())