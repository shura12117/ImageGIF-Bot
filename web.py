"""
Web сервер + запуск бота для Render
"""

from flask import Flask, jsonify
import threading
import time
import os
import sys

app = Flask(__name__)

# Глобальная переменная для отслеживания статуса бота
bot_status = {
    'running': False,
    'started_at': None,
    'message': 'Bot not started'
}

@app.route('/')
def home():
    return f"""
    <html>
    <head>
        <title>Image GIF Bot</title>
        <style>
            body {{ 
                background: linear-gradient(135deg, #0f0f13 0%, #1a237e 100%);
                color: white; 
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }}
            .container {{ text-align: center; }}
            h1 {{ font-size: 3em; margin-bottom: 0.5em; }}
            .stats {{ font-size: 1.5em; color: #64b5f6; }}
            .status {{ margin-top: 20px; padding: 10px; border-radius: 8px; }}
            .running {{ background: #43b581; }}
            .stopped {{ background: #f04747; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Image GIF Bot работает!</h1>
            <div class="stats">
                <p>🌐 Веб-сервер активен</p>
                <p>🤖 Статус бота: {'Онлайн' if bot_status['running'] else 'Офлайн'}</p>
            </div>
            <div class="status {'running' if bot_status['running'] else 'stopped'}">
                {bot_status['message']}
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok' if bot_status['running'] else 'bot_not_running',
        'uptime': time.time(),
        'bot_running': bot_status['running']
    })

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'bot_running': bot_status['running'],
        'message': bot_status['message']
    })

def run_bot():
    """Запускает бота в отдельном потоке"""
    try:
        print("=" * 70)
        print("🤖 ЗАПУСК БОТА...")
        print("=" * 70)
        
        bot_status['started_at'] = time.time()
        bot_status['running'] = True
        bot_status['message'] = 'Starting bot...'
        
        # Импортируем и запускаем бота
        import bot as bot_module
        
        # Запускаем бота в отдельном потоке чтобы не блокировать Flask
        bot_thread = threading.Thread(
            target=bot_module.client.run,
            args=(bot_module.config.BOT_TOKEN,),
            daemon=True
        )
        bot_thread.start()
        
        bot_status['message'] = 'Bot is running!'
        print("✅ Бот запущен в фоновом режиме!")
        
    except Exception as e:
        bot_status['running'] = False
        bot_status['message'] = f'Error: {str(e)}'
        print(f"❌ ОШИБКА ЗАПУСКА БОТА: {e}")
        import traceback
        traceback.print_exc()

def run_web():
    """Запускает Flask веб-сервер"""
    print(" Запуск веб-сервера...")
    app.run(host='0.0.0.0', port=8080, debug=False)

def keep_alive():
    """Запускает веб-сервер и бота"""
    print("=" * 70)
    print("🚀 IMAGE GIF BOT - ЗАПУСК СИСТЕМЫ")
    print("=" * 70)
    
    # Запускаем веб-сервер
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Ждём немного чтобы веб-сервер запустился
    time.sleep(2)
    
    # Запускаем бота
    run_bot()
    
    # Основной поток просто спит
    print("✅ Система запущена!")
    print("=" * 70)
    
    while True:
        time.sleep(3600)  # Спим час

if __name__ == "__main__":
    keep_alive()
