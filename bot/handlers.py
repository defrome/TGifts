from aiogram import types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, PreCheckoutQuery, Message
from bot.bot import bot, dp, router
from shared import paid_users
import os
import logging

logger = logging.getLogger(__name__)

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Играть", web_app=WebAppInfo(url=os.getenv("WEB_URL")))
    await message.answer(f"Привет, {message.from_user.full_name}!", reply_markup=builder.as_markup())

@router.pre_checkout_query(lambda q: True)
async def on_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@router.message()
async def on_message(msg: types.Message):
    if msg.successful_payment:
        paid_users[msg.from_user.id] = msg.successful_payment.telegram_payment_charge_id
        await msg.reply("Спасибо за платеж!")

@dp.message(Command("status"))
async def check_payment_status(message: types.Message):
    await message.reply("Вы оплатили." if message.from_user.id in paid_users else "Вы еще не оплатили.")

@dp.message(Command("refund"))
async def process_refund(message: Message):
    await message.answer("Возврат выполнен")