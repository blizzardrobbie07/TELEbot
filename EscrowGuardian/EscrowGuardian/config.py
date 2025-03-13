import os
import logging

# ========================
# LOGGING CONFIGURATION
# ========================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,  # Changed to INFO for production
    handlers=[
        logging.FileHandler("escrow_bot.log"),
        logging.StreamHandler()
    ]
)

# ========================
# CORE BOT CONFIGURATION
# ========================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7368183600:AAGU8yjK-ZDqip5dbjUiuG6YkQ-NeFGA4A8')
ADMIN_USER_IDS = [1281938416,6230591454]  # Add your admin user IDs here

# ========================
# CRYPTO CONFIGURATION
# ========================
SUPPORTED_CURRENCIES = ['BTC', 'LTC']
ESCROW_WALLETS = {
    'BTC': 'bc1qvcf5t3282g4ssxygcstxmk4s4tepdns8hmgpv4',
    'LTC': 'ltc1qwl8qe05cyr6phmn484nnc6rw7af335fh0q4kv7'
}

TRANSACTION_FEES = {
    'BTC': 0.00015,  # ~$5 at current prices
    'LTC': 0.001      # ~$0.10 at current prices
}

# ========================
# TRANSACTION SETTINGS
# ========================
ESCROW_TIMEOUT_HOURS = 72  # Time until automatic refund
MINIMUM_CONFIRMATIONS = 3   # Required blockchain confirmations

# ========================
# SAFETY FEATURES
# ========================
MAX_TRANSACTION_AMOUNT = {
    'BTC': 0.5,   # ~$15,000
    'LTC': 100     # ~$5,000
}

# ========================
# USER INTERFACE SETTINGS
# ========================
DEFAULT_LANGUAGE = 'en'
SUPPORT_CHAT_ID = '@GengarEscrowSupport'