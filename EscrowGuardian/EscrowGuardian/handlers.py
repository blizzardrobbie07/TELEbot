from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler
from models import Transaction, Review, Report, TransactionStatus
from storage import storage
from datetime import datetime
from crypto_mock import CryptoMock
from config import SUPPORTED_CURRENCIES, ESCROW_WALLETS
import logging
import os
import aiofiles
import uuid
import mimetypes

# Set up logger
logger = logging.getLogger(__name__)

# ======================== CORE FUNCTIONALITY ========================

async def start(update: Update, context: CallbackContext):
    """Send welcome message with animation."""
    try:
        logger.info("Start command received from user %s", update.effective_user.id)
        await send_welcome_message(update.effective_chat.id, context)
    except Exception as e:
        logger.error("Error in start command: %s", str(e), exc_info=True)
        if update.message:
            await update.message.reply_text("⚠️ Failed to load welcome message. Please try again.")

async def send_welcome_message(chat_id: int, context: CallbackContext):
    """Helper function to send welcome message."""
    try:
        welcome_message = (
            "👋 Welcome to GengarEscrow Bot! 👻💼\n\n"
            "Secure BTC/LTC escrow service with:\n"
            "• Instant transaction setup\n"
            "• Multi-signature wallets\n"
            "• Automated dispute resolution\n\n"
            "📌 Get started with /transaction"
        )

        keyboard = [
            [InlineKeyboardButton("📚 How It Works", callback_data='show_escrow_info'),
             InlineKeyboardButton("💼 Start Transaction", callback_data='start_transaction')],
            [InlineKeyboardButton("📝 Terms of Service", callback_data='show_terms')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        gif_path = os.path.join('attached_assets', 'gengar.gif.mp4')
        if os.path.exists(gif_path):
            async with aiofiles.open(gif_path, 'rb') as gif:
                await context.bot.send_animation(
                    chat_id=chat_id,
                    animation=InputFile(await gif.read()),
                    caption=welcome_message,
                    reply_markup=reply_markup
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_message,
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error("Error in send_welcome_message: %s", str(e))
        await context.bot.send_message(
            chat_id=chat_id,
            text="Welcome to Gengar Escrow Service!"
        )

# ======================== TRANSACTION FLOW ========================

async def transaction(update: Update, context: CallbackContext):
    """Initiate or view transaction"""
    if await group_required(update):
        return

    user_id = update.effective_user.id
    existing = storage.get_user_transaction(user_id)

    if existing:
        status_message = (
            f"📦 Active Transaction:\n"
            f"ID: {existing.id}\n"
            f"Currency: {existing.currency}\n"
            f"Status: {existing.status.value.capitalize()}\n"
            f"Created: {existing.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        await update.message.reply_text(status_message)
        return

# Directly trigger button-based selection
await select_currency(update, context)

async def select_currency(update: Update, context: CallbackContext):
    """Handle currency selection via buttons"""
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data='currency_btc'),
         InlineKeyboardButton("LTC", callback_data='currency_ltc')]
    ]
   async def select_currency(update: Update, context: CallbackContext):
    """Handle currency selection via buttons"""
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data='currency_btc'),  # Fixed callback_data
         InlineKeyboardButton("LTC", callback_data='currency_ltc')]
    ]
    await update.message.reply_text(
        "Select cryptocurrency:",
        reply_markup=InlineKeyboardMarkup(keyboard)  # Added closing )
    )

async def set_buyer(update: Update, context: CallbackContext):
    """Set buyer address"""
    if not context.args:
        await update.message.reply_text("Usage: /set_buyer [address]")
        return

    address = context.args[0]
    user_id = update.effective_user.id
    transaction = storage.get_user_transaction(user_id)

    if not transaction:
        await update.message.reply_text("❌ No active transaction. Start with /transaction")
        return

    if transaction.buyer_address:
        await update.message.reply_text("⚠️ Buyer address already set. Use /restart to reset.")
        return

    if not CryptoMock.verify_address(transaction.currency, address):
        await update.message.reply_text("❌ Invalid address format for selected currency")
        return

    transaction.buyer_address = address
    transaction.status = TransactionStatus.BUYER_SET
    await update.message.reply_text(f"✅ Buyer address set:\n`{address}`", parse_mode=ParseMode.MARKDOWN)

async def set_seller(update: Update, context: CallbackContext):
    """Set seller address"""
    if not context.args:
        await update.message.reply_text("Usage: /set_seller [address]")
        return

    address = context.args[0]
    user_id = update.effective_user.id
    transaction = storage.get_user_transaction(user_id)

    if not transaction:
        await update.message.reply_text("❌ No active transaction. Start with /transaction")
        return

    if transaction.seller_address:
        await update.message.reply_text("⚠️ Seller address already set. Use /restart to reset.")
        return

    if not CryptoMock.verify_address(transaction.currency, address):
        await update.message.reply_text("❌ Invalid address format for selected currency")
        return

    transaction.seller_address = address
    transaction.status = TransactionStatus.SELLER_SET
    await update.message.reply_text(f"✅ Seller address set:\n`{address}`", parse_mode=ParseMode.MARKDOWN)

