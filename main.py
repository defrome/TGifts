import asyncio
import os
import random
from typing import List

from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram.types import LabeledPrice, Message, WebAppInfo, PreCheckoutQuery, Update
from aiogram.methods.refund_star_payment import RefundStarPayment
from aiogram.exceptions import TelegramAPIError
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import certifi

from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from aiogram import Router, Dispatcher, Bot, types
import uvicorn
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Инициализация бота и FastAPI
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
app = FastAPI()
router = Router()
dp.include_router(router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Память об оплативших
paid_users = {}

# Тестовое хранилище подарков юзера
user_inventory = {}

# Команда /start
@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Играть",
        web_app=WebAppInfo(url=os.getenv("WEB_URL"))
    )
    await message.answer(
        f"Привет, {message.from_user.full_name}! Ждем тебя в нашем боте, поскорее крути кейсы!",
        reply_markup=builder.as_markup()
    )
    logger.info(f"/start от user_id={message.from_user.id}")

# Генерация инвойса
@app.get("/payment")
async def create_invoice_link_bot():
    payment_link = await bot.create_invoice_link(
        title="Case",
        description="1 stars",
        payload="{}",  # Можешь вставить user_id, если нужно
        provider_token="",  # Укажи токен от Telegram
        currency="XTR",
        prices=[LabeledPrice(label="Кейс с подарками", amount=1)],
    )
    logger.info("Создана ссылка на оплату")
    return {"invoice_link": payment_link}

async def init_user(user_id: int):
    """Инициализирует запись для нового пользователя"""
    if user_id not in user_inventory:
        user_inventory[user_id] = {
            'gifts': [],
        }

async def add_gift(user_id: int, gift_id: int):
    init_user(user_id)
    user_inventory[user_id].append(gift_id)



# Логика для тестов
@app.get("/inventory_check")
async def check_inventory(user_id: int):
    return user_inventory[user_id]

# Апгрейд
@app.post("/upgrade")
async def upgrade_gift(gift_id: int):

    if gift_id in user_inventory:
        upgrade_gift_id = random.randint(0, 7)
        user_inventory.remove(gift_id)
        user_inventory.append(upgrade_gift_id)
        if upgrade_gift_id == 0:
            user_inventory.remove(upgrade_gift_id)
            return {"Fail": "Повезет в следующий раз"}

        else:
            return {"Gift upgrade": upgrade_gift_id}
    else:
        return {"Такого подарка нет в вашем инвентаре"}

# Рулетка
@app.post("/spin")
async def roulette_spin(user_id: int):
    if user_id in paid_users:
        gift = random.randint(1,7)
        user_inventory.append(gift)
        return {"gift": gift}
    else:
        return {"error": "Оплата не прошла"}

# Проверка оплаты (для фронта)
@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса от user_id={user_id}")
    return {"paid": user_id in paid_users}


# Заглушка lifespan (polling вместо webhook)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("⚠️ Webhook отключён — используется polling.")
    yield
    logger.info("👋 Завершение FastAPI.")

app.router.lifespan_context = lifespan

# Подтверждение оплаты
@router.pre_checkout_query(lambda q: True)
async def on_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    logger.info(f"pre_checkout_query от user_id={pre_checkout_q.from_user.id}")
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# Обработка успешного платежа
@router.message()
async def on_message(msg: types.Message):
    if msg.successful_payment:
        user_id = msg.from_user.id
        charge_id = msg.successful_payment.telegram_payment_charge_id
        paid_users[user_id] = charge_id
        logger.info(f"✅ Успешный платеж от user_id={user_id}, charge_id={charge_id}")
        await msg.reply("Спасибо за ваш платеж! Ваша покупка завершена.")

# Команда /status
@dp.message(Command("status"))
async def check_payment_status(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"/status от user_id={user_id}")
    if user_id in paid_users:
        true_payment = await message.reply("Вы оплатили.")
    else:
        await message.reply("Вы еще не оплатили.")

# Команда /refund
@dp.message(Command("refund"))
async def process_refund(message: Message, bot: Bot) -> None:
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer()
        await message.delete()
        return

    transaction_id = parts[1]
    try:
        result = await bot(RefundStarPayment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        ))
        await message.delete()
    except TelegramAPIError:
        await message.answer()
        await message.delete()

# Запуск бота
async def start_bot():
    await dp.start_polling(bot)

# Запуск FastAPI
async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="localhost",
        port=8002,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

# Главный запуск
async def main():
    await asyncio.gather(
        start_bot(),
        start_fastapi()
    )

if __name__ == "__main__":
    asyncio.run(main())