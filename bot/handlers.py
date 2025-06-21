from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, Command
from aiogram.methods import RefundStarPayment
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, PreCheckoutQuery, Message
from bot.bot import bot, dp, router
from shared import paid_users  # Теперь это JSONStorage
import os
import logging

logger = logging.getLogger(__name__)

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Играть",
        web_app=WebAppInfo(url=os.getenv("WEB_URL"))
    )
    await message.answer(
        f"Привет, {message.from_user.full_name}! Ждем тебя в нашем боте!",
        reply_markup=builder.as_markup()
    )

@router.pre_checkout_query()
async def on_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@router.message()
async def on_message(msg: types.Message):
    if msg.successful_payment:
        user_id = msg.from_user.id
        charge_id = msg.successful_payment.telegram_payment_charge_id
        paid_users[user_id] = charge_id  # Автоматически сохраняется в JSON
        await msg.reply("✅ Платеж успешно обработан!")

@dp.message(Command("status"))
async def check_payment_status(message: types.Message):
    if message.from_user.id in paid_users:
        await message.reply("✔️ Вы оплатили")
    else:
        await message.reply("❌ Вы еще не оплатили")

@dp.message(Command("refund"))
async def process_refund(message: Message):
    try:
        transaction_id = message.text.split()[1]
        await bot(RefundStarPayment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        ))
        await message.answer("💰 Возврат выполнен")
    except (IndexError, TelegramAPIError) as e:
        await message.answer(f"❌ Ошибка: {e}")