import os
from aiogram import Bot, Dispatcher, Router
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
router = Router()
dp.include_router(router)