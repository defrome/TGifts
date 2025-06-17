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

from app.main import paid_users, logger

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

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
