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