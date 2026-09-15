from flask import Flask
import threading
import os
import sys

app = Flask('keep-alive')

@app.route('/')
def home():
    return "✅ Image GIF Bot работает!"

@app.route('/health')
def health():
    return {"status": "ok", "bot": "running"}

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()
    print("🌐 Web сервер запущен на порту 8080")

if __name__ == "__main__":
    keep_alive()
    
    # Теперь запускаем бота
    print("🚀 Запуск бота...")
    
    try:
        import bot
        print("📦 Модуль bot импортирован")
        
        # Проверяем токен
        token = bot.config.BOT_TOKEN
        if not token:
            print("❌ ОШИБКА: BOT_TOKEN не найден!")
            sys.exit(1)
        
        print(f"🔑 Токен найден (длина: {len(token)})")
        print("🔗 Подключение к Lolka...")
        
        # Запускаем бота
        bot.client.run(token)
        
    except Exception as e:
        print(f" КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
