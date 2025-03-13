import logging
import os
import aiofiles
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from config import TELEGRAM_TOKEN
from handlers import (
    start, transaction, select_currency, set_buyer, set_seller,
    status, balance, verify, review, report, restart, terms,
    button_callback, refund_buyer, pay_seller, contact, real, check, how
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define bot commands for menu
BOT_COMMANDS = [
    ("start", "Start the bot and receive a welcome menu"),
    ("transaction", "Initiate or view transaction"),
    ("set_buyer", "Set buyer's wallet address"),
    ("set_seller", "Set seller's wallet address"),
    ("status", "View transaction status"),
    ("balance", "Check balance"),
    ("refund_buyer", "Process buyer refund"),
    ("pay_seller", "Complete seller payment"),
    ("review", "Leave transaction review"),
    ("restart", "Reset transaction"),
    ("verify", "Verify escrow address"),
    ("report", "Report issues"),
    ("contact", "Contact support"),
    ("real", "Verify bot authenticity"),
    ("check", "Check admin privileges"),
    ("terms", "View terms of service"),
    ("how", "Usage guide")
]

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and notify user"""
    logger.error("Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("⚠️ Service temporarily unavailable. Please try again later.")

async def set_bot_profile_photo(application: Application):
    """Set bot's profile photo using async file handling"""
    try:
        photo_path = os.path.abspath(os.path.join('attached_assets', 'gengar_pfp.jpg'))
        if os.path.exists(photo_path):
            async with aiofiles.open(photo_path, 'rb') as photo_file:
                photo_data = await photo_file.read()
                await application.bot.set_my_photo(photo=photo_data)
                logger.info("Successfully updated bot profile photo")
        else:
            logger.error("Profile photo file not found at: %s", photo_path)
    except Exception as e:
        logger.error("Failed to set profile photo: %s", str(e))

async def set_bot_name(application: Application):
    """Set bot's display name with flood control handling"""
    max_retries = 3
    base_delay = 10
    
    for attempt in range(1, max_retries+1):
        try:
            await application.bot.set_my_name("Gengar Escrow Bot")
            logger.info("Successfully updated bot name")
            return
        except Exception as e:
            if "retry after" in str(e):
                wait_time = int(str(e).split()[-1])
                logger.warning("Flood control: Waiting %d seconds (attempt %d)", wait_time, attempt)
                await asyncio.sleep(wait_time + 5)
            else:
                logger.warning("Name set attempt %d failed: %s", attempt, str(e))
                await asyncio.sleep(base_delay * (2 ** attempt))
    logger.error("Permanent failure setting bot name")

async def post_init(application: Application):
    """Async initialization tasks"""
    try:
        # Set commands first for immediate usability
        await application.bot.set_my_commands(BOT_COMMANDS)
        
        # Profile customization (optional)
        await set_bot_profile_photo(application)
        # await set_bot_name(application)  # Temporarily disabled due to flood control
        
        logger.info("Bot initialization completed")
    except Exception as e:
        logger.error("Post-init failed: %s", str(e))
        raise

def setup_handlers(application: Application):
    """Configure all async handlers"""
    handlers = [
        CommandHandler("start", start),
        CommandHandler("transaction", transaction),
        CommandHandler("select_currency", select_currency),
        CommandHandler("set_buyer", set_buyer),
        CommandHandler("set_seller", set_seller),
        CommandHandler("status", status),
        CommandHandler("balance", balance),
        CommandHandler("verify", verify),
        CommandHandler("review", review),
        CommandHandler("report", report),
        CommandHandler("restart", restart),
        CommandHandler("terms", terms),
        CommandHandler("contact", contact),
        CommandHandler("refund_buyer", refund_buyer),
        CommandHandler("pay_seller", pay_seller),
        CommandHandler("real", real),
        CommandHandler("check", check),
        CommandHandler("how", how),
        CallbackQueryHandler(button_callback)
    ]

    for handler in handlers:
        application.add_handler(handler)

    application.add_error_handler(error_handler)

def main():
    """Start the async application"""
    application = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .post_init(post_init) \
        .build()

    setup_handlers(application)
    
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()