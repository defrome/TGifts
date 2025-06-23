import os
import asyncio

from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.methods import RefundStarPayment
from aiogram.types import LabeledPrice, Update, Message
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from aiogram import Router, Dispatcher, Bot, types
import uvicorn
from dotenv import load_dotenv

load_dotenv()

paid_users = {}

# Инициализация бота
bot = Bot(os.getenv('BOT_TOKEN'))
router = Router()
dp = Dispatcher()
dp.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Контекстный менеджер для управления жизненным циклом вебхука"""
    try:
        # Настройка вебхука
        url_webhook = "https://tgifts.space/webhook"

        # Удаляем предыдущий вебхук (на всякий случай)
        try:
            await bot.delete_webhook()
            print("🔄 Предыдущий вебхук удален")
        except Exception as e:
            print(f"⚠️ Ошибка при удалении старого вебхука: {e}")

        # Устанавливаем новый вебхук
        webhook_info = await bot.set_webhook(
            url=url_webhook,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )

        # Проверяем установку вебхука
        current_webhook = await bot.get_webhook_info()
        print(f"✅ Вебхук установлен. Текущие настройки: {current_webhook}")

        yield

    except Exception as e:
        print(f"🔥 Критическая ошибка в lifespan: {e}")
        raise
    finally:
        try:
            await bot.delete_webhook()
            print("🛑 Вебхук успешно удален")
        except Exception as e:
            print(f"⚠️ Ошибка при удалении вебхука: {e}")


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
   return {"payment_link": payment_link}


@app.post("/webhook")
async def handle_webhook(request: Request):
    """Обработчик вебхука"""
    update = await request.json()
    if payment := update.get("message", {}).get("successful_payment"):
        print(f"💳 Получен платеж: {payment}")
        return payment
    await dp.feed_update(bot, Update.model_validate(update, context={"bot": bot}))

@app.post("/check_payment")
async def user_payment_check():
    return paid_users


@router.pre_checkout_query()
async def pre_checkout_handler(query: types.PreCheckoutQuery):
    """Подтверждение платежа"""
    await bot.answer_pre_checkout_query(query.id, ok=True)

@router.message()
async def on_message(msg: types.Message):
    if msg.successful_payment:
        user_id = msg.from_user.id
        charge_id = msg.successful_payment.telegram_payment_charge_id
        paid_users[user_id] = charge_id
        print(f"✅ Успешный платеж от user_id={user_id}, charge_id={charge_id}")
        await msg.reply("Спасибо за ваш платеж! Ваша покупка завершена.")

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