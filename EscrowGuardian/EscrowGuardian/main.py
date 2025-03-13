import uuid
from flask import Flask, jsonify
import threading
import asyncio
import bot

app = Flask(__name__)

@app.route('/')
def index():
    return "Gengar Escrow Bot is running"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

def run_bot():
    """Run the Telegram bot with proper async event loop setup"""
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Run the bot main function
    bot.main()

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start the Flask server
    print("Starting Flask server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, use_reloader=False)