# ======================== TRANSACTION ACTIONS ========================

async def refund_buyer(update: Update, context: CallbackContext):
    """Process refund to buyer"""
    user_id = update.effective_user.id
    transaction = storage.get_user_transaction(user_id)

    if not transaction:
        await update.message.reply_text("❌ No active transaction")
        return

    if transaction.status != TransactionStatus.FUNDED:
        await update.message.reply_text("⚠️ Funds not verified for refund")
        return

    transaction.status = TransactionStatus.REFUNDED
    await update.message.reply_text(
        f"💸 Refund Initiated!\n\n"
        f"Amount: {transaction.amount} {transaction.currency}\n"
        f"To: `{transaction.buyer_address}`\n"
        f"TX ID: `{uuid.uuid4()}`",
        parse_mode=ParseMode.MARKDOWN
    )

async def pay_seller(update: Update, context: CallbackContext):
    """Complete payment to seller"""
    user_id = update.effective_user.id
    transaction = storage.get_user_transaction(user_id)

    if not transaction:
        await update.message.reply_text("❌ No active transaction")
        return

    if transaction.status != TransactionStatus.FUNDED:
        await update.message.reply_text("⚠️ Funds not verified for payment")
        return

    transaction.status = TransactionStatus.COMPLETED
    await update.message.reply_text(
        f"💸 Payment Released!\n\n"
        f"Amount: {transaction.amount} {transaction.currency}\n"
        f"To: `{transaction.seller_address}`\n"
        f"TX ID: `{uuid.uuid4()}`",
        parse_mode=ParseMode.MARKDOWN
    )

# ======================== REVIEW SYSTEM ========================

async def review(update: Update, context: CallbackContext):
    """Handle review submissions"""
    if not context.args:
        await update.message.reply_text("Usage: /review [your feedback]")
        return

    user_id = update.effective_user.id
    transaction = storage.get_user_transaction(user_id)
    
    if not transaction or transaction.status != TransactionStatus.COMPLETED:
        await update.message.reply_text("❌ You can only review completed transactions")
        return

    review_text = ' '.join(context.args)
    new_review = Review(
        transaction_id=transaction.id,
        user_id=user_id,
        message=review_text,
        created_at=datetime.now()
    )
    storage.add_review(new_review)
    
    await update.message.reply_text(
        "⭐ Thank you for your review!\n\n"
        f"Your feedback: _{review_text}_",
        parse_mode=ParseMode.MARKDOWN
    )

# ======================== VERIFICATION & SECURITY ========================

async def verify(update: Update, context: CallbackContext):
    """Verify escrow address"""
    if not context.args:
        await update.message.reply_text("Usage: /verify [address]")
        return

    address = context.args[0]
    is_valid = any(address == addr for addr in ESCROW_WALLETS.values())

    response = ("✅ Verified Gengar Escrow Address" if is_valid 
                else "❌ Potential Fraudulent Address!")

    await update.message.reply_text(
        f"{response}\n\n"
        f"Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Address: `{address}`",
        parse_mode=ParseMode.MARKDOWN
    )

async def real(update: Update, context: CallbackContext):
    """Verify bot authenticity"""
    verification_msg = (
        "🔒 **Official Gengar Escrow Bot** 🔒\n\n"
        "Authentication Marks:\n"
        "• Verified Telegram Checkmark\n"
        "• Consistent Branding\n"
        "• Secure HTTPS Connections\n\n"
        "⚠️ Report imposters with /report"
    )
    await update.message.reply_text(verification_msg, parse_mode=ParseMode.MARKDOWN)

async def check(update: Update, context: CallbackContext):
    """Check admin privileges"""
    try:
        chat_id = update.effective_chat.id
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)

        if bot_member.status in ['administrator', 'creator']:
            response = "✅ Has Admin Privileges\nFull functionality enabled"
        else:
            response = ("⚠️ Limited Functionality\n"
                       "Required Permissions:\n"
                       "- Delete Messages\n"
                       "- Pin Messages\n"
                       "- Ban Users")

        await update.message.reply_text(
            f"🛡️ Bot Permission Status:\n\n{response}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error("Admin check failed: %s", e)
        await update.message.reply_text("❌ Could not verify permissions")

# ======================== OTHER HANDLERS ========================

async def status(update: Update, context: CallbackContext):
    """Show transaction status"""
    user_id = update.effective_user.id
    transaction = storage.get_user_transaction(user_id)

    if not transaction:
        await update.message.reply_text("❌ No active transaction")
        return

    deposit_address = ESCROW_WALLETS[transaction.currency]
    status_message = (
        f"📊 Transaction Status\n\n"
        f"🔖 ID: `{transaction.id}`\n"
        f"🕒 Created: {transaction.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"💰 Currency: {transaction.currency}\n"
        f"📥 Escrow Address:\n`{deposit_address}`\n"
        f"📈 Status: {transaction.status.value.capitalize()}\n"
        f"👤 Buyer: {transaction.buyer_address or 'Not set'}\n"
        f"👥 Seller: {transaction.seller_address or 'Not set'}"
    )
    await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)

