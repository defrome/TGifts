import os
import asyncio
from aiogram.types import LabeledPrice, Update
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from aiogram import Router, Dispatcher, Bot, types
import uvicorn
from dotenv import load_dotenv

load_dotenv()


# Инициализация бота
bot = Bot(os.getenv('BOT_TOKEN'))
router = Router()
dp = Dispatcher()
dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Настройка вебхука
    url_webhook = "https://tgifts.space/webhook"  # Замените на ваш URL
    await bot.set_webhook(
        url=url_webhook,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    print(f"✅ Вебхук установлен на {url_webhook}")
    yield
    await bot.delete_webhook()
    print("🛑 Вебхук удален")


app = FastAPI(lifespan=lifespan)


@app.get('/payment')
async def create_invoice_link_bot():
   payment_link = await bot.create_invoice_link(
       "Subscription",
       "100 stars",
       "{}",
       "XTR",
       prices=[LabeledPrice(label="Subscription", amount=1)]
   )
   return payment_link


@app.post("/webhook")
async def handle_webhook(request: Request):
    """Обработчик вебхука"""
    update = await request.json()
    if payment := update.get("message", {}).get("successful_payment"):
        print(f"💳 Получен платеж: {payment}")
        return payment
    await dp.feed_update(bot, Update.model_validate(update, context={"bot": bot}))


@router.pre_checkout_query()
async def pre_checkout_handler(query: types.PreCheckoutQuery):
    """Подтверждение платежа"""
    await bot.answer_pre_checkout_query(query.id, ok=True)


if __name__ == "__main__":
    # Проверка переменных окружения
    if not os.getenv('BOT_TOKEN'):
        raise EnvironmentError("❌ Токен бота не найден в переменных окружения")

    # Запуск сервера
    config = uvicorn.Config(
        app,
        host="localhost",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)

    print("🚀 Запуск сервера...")
    asyncio.run(server.serve())