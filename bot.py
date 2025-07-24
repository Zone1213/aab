# bot.py

import asyncio
import logging
import hashlib
import hmac
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ── Your real Telegram Bot Token ──
BOT_TOKEN = "7676931713:AAHwFr_5u4BlO8vRlCjjCoyoEGY95EBAoIk"
WEBAPP_URL = "https://yourdomain.com"  # ← replace with your actual WebApp URL
PROJECT_NAME = "FahamAI Airdrop & Wallet"

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /start:
    Sends a welcome message with the project name
    and a persistent 'Open WebApp' button.
    """
    welcome_text = f"👋 Welcome to *{PROJECT_NAME}*!\nClick below to open the WebApp."
    keyboard = [
        [InlineKeyboardButton(text="Open WebApp", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    await update.message.reply_markdown(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def verify_telegram_init_data(init_data: str) -> bool:
    """
    Verifies the authenticity of Telegram WebApp initData using HMAC-SHA256.
    """
    try:
        parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        data_check_string = "\n".join(
            f"{k}={v[0]}" for k, v in sorted(parsed.items()) if k != "hash"
        )
        received_hash = parsed.get("hash", [""])[0]

        secret_key = hmac.new(BOT_TOKEN.encode(), b"WebAppData", hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(calculated_hash, received_hash)
    except Exception as e:
        logger.error("initData verification failed: %s", e)
        return False

def extract_telegram_user(init_data: str) -> dict:
    """
    Extracts Telegram user information from initData.
    """
    parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
    return {
        "id": parsed.get("id", [""])[0],
        "first_name": parsed.get("first_name", [""])[0],
        "last_name": parsed.get("last_name", [""])[0],
        "username": parsed.get("username", [""])[0],
        "photo_url": parsed.get("photo_url", [""])[0],
        "auth_date": parsed.get("auth_date", [""])[0],
    }

def run_bot() -> None:
    """
    Start the Telegram bot with polling inside its own asyncio loop.
    Wrap polling in try/except to catch network errors.
    """
    # Create & set new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    logger.info("Bot starting polling…")
    try:
        app.run_polling()
    except Exception as e:
        logger.error("Bot polling crashed: %s", e)
        # Optionally, you could retry after a delay:
        # import time; time.sleep(10); run_bot()
