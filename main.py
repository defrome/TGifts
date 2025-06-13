import asyncio
import os

from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import uvicorn
from aiogram.types import LabeledPrice, Message, WebAppInfo
from fastapi import FastAPI
from contextlib import asynccontextmanager
from aiogram.types import Update
from fastapi import FastAPI
from fastapi.requests import Request
from starlette.responses import JSONResponse
from aiogram import Router, Dispatcher, Bot, types, html

# Bot initialization
my_router = Router()
dp = Dispatcher()
app = FastAPI()

load_dotenv()  # Загружаем переменные из .env

bot = Bot(token=os.getenv("BOT_TOKEN"))


@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    # Создаем клавиатуру с кнопкой
    builder = InlineKeyboardBuilder()

    # Добавляем кнопку с WebApp
    builder.button(
        text="Играть",
        web_app=WebAppInfo(url=os.getenv("WEB_URL"))
    )

    # Отправляем сообщение с кнопкой
    await message.answer(
        f"Привет, {message.from_user.full_name}! Ждем тебя в нашем боте, поскорее крути кейсы!",
        reply_markup=builder.as_markup()
    )

@app.get('/payment')
async def create_invoice_link_bot():
   payment_link = await bot.create_invoice_link(
       "Case",
       "25 stars",
       "{}",
       "XTR",
       prices=[LabeledPrice(label="Кейс с подарками", amount=25)]
   )
   return payment_link

# Lifespan manager for FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    url_webhook = "https://localhost:8001/webhook"
    await bot.set_webhook(url=url_webhook,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    yield
    await bot.delete_webhook()

# Accepting payments
@my_router.pre_checkout_query(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@app.post("/webhook")
async def webhook(request: Request):
    new_update_msg = await request.json()
    successful_payment = new_update_msg.get("message", {}).get("successful_payment")
    if successful_payment:
       return JSONResponse ({'response': successful_payment})
    update = Update.model_validate(new_update_msg, context={"bot": bot})
    await dp.feed_update(bot, update)

async def start_bot():
    await dp.start_polling(bot)

async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="localhost",
        port=8001,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    # Запускаем оба сервиса параллельно
    await asyncio.gather(
        start_bot(),
        start_fastapi()
    )

if __name__ == "__main__":
    asyncio.run(main())