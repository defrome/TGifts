import os
import asyncio
import random
from fastapi import HTTPException
from typing import Dict
from fastapi.responses import JSONResponse
import logging
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.methods import RefundStarPayment
from aiogram.types import LabeledPrice, Update, Message, MessageEntity
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from aiogram import Router, Dispatcher, Bot, types
import uvicorn
from dotenv import load_dotenv
from shared import spin_gifts, referral_users, init_user, referral_gifts, user_inventory, gifts

load_dotenv()

# Временная база данных

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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Улучшенный обработчик вебхука с полной диагностикой"""
    try:
        # 1. Логируем входящий запрос
        body = await request.body()
        logger.info(f"📨 Входящий запрос: {body.decode()}")

        # 2. Парсим JSON
        try:
            update_data = await request.json()
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            return JSONResponse(
                content={"status": "error", "detail": "Invalid JSON"},
                status_code=400
            )

        # 3. Валидируем структуру обновления
        if not isinstance(update_data, dict):
            logger.error("⚠️ Неверный формат обновления")
            return JSONResponse(
                content={"status": "error", "detail": "Invalid update format"},
                status_code=400
            )

        # 4. Обрабатываем платежи
        if update_data.get("message", {}).get("successful_payment"):
            payment = update_data["message"]["successful_payment"]
            user_id = update_data["message"]["from"]["id"]

            paid_users[user_id] = {
                "user_id": user_id
            }
            logger.info(f"💳 Получен платеж: {payment}")

            # Здесь можно добавить дополнительную обработку платежа
            return JSONResponse(
                content={"status": "success", "payment": payment},
                status_code=200
            )

        # 5. Пробуем обработать через диспетчер
        try:
            update = Update.model_validate(update_data, context={"bot": bot})
            await dp.feed_update(bot, update)
            logger.info("🔄 Обновление передано диспетчеру")
            return JSONResponse(
                content={"status": "success"},
                status_code=200
            )
        except Exception as e:
            logger.error(f"⚠️ Ошибка обработки обновления: {e}")
            return JSONResponse(
                content={"status": "error", "detail": str(e)},
                status_code=500
            )

    except Exception as e:
        logger.critical(f"🔥 Критическая ошибка: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "detail": "Internal server error"},
            status_code=500
        )

@app.post("/referral_subscribe")
async def subscribe_referral(user_id: int):

    try:
        chat_member = await bot.get_chat_member(chat_id="@tgiftstestdev", user_id=user_id)

        if chat_member.status in ['member', 'administrator', 'creator']:
            referral_users.add(user_id)
            return {"status": "subscribed"}

        else:
            return {"status": "not_subscribed"}


    except Exception as e:

        return {"status": "error", "details": str(e)}


@app.post("/referral_spin")
async def referral_spin(user_id: int):
    if user_id not in referral_users:
        raise HTTPException(status_code=400, detail="Вы не прошли задания в реферальной системе или ваши реферальные бонусы закончились")

    else:
        await init_user(user_id)

        gift_id = random.choice(referral_gifts)

        # Добавляем подарок в инвентарь
        user_inventory[user_id]['gifts'].append(gift_id)

        # Безопасно удаляем пользователя из списка прошедших реферальную систему
        referral_users.remove(user_id)  # Не вызовет ошибку, если user_id нет

        return {"telegram_gift_id": gift_id['telegram_id'],
                "gift_id": gift_id['gift_id'],
                "emoji": gift_id['emoji'],
                "image_url": gift_id['image_path'],
                "star": gift_id['star']}

@app.get("/get_spin_gifts", response_class=JSONResponse)
async def get_spin_gifts():

    return spin_gifts


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


@app.get("/paid_check")
async def paid_check():
    paid = paid_users
    return {"paid_users": paid}

@app.get("/available_gifts")
async def get_available_gifts():
    Gifts = await bot.get_available_gifts()
    return Gifts

# Апгрейд подарка
@app.post("/upgrade")
async def upgrade_gift(gift_id: str, user_id: int):  # Изменили тип gift_id на str
    await init_user(user_id)

    # Проверяем наличие подарка в инвентаре
    user_gifts = user_inventory[user_id]['gifts']
    gift_to_upgrade = next((g for g in user_gifts if g['gift_id'] == gift_id), None)

    if not gift_to_upgrade:
        raise HTTPException(status_code=400, detail="У вас нет такого подарка в инвентаре")

    # Удаляем старый подарок
    user_gifts.remove(gift_to_upgrade)

    # Выбираем случайный новый подарок (можно добавить логику улучшения)
    new_gift = random.choice(gifts)

    # Добавляем новый подарок в инвентарь
    user_gifts.append({
        "telegram_id": new_gift['telegram_id'],
        "gift_id": new_gift['gift_id'],
        "emoji": new_gift['emoji'],
        "image_path": new_gift['image_path'],
        "star": new_gift['star']
    })

    return {
        "new_telegram_id": new_gift['telegram_id'],
        "new_gift_id": new_gift['gift_id'],
        "emoji": new_gift['emoji'],
        "image_url": new_gift['image_path'],
        "star": new_gift['star']
    }


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
        user_inventory[user_id]['gifts'].append(gift_id)

        # Безопасно удаляем пользователя из списка оплативших
        paid_users.pop(user_id, None)  # Не вызовет ошибку, если user_id нет

        return {"telegram_gift_id": gift_id['telegram_id'],
                "gift_id": gift_id['gift_id'],
                "emoji": gift_id['emoji'],
                "image_url": gift_id['image_path'],
                "star": gift_id['star']}

    except Exception as e:
        # В случае ошибки оставляем пользователя в paid_users для повторной попытки
        raise HTTPException(
            status_code=500,
            detail=f"Spin failed: {str(e)}"
        )


@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса от user_id={user_id}")
    return {"paid": user_id in paid_users}


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