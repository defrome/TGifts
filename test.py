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

from app.main import paid_users
from shared import spin_gifts, referral_users, init_user, referral_gifts, user_inventory, gifts

async def test_roulette_spin(user_id: int):
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