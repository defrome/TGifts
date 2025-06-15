import asyncio
import os
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from aiogram.types import LabeledPrice, Message, WebAppInfo, PreCheckoutQuery, Update
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
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

# Память об оплативших
paid_users = {}

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

# Проверка оплаты (для фронта)
@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса от user_id={user_id}")
    return {"paid": user_id in paid_users}

# Webhook (если будешь использовать)
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}

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
        await message.reply("Вы оплатили.")
    else:
        await message.reply("Вы еще не оплатили.")

# Команда /refund
# Команда /refund
@dp.message(Command("refund"))
async def handle_refund(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"💬 Команда /refund от user_id={user_id}")

    if user_id not in paid_users:
        await message.reply("❌ Вы еще не оплатили, нечего возвращать.")
        logger.warning(f"❗ Попытка возврата без оплаты от user_id={user_id}")
        return

    charge_id = paid_users[user_id]

    try:
        # Симуляция возврата (здесь должна быть реальная логика возврата через API, если есть)
        # Например: await external_api.refund(user_id, charge_id)
        del paid_users[user_id]
        await message.reply("✅ Возврат успешно выполнен.")
        logger.info(f"💸 Возврат выполнен для user_id={user_id}, charge_id={charge_id}")
    except Exception as e:
        logger.error(f"🔥 Ошибка при возврате для user_id={user_id}: {e}")
        await message.reply("❌ Возврат не удался.")

# Запуск бота
async def start_bot():
    await dp.start_polling(bot)

# Запуск FastAPI
async def start_fastapi():
    config = uvicorn.Config(app, host="localhost", port=8001, log_level="info")
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