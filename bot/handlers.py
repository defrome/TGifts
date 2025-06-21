from aiogram import types
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart, Command, SuccessfulPayment
from aiogram.methods import RefundStarPayment
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, PreCheckoutQuery, Message
from bot.bot import bot, dp, router
from shared import paid_users
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

@router.pre_checkout_query(lambda q: True)
async def on_pre_checkout(pre_checkout_q: PreCheckoutQuery):
    logger.info(f"pre_checkout_query от user_id={pre_checkout_q.from_user.id}")
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

# проверяем оплату в боtе
@dp.message(Command('paid'))
async def get_paid_bot(message: types.Message):
    paid = paid_users
    await message.reply(paid)

@router.message(SuccessfulPayment())
async def on_message(msg: types.Message):
    if msg.successful_payment:
        user_id = msg.from_user.id
        charge_id = msg.successful_payment.telegram_payment_charge_id
        paid_users[user_id] = charge_id
        logger.info(f"✅ Успешный платеж от user_id={user_id}, charge_id={charge_id}")
        await msg.reply("Спасибо за ваш платеж! Ваша покупка завершена.")

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
