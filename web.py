from flask import Flask
import threading
import bot  # Импортируем твой основной файл с ботом

app = Flask('keep-alive')

@app.route('/')
def home():
    return "✅ Image GIF Bot работает!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

if __name__ == "__main__":
    keep_alive()
    # Запускаем бота из файла bot.py
    bot.client.run(bot.config.BOT_TOKEN)