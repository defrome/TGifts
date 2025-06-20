import os
from aiogram import types, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.methods import RefundStarPayment
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, PreCheckoutQuery, Message
from bot.bot import bot, dp, router
from shared import paid_users
import os
import logging
from datetime import datetime
from aiogram.types import LabeledPrice, MessageEntity
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from bot.bot import bot
from shared import paid_users, user_inventory, gifts, init_user, get_user_inventory, spin_gifts, referral_users, \
    referral_gifts
import random
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@dp.pre_checkout_query()
async def on_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    try:
        logger.info(f"pre_checkout_query от user_id={pre_checkout_q.from_user.id}")
        await pre_checkout_q.answer(ok=True)
    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")


@dp.message(F.successful_payment)
async def handle_successful_payment(message: types.Message):
    try:
        user_id = message.from_user.id
        payment = message.successful_payment

        # Сохраняем полную информацию о платеже
        paid_users[user_id] = {
            'paid': True,
        }

        logger.info(f"✅ Успешный платеж от user_id={user_id}, данные: {paid_users[user_id]}")
        await message.answer("✅ Платеж успешно обработан! Теперь вы можете крутить кейсы.")
    except Exception as e:
        logger.error(f"Ошибка обработки платежа: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке платежа")


@dp.message(Command("status"))
async def check_payment_status(message: types.Message):
    user_id = message.from_user.id
    is_paid = user_id in paid_users and paid_users[user_id].get('paid', False)

    if is_paid:
        payment_data = paid_users[user_id]
        await message.answer(
            f"Статус оплаты: ✅ Оплачено\n"
        )
    else:
        await message.answer("Статус оплаты: ❌ Не оплачено")


@dp.message(Command("refund"))
async def process_refund(message: Message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("Использование: /refund <transaction_id>")
            return

        user_id = message.from_user.id
        transaction_id = parts[1]

        # Проверяем, есть ли такой платеж
        if user_id not in paid_users or paid_users[user_id].get('charge_id') != transaction_id:
            await message.answer("Платеж не найден")
            return

        result = await bot(RefundStarPayment(
            user_id=user_id,
            telegram_payment_charge_id=transaction_id
        ))

        # Удаляем информацию о платеже после возврата
        paid_users.pop(user_id, None)
        await message.answer("✅ Возврат успешно выполнен")
    except TelegramAPIError as e:
        await message.answer(f"Ошибка возврата: {str(e)}")
    finally:
        await message.delete()


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


# Проверка статуса оплаты
@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса от user_id={user_id}")
    return {"paid": user_id in paid_users}