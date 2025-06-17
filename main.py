import asyncio
import os
import random
from typing import List

from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram.types import LabeledPrice, Message, WebAppInfo, PreCheckoutQuery, MessageEntity
from aiogram.methods.get_available_gifts import GetAvailableGifts
from aiogram.methods.refund_star_payment import RefundStarPayment
from aiogram.exceptions import TelegramAPIError
from fastapi import FastAPI, HTTPException
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

# Хранилища данных
paid_users = {}
user_inventory = {}

# Список подарков и их айди
gifts = [
    {"telegram_id": "5170145012310081615", "gift_id": "1", "emoji": "💝", "image_url": "http://localhost:8001/gifts/heart.png"},
    {"telegram_id": "5170233102089322756", "gift_id": "2", "emoji": "🧸"},
    {"telegram_id": "5170250947678437525", "gift_id": "3", "emoji": "🎁"},
    {"telegram_id": "5168103777563050263", "gift_id": "4", "emoji": "🌹"},
    {"telegram_id": "5170144170496491616", "gift_id": "5", "emoji": "🎂"},
    {"telegram_id": "5170314324215857265", "gift_id": "6", "emoji": "💐"},
    {"telegram_id": "5170564780938756245", "gift_id": "7", "emoji": "🚀"},
    {"telegram_id": "5168043875654172773", "gift_id": "8", "emoji": "🏆"},
    {"telegram_id": "5170690322832818290", "gift_id": "9", "emoji": "💍"},
    {"telegram_id": "5170521118301225164", "gift_id": "10", "emoji": "💎"},
    {"telegram_id": "6028601630662853006", "gift_id": "11", "emoji": "🍾"}
]


async def init_user(user_id: int):
    """Инициализирует запись для нового пользователя"""
    if user_id not in user_inventory:
        user_inventory[user_id] = {'gifts': []}


async def get_user_inventory(user_id: int):
    """Возвращает инвентарь пользователя"""
    await init_user(user_id)
    return user_inventory.get(user_id)


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
        payload="{}",
        provider_token=os.getenv("PAYMENT_PROVIDER_TOKEN"),
        currency="XTR",
        prices=[LabeledPrice(label="Кейс с подарками", amount=1)],
    )
    logger.info("Создана ссылка на оплату")
    return {"invoice_link": payment_link}

# Выдача подарка
@app.get("/sendgift")
async def send_telegram_gift(gift_id: str, user_id: int):

    # Опциональные параметры
    text = "🎁 Тест подарка"
    text_entities = [
        MessageEntity(type="bold", offset=0, length=2),  # Жирный смайлик 🎁
        MessageEntity(type="italic", offset=3, length=8)  # Курсив "подарок"
    ]


    try:
        # Отправка подарка
        success = await bot.send_gift(
            gift_id=gift_id,
            user_id=user_id,  # ИЛИ chat_id=chat_id,
            pay_for_upgrade=False,  # Оплатить из баланса бота
            text=text,
            text_entities=text_entities,  # ИЛИ text_parse_mode="HTML"
        )

        if success:
            print("✅ Подарок успешно отправлен!")
        else:
            print("❌ Ошибка при отправке подарка.")

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")


# Проверка инвентаря
@app.get("/inventory_check")
async def inventory_check(user_id: int):
    inventory = await get_user_inventory(user_id)
    return {"inventory": inventory['gifts']}

@app.get("/available_gifts")
async def get_available_gifts():
    Gifts = await bot.get_available_gifts()
    return Gifts

# Апгрейд подарка
@app.post("/upgrade")
async def upgrade_gift(gift_id: int, user_id: int):
    await init_user(user_id)

    if gift_id not in user_inventory[user_id]['gifts']:
        raise HTTPException(status_code=400, detail="У вас нет такого подарка в инвентаре")

    user_inventory[user_id]['gifts'].remove(gift_id)
    new_gift_id = random.choice(gifts)
    user_inventory[user_id]['gifts'].append(new_gift_id)

    return {"new_gift_id": new_gift_id['telegram_id']}


# Рулетка
@app.post("/spin")
async def roulette_spin(user_id: int):
    # Проверяем, что пользователь оплатил
    if user_id not in paid_users:
        raise HTTPException(
            status_code=402,
            detail="Payment required. Please pay first."
        )

    try:
        # Инициализируем пользователя (если еще не инициализирован)
        await init_user(user_id)

        # Выбираем случайный подарок
        gift_id = random.choice(gifts)


        # Добавляем подарок в инвентарь
        user_inventory[user_id].setdefault('gifts', []).append(gift_id)

        # Безопасно удаляем пользователя из списка оплативших
        paid_users.pop(user_id, None)  # Не вызовет ошибку, если user_id нет

        return {
            "gift_id": gift_id['telegram_id'],
        }

    except Exception as e:
        # В случае ошибки оставляем пользователя в paid_users для повторной попытки
        raise HTTPException(
            status_code=500,
            detail=f"Spin failed: {str(e)}"
        )


# Проверка статуса оплаты
@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса от user_id={user_id}")
    return {"paid": user_id in paid_users}


# Обработчики платежей
@router.pre_checkout_query(lambda q: True)
async def on_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    logger.info(f"pre_checkout_query от user_id={pre_checkout_q.from_user.id}")
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


@router.message()
async def on_message(msg: types.Message):
    if msg.successful_payment:
        user_id = msg.from_user.id
        charge_id = msg.successful_payment.telegram_payment_charge_id
        paid_users[user_id] = charge_id
        logger.info(f"✅ Успешный платеж от user_id={user_id}, charge_id={charge_id}")
        await msg.reply("Спасибо за ваш платеж! Ваша покупка завершена.")


# Команды бота
@dp.message(Command("status"))
async def check_payment_status(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"/status от user_id={user_id}")
    if user_id in paid_users:
        await message.reply("Вы оплатили.")
    else:
        await message.reply("Вы еще не оплатили.")


@dp.message(Command("refund"))
async def process_refund(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /refund <transaction_id>")
        return

    transaction_id = parts[1]
    try:
        result = await bot(RefundStarPayment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        ))
        await message.answer("Возврат успешно выполнен")
    except TelegramAPIError as e:
        await message.answer(f"Ошибка возврата: {str(e)}")
    finally:
        await message.delete()


# Запуск приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Запуск приложения")
    yield
    logger.info("👋 Завершение работы")


app.router.lifespan_context = lifespan


async def start_bot():
    await dp.start_polling(bot)


async def start_fastapi():
    config = uvicorn.Config(
        app,
        host="localhost",
        port=8001,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        start_bot(),
        start_fastapi()
    )


if __name__ == "__main__":
    asyncio.run(main())