import os
import httpx
from io import BytesIO
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
import asyncio
from bot.utils import format_response

load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("NUTRISCAN_API_URL", "http://127.0.0.1:8000/analyze/")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer("Привіт! Надішли фото страви 🍽")

@dp.message(F.photo)
async def handle_photo(msg: Message):
    photo = msg.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)

    # Конвертуємо в байти для відправки як файл
    image_data = file_bytes.read()
    image_stream = BytesIO(image_data)

    # multipart/form-data
    files = {
        "image": ("image.jpg", image_stream, "image/jpeg")
    }

    timeout = httpx.Timeout(60.0)  # або 120.0 сек при потребі
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(API_URL, files=files)


    print("Response status:", resp.status_code)
    print("Response text:", resp.text)

    if resp.status_code != 200:
        await msg.answer("⚠️ Не вдалося обробити зображення.")
        return

    result = resp.json()
    print("📦 RAW API result:", result)

    if isinstance(result, dict) and "data" in result and "ingredients" in result["data"]:
        reply = format_response(result)
    else:
        reply = "⚠️ Не вдалося визначити інгредієнти."

    await msg.answer(reply, parse_mode=ParseMode.MARKDOWN)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
