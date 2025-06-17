import os

from aiogram.types import LabeledPrice
from fastapi import FastAPI, HTTPException
from bot.bot import bot
from shared import paid_users, user_inventory, gifts, init_user, get_user_inventory
import random
import logging

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
    return {"invoice_link": payment_link}


@app.post("/spin")
async def roulette_spin(user_id: int):
    if user_id not in paid_users:
        raise HTTPException(status_code=402, detail="Payment required")

    await init_user(user_id)
    gift = random.choice(gifts)
    user_inventory[user_id]['gifts'].append(gift)
    paid_users.pop(user_id, None)

    return {
        "gift_id": gift['telegram_id'],
        "emoji": gift['emoji'],
        "image_url": gift['image_path']
    }