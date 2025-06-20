import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from bot.bot import bot, dp
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(router)

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
    yield
    logger.info("👋 Shutting down")
    await bot.session.close()

async def start_bot():
    from bot import handlers  # Импорт обработчиков после инициализации
    await dp.start_polling(bot)

async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="localhost",
        port=8001,
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(start_bot(), start_fastapi())

if __name__ == "__main__":
    asyncio.run(main())