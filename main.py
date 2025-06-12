from typing import AsyncGenerator

from aiogram import Bot, Dispatcher, F
from aiogram.client import bot
from aiogram.methods import CreateInvoiceLink
from aiogram.types import Message, Update, WebAppInfo, LabeledPrice, PreCheckoutQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from starlette.middleware.cors import CORSMiddleware

from config_reader import config

async def lifespan(app: FastAPI) -> AsyncGenerator:
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    yield
    # Shutdown logic
    await bot.session.close()


bot = Bot(config.BOT_TOKEN.get_secret_value())

dp = Dispatcher()

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

markup = (
    InlineKeyboardBuilder()
    .button(text="Open app", web_app=WebAppInfo(url=config.WEBAPP_URL))
).as_markup()

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Hello!", reply_markup=markup)

@dp.pre_checkout_query()
async def precheck(event: PreCheckoutQuery) -> None:
    await event.answer(True)

@dp.message(F.succesful_payment)
async def succesful_payment(message: Message) -> None:
    await message.answer("Ваши звезды зачислены на ваш баланс")

@app.post(config.WEBHOOK_PATH)
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={'bot': bot})
    await dp.feed_update(bot, update)

@app.post("/api/donate", response_class=JSONResponse)
async def donate(request: Request) -> JSONResponse:
    data = await request.json()
    invoice_link = await bot(
        CreateInvoiceLink(
            title="Пополнение баланса",
            description="",
            payload="Оплата",
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=data["amount"])]
        )

    )

    return JSONResponse({"invoice_link": invoice_link})



if __name__ == "__main__":
    uvicorn.run(app, host=config.APP_HOST, port=config.APP_PORT)
