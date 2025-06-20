from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.methods import RefundStarPayment
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, PreCheckoutQuery, Message
from bot.bot import bot, dp, router
import os
import logging

logger = logging.getLogger(__name__)

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