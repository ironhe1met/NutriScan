import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from io import BytesIO
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

logger = logging.getLogger("nutriscan.bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ALLOWED_USERS = [int(x) for x in os.getenv("BOT_ALLOWED_USERS", "").split(",") if x.strip()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Per-user provider/model preference
user_prefs: dict[int, dict] = {}

PROVIDERS = {
    "anthropic": {"label": "Claude", "models": ["sonnet", "opus", "haiku"]},
    "openai": {"label": "GPT", "models": ["gpt4o", "gpt4o-mini"]},
    "google": {"label": "Gemini", "models": ["flash", "flash-lite", "pro"]},
}


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True  # no whitelist = everyone allowed
    return user_id in ALLOWED_USERS


def get_prefs(user_id: int) -> dict:
    return user_prefs.get(user_id, {"provider": "anthropic", "model": "sonnet"})


@dp.message(CommandStart())
async def cmd_start(msg: Message):
    if not is_allowed(msg.from_user.id):
        await msg.answer("Access denied. Contact admin.")
        return
    prefs = get_prefs(msg.from_user.id)
    await msg.answer(
        f"Hi! Send a food photo and I'll analyze its nutrients.\n\n"
        f"Current: *{prefs['provider']}* / *{prefs['model']}*\n"
        f"/settings — change provider/model",
        parse_mode=ParseMode.MARKDOWN,
    )


@dp.message(Command("settings"))
async def cmd_settings(msg: Message):
    if not is_allowed(msg.from_user.id):
        return
    builder = InlineKeyboardBuilder()
    for key, info in PROVIDERS.items():
        builder.button(text=info["label"], callback_data=f"prov:{key}")
    builder.adjust(3)
    await msg.answer("Choose AI provider:", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("prov:"))
async def pick_provider(cb: CallbackQuery):
    provider = cb.data.split(":")[1]
    user_prefs.setdefault(cb.from_user.id, {"provider": "anthropic", "model": "sonnet"})
    user_prefs[cb.from_user.id]["provider"] = provider

    builder = InlineKeyboardBuilder()
    for m in PROVIDERS[provider]["models"]:
        builder.button(text=m, callback_data=f"model:{m}")
    builder.adjust(3)
    await cb.message.edit_text(f"Provider: *{provider}*\nChoose model:", parse_mode=ParseMode.MARKDOWN, reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("model:"))
async def pick_model(cb: CallbackQuery):
    model = cb.data.split(":")[1]
    user_prefs.setdefault(cb.from_user.id, {"provider": "anthropic", "model": "sonnet"})
    user_prefs[cb.from_user.id]["model"] = model
    prefs = user_prefs[cb.from_user.id]
    await cb.message.edit_text(
        f"Set: *{prefs['provider']}* / *{prefs['model']}*\n\nNow send a food photo!",
        parse_mode=ParseMode.MARKDOWN,
    )


@dp.message(F.photo)
async def handle_photo(msg: Message):
    if not is_allowed(msg.from_user.id):
        await msg.answer("Access denied.")
        return

    prefs = get_prefs(msg.from_user.id)
    wait_msg = await msg.answer(f"Analyzing with *{prefs['provider']}* / *{prefs['model']}*...", parse_mode=ParseMode.MARKDOWN)

    photo = msg.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    image_data = file_bytes.read()

    files = {"image": ("image.jpg", BytesIO(image_data), "image/jpeg")}
    url = f"{API_URL}/analyze/?provider={prefs['provider']}&model={prefs['model']}"

    try:
        timeout = httpx.Timeout(120.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, files=files)

        if resp.status_code != 200:
            await wait_msg.edit_text("Failed to analyze image.")
            return

        result = resp.json()
        data = result.get("data", {})

        if not data or "ingredients" not in data:
            await wait_msg.edit_text("Could not identify ingredients.")
            return

        reply = format_response(data, prefs)
        await wait_msg.edit_text(reply, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error("Bot error: %s", e)
        await wait_msg.edit_text(f"Error: {e}")


def format_response(data: dict, prefs: dict) -> str:
    lines = [f"*{data.get('dish_name', 'Unknown')}*"]
    lines.append("")

    for ing in data.get("ingredients", []):
        allergens = ""
        if ing.get("allergens"):
            allergens = f" ⚠️ {', '.join(ing['allergens'])}"
        lines.append(f"• {ing['name']} — {ing.get('weight_g', '?')}g ({ing.get('calories_kcal', '?')} kcal){allergens}")

    total = data.get("total", {})
    macro = total.get("macronutrients", {})
    lines.append("")
    lines.append(
        f"*Total:* {total.get('calories_kcal', 0)} kcal\n"
        f"P: {macro.get('protein_g', 0)}g | "
        f"F: {macro.get('fat_g', 0)}g | "
        f"C: {macro.get('carbs_g', 0)}g"
    )

    if total.get("allergens"):
        lines.append(f"\n⚠️ *Allergens:* {', '.join(total['allergens'])}")

    lines.append(f"\n_{prefs['provider']} / {prefs['model']}_")
    return "\n".join(lines)


async def main():
    logger.info("NutriScan bot starting (allowed users: %s)", ALLOWED_USERS or "all")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
