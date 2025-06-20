import os

from aiogram import types
from aiogram.types import LabeledPrice, MessageEntity, Update
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from bot.bot import bot
from shared import paid_users, user_inventory, gifts, init_user, get_user_inventory, spin_gifts, referral_users, \
    referral_gifts
import random
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    webhook_url = f"https://tgifts.space/webhook"
    await bot.set_webhook(
        url=webhook_url,
    )
    logger.info("Бот запущен, вебхук установлен")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logger.info("off")


@app.post("/webhook")
async def handle_webhook(update: dict):
    try:
        telegram_update = types.Update(**update)

        if telegram_update.message and telegram_update.message.successful_payment:
            user_id = telegram_update.message.from_user.id
            paid_users.add(user_id)
            logger.info(f"Пользователь {user_id} успешно оплатил")

            await bot.send_message(
                chat_id=user_id,
                text="✅ Платеж успешно получен! Теперь вы можете крутить рулетку."
            )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
        raise HTTPException(status_code=400, detail="Invalid update data")

@app.get("/payment")
async def create_invoice_link_bot():
    payment_link = await bot.create_invoice_link(
        title="Case",
        description="1 stars",
        payload="{}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Кейс с подарками", amount=1)],
    )
    logger.info("Создана ссылка на оплату")
    return {"invoice_link": payment_link}


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



# Проверка инвентаря
@app.get("/inventory_check")
async def inventory_check(user_id: int):
    inventory = await get_user_inventory(user_id)
    return {"inventory": inventory}

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

@app.post("/payment_handler")
async def handle_payment(update: Update):
    if update.message and update.message.successful_payment:
        user_id = update.message.from_user.id
        paid_users.add(user_id)
        logger.info(f"Пользователь {user_id} успешно оплатил")
        await bot.send_message(user_id, "✅ Платеж успешно получен! Теперь вы можете крутить рулетку.")
    return {"status": "ok"}

# Проверка статуса оплаты
@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса от user_id={user_id}")
    return {"paid": user_id in paid_users}