async def how(update: Update, context: CallbackContext):
    """Show usage guide"""
    guide = (
        "📘 **Gengar Escrow Guide**\n\n"
        "1. Start: /transaction\n"
        "2. Set currency: /select_currency\n"
        "3. Configure addresses:\n"
        "   - /set_buyer [address]\n"
        "   - /set_seller [address]\n"
        "4. Fund escrow wallet\n"
        "5. Complete transaction:\n"
        "   - /pay_seller to release funds\n"
        "   - /refund_buyer to cancel\n\n"
        "🔍 Check /status anytime\n"
        "🔄 Reset with /restart"
    )
    await update.message.reply_text(guide, parse_mode=ParseMode.MARKDOWN)

async def restart(update: Update, context: CallbackContext):
    """Reset transaction"""
    user_id = update.effective_user.id
    storage.reset_transaction(user_id)
    await update.message.reply_text("♻️ Transaction reset. Start new with /transaction")

async def contact(update: Update, context: CallbackContext):
    """Contact support"""
    message = ' '.join(context.args) if context.args else "No message provided"
    logger.info(f"Contact message from {update.effective_user.id}: {message}")
    await update.message.reply_text("📩 Message received. Support will respond within 24h.")

async def report(update: Update, context: CallbackContext):
    """Report issue"""
    if not context.args:
        await update.message.reply_text("Usage: /report [description]")
        return

    report = Report(
        user_id=update.effective_user.id,
        message=' '.join(context.args),
        created_at=datetime.now()
    )
    storage.add_report(report)
    await update.message.reply_text("🚨 Report filed. Thank you for your vigilance!")

# ======================== HELPER FUNCTIONS ========================

def is_group_chat(update: Update) -> bool:
    return update.effective_chat.type in ['group', 'supergroup']

async def group_required(update: Update) -> bool:
    if not is_group_chat(update):
        await update.message.reply_text(
            "⚠️ Group Chat Required\n\n"
            "This bot functions best in group chats where:\n"
            "- Multiple participants can verify transactions\n"
            "- Transparent communication is maintained\n"
            "- Disputes can be publicly resolved\n\n"
            "Create a group and add me as admin!"
        )
        return True
    return False

# ======================== CALLBACK HANDLERS ========================

async def button_callback(update: Update, context: CallbackContext):
    """Handle all inline button interactions"""
    query = update.callback_query
    await query.answer()
    
    try:
      if query.data.startswith('currency_'):
    currency = query.data.split('_')[1].upper()
    user_id = query.from_user.id
    transaction = storage.create_transaction(user_id, currency)
    deposit_address = ESCROW_WALLETS[currency]
    
    await query.message.reply_text(
        f"✅ Transaction Created!\n\n"
        f"🔐 ID: `{transaction.id}`\n"
        f"💰 Currency: {currency}\n"
        f"📥 Deposit Address:\n`{deposit_address}`\n\n"
        "Next Steps:\n"
        "1. /set_buyer [crypto_address]\n"
        "2. /set_seller [crypto_address]\n"
        "3. Send funds to escrow address",
        parse_mode=ParseMode.MARKDOWN
    )
elif query.data == 'show_escrow_info':
    escrow_info = (
        "🛡️ How Escrow Works:\n\n"
        "1. Buyer/seller agree to terms\n"
        "2. Funds are locked in escrow\n"
        "3. Goods/services are exchanged\n"
        "4. Funds released to seller\n\n"
        "Full guide: /how"
    )
    await query.edit_message_text(escrow_info)
elif query.data == 'show_terms':
    context.user_data['original_message'] = query.message
    await terms(update, context)
    if query.message:
        await query.message.delete()
elif query.data == 'start_transaction':
    context.user_data['original_message'] = query.message
    await transaction(update, context)
    if query.message:
        await query.message.delete()

# ======================== SYSTEM COMMANDS ========================

async def terms(update: Update, context: CallbackContext):
    """Show terms of service"""
    terms_text = (
        "📜 Terms of Service\n\n"
        "1. Funds held in escrow until mutual agreement\n"
        "2. 0.5% service fee on completed transactions\n"
        "3. Users must verify counterparty identities\n"
        "4. Disputes resolved via multisig arbitration\n"
        "5. Full logs available upon request\n\n"
        "By using this service, you agree to these terms."
    )
    await update.message.reply_text(terms_text)

async def balance(update: Update, context: CallbackContext):
    """Check balances (stub implementation)"""
    await update.message.reply_text(
        "💰 Balance Summary:\n"
        "BTC: 0.00000000\n"
        "LTC: 0.00000000\n\n"
        "Fund escrow wallet to start transactions!"
    )
