import os
import sys
import threading
from flask import Flask

# 1. Создаем Flask приложение для поддержания жизни сервиса на Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Image GIF Bot работает! (Web сервер активен)"

@app.route('/health')
def health():
    return {"status": "ok", "service": "alive"}

# 2. Функция для запуска бота в фоновом потоке
def start_bot():
    try:
        print("=" * 70)
        print("🚀 ЗАПУСК БОТА В ФОНОВОМ РЕЖИМЕ...")
        print("=" * 70)
        
        # Импортируем bot здесь, чтобы избежать проблем с Gunicorn
        import bot
        
        # Берем токен из переменных окружения Render или из config.py
        token = os.environ.get('BOT_TOKEN') or getattr(bot.config, 'BOT_TOKEN', None)
        
        if not token:
            print("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
            return

        print(f"🔑 Токен найден (длина: {len(token)})")
        print("🔗 Подключение к Lolka API...")
        
        # Запускаем бота (это блокирующий вызов, поэтому он в отдельном потоке)
        bot.client.run(token)
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА ЗАПУСКА БОТА: {e}")
        import traceback
        traceback.print_exc()

# 3. Запускаем поток с ботом СРАЗУ при загрузке этого файла Gunicorn'ом
print("🌐 Инициализация фонового потока для бота...")
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()
