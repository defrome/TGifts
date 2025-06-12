from typing import AsyncGenerator
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update, WebAppInfo, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from config_reader import config

# Инициализация бота и диспетчера
bot = Bot(config.BOT_TOKEN.get_secret_value())
dp = Dispatcher()

# Создаем FastAPI приложение
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Клавиатура с WebApp кнопкой
markup = (
    InlineKeyboardBuilder()
    .button(text="Open app", web_app=WebAppInfo(url=config.WEBAPP_URL))
).as_markup()


# Обработчики для бота
@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Hello!", reply_markup=markup)


@dp.pre_checkout_query()
async def precheck(event: PreCheckoutQuery) -> None:
    await event.answer(True)


@dp.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    await message.answer("Ваши звезды зачислены на ваш баланс")


# Обработчики для FastAPI
@app.post(config.WEBHOOK_PATH)
async def bot_webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={'bot': bot})
    await dp.feed_update(bot, update)


@app.post("/api/donate")
async def donate(request: Request) -> JSONResponse:
    data = await request.json()
    invoice_link = await bot.create_invoice_link(
        title="Пополнение баланса",
        description="Пополнение игрового баланса",
        payload="Оплата",
        provider_token=config.PAYMENT_TOKEN.get_secret_value(),
        currency="RUB",
        prices=[LabeledPrice(label="Игровая валюта", amount=data["amount"] * 100)]  # amount в копейках
    )
    return JSONResponse({"invoice_link": invoice_link})


async def run_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        await bot.session.close()


def run_fastapi():
    uvicorn.run(
        app,
        host=config.APP_HOST,
        port=config.APP_PORT,
        log_level="info"
    )


async def main():
    # Создаем и запускаем задачи
    bot_task = asyncio.create_task(run_bot())
    fastapi_task = asyncio.get_event_loop().run_in_executor(None, run_fastapi)

    try:
        # Ожидаем завершения одной из задач
        done, pending = await asyncio.wait(
            [bot_task, fastapi_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Отменяем оставшиеся задачи
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except KeyboardInterrupt:
        # Обработка Ctrl+C
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Приложение остановлено")