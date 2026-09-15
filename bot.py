"""
Image GIF Bot для Lolka
Использует discord.py с перенаправлением на Lolka API
API: Giphy (GIF) + Unsplash (картинки)
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.http import Route
import yarl
import aiohttp
import config
import logging
import os
import sys
import random

# ===== ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ =====
print("=" * 70)
print(" ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
print(f"  BOT_TOKEN: {'✅ Найден' if config.BOT_TOKEN else '❌ НЕ НАЙДЕН'}")
print(f"  GIPHY_API_KEY: {'✅ Найден' if config.GIPHY_API_KEY else '❌ НЕ НАЙДЕН'}")
print(f"  UNSPLASH_ACCESS_KEY: {'✅ Найден' if config.UNSPLASH_ACCESS_KEY else '❌ НЕ НАЙДЕН'}")
print("=" * 70)

# ===== ПЕРЕНАПРАВЛЕНИЕ НА LOLKA API =====
Route.BASE = "https://lolka.app/api/bot/v10"
discord.gateway.DiscordWebSocket.DEFAULT_GATEWAY = yarl.URL("wss://lolka.app/ws/bot")

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ===== ИНТЕНТЫ =====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# ===== КЛИЕНТ =====
client = commands.Bot(
    command_prefix=commands.when_mentioned_or(config.COMMAND_PREFIX),
    intents=intents,
    help_command=None
)

session = None

# ===== СПИСОК СТАТУСОВ =====
STATUSES = [
    "Играет в Доту | Сайт: imagegif.gt.tc",
    "Играет в Раст | Сайт: imagegif.gt.tc",
    "Играет в КС | Сайт: imagegif.gt.tc",
    "Играет в Майнкрафт | Сайт: imagegif.gt.tc",
    "Играет в GTA | Сайт: imagegif.gt.tc",
]

# ===== ЗАДАЧА СМЕНЫ СТАТУСА =====
@tasks.loop(minutes=2)
async def change_status():
    """Меняет статус бота каждые 2 минуты"""
    status = random.choice(STATUSES)
    await client.change_presence(activity=discord.Game(name=status))
    logger.info(f" Статус изменён: {status}")

@change_status.before_loop
async def before_change_status():
    """Ждём пока бот подключится"""
    await client.wait_until_ready()

# ==================== СОБЫТИЯ ====================

@client.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    
    # Первый статус
    await client.change_presence(
        activity=discord.Game(name="Играет в Доту | Сайт: imagegif.gt.tc")
    )
    
    # Запускаем авто-смену статуса
    if not change_status.is_running():
        change_status.start()
    
    logger.info("=" * 70)
    logger.info(f"✅ Бот подключён: {client.user}")
    logger.info(f"📊 Серверов: {len(client.guilds)}")
    logger.info(f"🎮 Статус: Играет в Доту | Сайт: imagegif.gt.tc")
    logger.info("🔄 Авто-смена статуса каждые 2 минуты запущена")
    logger.info("=" * 70)
    
    try:
        synced = await client.tree.sync()
        logger.info(f"🔄 Синхронизировано команд: {len(synced)}")
    except Exception as e:
        logger.error(f" Ошибка синхронизации: {e}")

# ==================== КОМАНДЫ ====================

@client.tree.command(name="gif", description="🎬 Найти GIF")
@app_commands.describe(query="Что искать?")
async def gif_command(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    if not query or len(query) < 2:
        return await interaction.followup.send("❌ Введите запрос (минимум 2 символа)!", ephemeral=True)
    
    if not config.GIPHY_API_KEY:
        return await interaction.followup.send("❌ Giphy API ключ не настроен!", ephemeral=True)
    
    url = "https://api.giphy.com/v1/gifs/search"
    params = {
        "api_key": config.GIPHY_API_KEY,
        "q": query,
        "limit": 10,
        "rating": "g",
        "lang": "ru"
    }
    
    try:
        async with session.get(url, params=params, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                gifs = data.get("data", [])
                
                if not gifs:
                    return await interaction.followup.send("😕 GIF не найдены!", ephemeral=True)
                
                first = gifs[0]
                gif_url = first.get("images", {}).get("fixed_width", {}).get("url", "")
                title = first.get("title", "GIF")[:256]
                
                embed = discord.Embed(title=title, color=discord.Color.pink())
                embed.set_image(url=gif_url)
                embed.set_footer(text=f"📸 1/{len(gifs)} | Giphy")
                
                view = GIFPaginator(gifs, interaction.user.id, "Giphy")
                msg = await interaction.followup.send(embed=embed, view=view)
                view.message = msg
            else:
                await interaction.followup.send(f"❌ Ошибка Giphy: {resp.status}", ephemeral=True)
    except Exception as e:
        logger.error(f"GIF error: {e}")
        await interaction.followup.send(f"❌ Ошибка: {str(e)}", ephemeral=True)


@client.tree.command(name="image", description="🖼️ Найти картинку (Unsplash)")
@app_commands.describe(query="Что искать?")
async def image_command(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    if not query or len(query) < 2:
        return await interaction.followup.send("❌ Введите запрос (минимум 2 символа)!", ephemeral=True)
    
    if not config.UNSPLASH_ACCESS_KEY:
        return await interaction.followup.send("❌ Unsplash API ключ не настроен!", ephemeral=True)
    
    url = "https://api.unsplash.com/search/photos"
    headers = {
        "Authorization": f"Client-ID {config.UNSPLASH_ACCESS_KEY}"
    }
    params = {
        "query": query,
        "per_page": 10,
        "lang": "ru",
        "order_by": "relevant"
    }
    
    try:
        async with session.get(url, headers=headers, params=params, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                images = data.get("results", [])
                
                if not images:
                    return await interaction.followup.send("😕 Картинки не найдены!", ephemeral=True)
                
                first = images[0]
                img_url = first["urls"]["regular"]
                description = first.get("description", "Image") or first.get("alt_description", "Image")
                photographer = first["user"]["name"]
                
                embed = discord.Embed(title=f"🖼️ {description[:100]}", color=discord.Color.blue())
                embed.set_image(url=img_url)
                embed.set_footer(text=f"📸 1/{len(images)} | Unsplash | {photographer}")
                
                view = ImagePaginator(images, interaction.user.id)
                msg = await interaction.followup.send(embed=embed, view=view)
                view.message = msg
            else:
                error_text = await resp.text()
                await interaction.followup.send(f" Ошибка Unsplash: {resp.status}", ephemeral=True)
    except Exception as e:
        logger.error(f"Image error: {e}")
        await interaction.followup.send(f"❌ Ошибка: {str(e)}", ephemeral=True)


@client.tree.command(name="help", description="📖 Справка")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 Image GIF Bot - Справка",
        description=(
            "**Команды:**\n\n"
            "**/gif** <запрос> - Найти GIF (Giphy)\n"
            "**/image** <запрос> - Найти фото (Unsplash)\n"
            "**/help** - Справка\n"
            "**/ping** - Пинг бота"
        ),
        color=discord.Color.pink()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@client.tree.command(name="ping", description="🏓 Пинг")
async def ping_command(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Пинг: **{latency}ms**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== КЛАССЫ КНОПОК (без изменений) ====================

class GIFPaginator(discord.ui.View):
    def __init__(self, gifs: list, author_id: int, source: str = "Giphy"):
        super().__init__(timeout=120)
        self.gifs = gifs
        self.author_id = author_id
        self.current_index = 0
        self.source = source
        self.message = None
    
    async def update_message(self, interaction: discord.Interaction):
        if not self.gifs:
            return
        
        gif = self.gifs[self.current_index]
        
        if self.source == "Giphy":
            gif_url = gif.get("images", {}).get("fixed_width", {}).get("url", "")
            title = gif.get("title", "GIF")[:256]
            username = gif.get("username", "Unknown")
        else:
            gif_url = gif.get("media", [{}])[0].get("gif", {}).get("url", "")
            title = gif.get("content_description", "GIF")[:256]
            username = "Tenor"
        
        embed = discord.Embed(title=title, color=discord.Color.pink())
        embed.set_image(url=gif_url)
        embed.set_footer(text=f"📸 {self.current_index + 1}/{len(self.gifs)} | {self.source}")
        
        self.first.disabled = self.current_index == 0
        self.prev.disabled = self.current_index == 0
        self.next.disabled = self.current_index == len(self.gifs) - 1
        self.last.disabled = self.current_index == len(self.gifs) - 1
        
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Ошибка обновления: {e}")
    
    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.gray)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(" Не ваша команда!", ephemeral=True)
        self.current_index = 0
        await self.update_message(interaction)
    
    @discord.ui.button(label="️", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        if self.current_index > 0:
            self.current_index -= 1
            await self.update_message(interaction)
    
    @discord.ui.button(label="📤 Отправить", style=discord.ButtonStyle.green)
    async def send_gif(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        
        gif = self.gifs[self.current_index]
        if self.source == "Giphy":
            gif_url = gif.get("images", {}).get("fixed_width", {}).get("url", "")
        else:
            gif_url = gif.get("media", [{}])[0].get("gif", {}).get("url", "")
        
        await interaction.channel.send(gif_url)
        await interaction.response.send_message("✅ GIF отправлен!", ephemeral=True)
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        if self.current_index < len(self.gifs) - 1:
            self.current_index += 1
            await self.update_message(interaction)
    
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.gray)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        self.current_index = len(self.gifs) - 1
        await self.update_message(interaction)
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class ImagePaginator(discord.ui.View):
    def __init__(self, images: list, author_id: int):
        super().__init__(timeout=120)
        self.images = images
        self.author_id = author_id
        self.current_index = 0
        self.message = None
    
    async def update_message(self, interaction: discord.Interaction):
        if not self.images:
            return
        
        img = self.images[self.current_index]
        img_url = img["urls"]["regular"]
        description = img.get("description", "Image") or img.get("alt_description", "Image")
        photographer = img["user"]["name"]
        
        embed = discord.Embed(title=f"🖼️ {description[:100]}", color=discord.Color.blue())
        embed.set_image(url=img_url)
        embed.set_footer(text=f"📸 {self.current_index + 1}/{len(self.images)} | Unsplash | {photographer}")
        
        self.first.disabled = self.current_index == 0
        self.prev.disabled = self.current_index == 0
        self.next.disabled = self.current_index == len(self.images) - 1
        self.last.disabled = self.current_index == len(self.images) - 1
        
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Ошибка обновления: {e}")
    
    @discord.ui.button(label="⏮️", style=discord.ButtonStyle.gray)
    async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        self.current_index = 0
        await self.update_message(interaction)
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        if self.current_index > 0:
            self.current_index -= 1
            await self.update_message(interaction)
    
    @discord.ui.button(label=" Отправить", style=discord.ButtonStyle.green)
    async def send_image(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        
        img_url = self.images[self.current_index]["urls"]["full"]
        await interaction.channel.send(img_url)
        await interaction.response.send_message("✅ Картинка отправлена!", ephemeral=True)
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            await self.update_message(interaction)
    
    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.gray)
    async def last(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Не ваша команда!", ephemeral=True)
        self.current_index = len(self.images) - 1
        await self.update_message(interaction)
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    try:
        logger.info("🚀 Запуск бота...")
        if not config.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не найден!")
            sys.exit(1)
        client.run(config.BOT_TOKEN)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session:
            session.close()
