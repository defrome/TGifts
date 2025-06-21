import os
import random
import logging

from aiogram.types import LabeledPrice, MessageEntity
from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse

from bot.bot import bot
from shared import (
    is_user_paid, clear_user_payment, mark_user_as_paid,
    user_inventory, gifts, init_user, get_user_inventory,
    spin_gifts, referral_users, referral_gifts, paid_users
)

logger = logging.getLogger(__name__)

app = FastAPI()


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
    text = "🎁 Тест подарка"
    text_entities = [
        MessageEntity(type="bold", offset=0, length=2),
        MessageEntity(type="italic", offset=3, length=8)
    ]

    try:
        success = await bot.send_gift(
            gift_id=gift_id,
            user_id=user_id,
            pay_for_upgrade=False,
            text=text,
            text_entities=text_entities,
        )
        return {"success": success}
    except Exception as e:
        logger.error(f"Ошибка при отправке подарка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при отправке подарка")


@app.post("/referral_subscribe")
async def subscribe_referral(user_id: int):
    try:
        chat_member = await bot.get_chat_member(chat_id="@tgiftstestdev", user_id=user_id)

        if chat_member.status in ['member', 'administrator', 'creator']:
            referral_users.add(user_id)
            return {"status": "subscribed"}
        return {"status": "not_subscribed"}

    except Exception as e:
        return {"status": "error", "details": str(e)}


@app.post("/referral_spin")
async def referral_spin(user_id: int):
    if user_id not in referral_users:
        raise HTTPException(status_code=400, detail="Вы не прошли задания в реферальной системе или бонусы закончились")

    await init_user(user_id)

    gift = random.choice(referral_gifts)
    user_inventory[user_id]['gifts'].append(gift)
    referral_users.discard(user_id)

    return {
        "telegram_gift_id": gift['telegram_id'],
        "gift_id": gift['gift_id'],
        "emoji": gift['emoji'],
        "image_url": gift['image_path'],
        "star": gift['star']
    }


@app.get("/inventory_check")
async def inventory_check(user_id: int):
    inventory = await get_user_inventory(user_id)
    return {"inventory": inventory}


@app.get("/paid_check")
async def paid_check():
    return {"paid_users": paid_users}


@app.get("/available_gifts")
async def get_available_gifts():
    return await bot.get_available_gifts()


@app.post("/upgrade")
async def upgrade_gift(gift_id: str, user_id: int):
    await init_user(user_id)
    user_gifts = user_inventory[user_id]['gifts']
    gift_to_upgrade = next((g for g in user_gifts if g['gift_id'] == gift_id), None)

    if not gift_to_upgrade:
        raise HTTPException(status_code=400, detail="У вас нет такого подарка")

    user_gifts.remove(gift_to_upgrade)
    new_gift = random.choice(gifts)
    user_gifts.append(new_gift)
    ##
    return {
        "new_telegram_id": new_gift['telegram_id'],
        "new_gift_id": new_gift['gift_id'],
        "emoji": new_gift['emoji'],
        "image_url": new_gift['image_path'],
        "star": new_gift['star']
    }


@app.post("/spin")
async def roulette_spin(user_id: int):
    if not is_user_paid(user_id):
        raise HTTPException(status_code=402, detail="Payment required. Please pay first.")

    try:
        await init_user(user_id)
        gift = random.choice(gifts)
        user_inventory[user_id]['gifts'].append(gift)
        clear_user_payment(user_id)

        return {
            "telegram_gift_id": gift['telegram_id'],
            "gift_id": gift['gift_id'],
            "emoji": gift['emoji'],
            "image_url": gift['image_path'],
            "star": gift['star']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spin failed: {str(e)}")


@app.get("/status")
async def get_payment_status(user_id: int):
    logger.info(f"Запрос статуса оплаты: user_id={user_id}")
    return {"paid": is_user_paid(user_id)}