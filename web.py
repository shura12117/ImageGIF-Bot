from flask import Flask
import threading
import os
import sys
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот работает!"

@app.route('/health')
def health():
    return {"status": "ok", "uptime": time.time()}

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()

if __name__ == "__main__":
    keep_alive()
    
    print("🚀 Запуск бота...")
    import bot
    bot.client.run(bot.config.BOT_TOKEN)
