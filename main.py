from typing import AsyncGenerator

from aiogram import Bot, Dispatcher, F
from aiogram.client import bot
from aiogram.types import Message, Update, WebAppInfo
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from config_reader import config

async def lifespan(app: FastAPI) -> AsyncGenerator:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    yield
    # Shutdown logic
    await bot.session.close()


bot = Bot(config.BOT_TOKEN.get_secret_value())

dp = Dispatcher()

app = FastAPI(lifespan=lifespan)

markup = (
    InlineKeyboardBuilder()
    .button(text="Open app", web_app=WebAppInfo(url=config.WEBAPP_URL))
).as_markup()

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Hello!", reply_markup=markup)

@app.post(config.WEBHOOK_PATH)
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={'bot': bot})
    await dp.feed_update(bot, update)

if __name__ == "__main__":
    uvicorn.run(app, host=config.APP_HOST, port=config.APP_PORT)
