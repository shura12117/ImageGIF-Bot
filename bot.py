"""
Image GIF Bot для Lolka
Использует discord.py с перенаправлением на Lolka API
API: Giphy (GIF) + Unsplash (картинки)
"""

import discord
from discord import app_commands
from discord.ext import commands
from discord.http import Route
import yarl
import aiohttp
import config
import logging
import os
import sys

# ===== ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ =====
print("=" * 70)
print("🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
print(f"  BOT_TOKEN: {'✅ Найден' if os.environ.get('BOT_TOKEN') else '❌ НЕ НАЙДЕН'}")
print(f"  GIPHY_API_KEY: {'✅ Найден' if os.environ.get('GIPHY_API_KEY') else '❌ НЕ НАЙДЕН'}")
print(f"  UNSPLASH_ACCESS_KEY: {'✅ Найден' if os.environ.get('UNSPLASH_ACCESS_KEY') else '❌ НЕ НАЙДЕН'}")
print("=" * 70)

# ===== ПРОВЕРКА API КЛЮЧЕЙ =====
print("=" * 70)
print("🚀 Image GIF Bot - запуск...")
print(f"🔑 Giphy API Key: {config.GIPHY_API_KEY[:20] if config.GIPHY_API_KEY else 'НЕ УСТАНОВЛЕН'}... (длина: {len(config.GIPHY_API_KEY) if config.GIPHY_API_KEY else 0})")
print(f"🔑 Unsplash API Key: {config.UNSPLASH_ACCESS_KEY[:20] if config.UNSPLASH_ACCESS_KEY else 'НЕ УСТАНОВЛЕН'}... (длина: {len(config.UNSPLASH_ACCESS_KEY) if config.UNSPLASH_ACCESS_KEY else 0})")
print(f"🔑 Bot Token: {config.BOT_TOKEN[:20] if config.BOT_TOKEN else 'НЕ УСТАНОВЛЕН'}... (длина: {len(config.BOT_TOKEN) if config.BOT_TOKEN else 0})")

# Проверка критических переменных
if not config.BOT_TOKEN:
    print("❌ КРИТИЧЕСКАЯ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

if not config.GIPHY_API_KEY:
    print("⚠️  WARNING: GIPHY_API_KEY не настроен, команда /gif не будет работать")

if not config.UNSPLASH_ACCESS_KEY:
    print("⚠️  WARNING: UNSPLASH_ACCESS_KEY не настроен, команда /image не будет работать")

print("=" * 70)

# ===== ПЕРЕНАПРАВЛЕНИЕ НА LOLKA API =====
print("🔗 Настройка подключения к Lolka API...")
Route.BASE = "https://lolka.app/api/bot/v10"
discord.gateway.DiscordWebSocket.DEFAULT_GATEWAY = yarl.URL("wss://lolka.app/ws/bot")
print(f"✅ REST API: {Route.BASE}")
print(f"✅ Gateway: {discord.gateway.DiscordWebSocket.DEFAULT_GATEWAY}")
print("=" * 70)

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


# ==================== КЛАССЫ КНОПОК ====================

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
        else:  # Tenor
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
            return await interaction.response.send_message(" Не ваша команда!", ephemeral=True)
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
    
    @discord.ui.button(label="📤 Отправить", style=discord.ButtonStyle.green)
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


# ==================== СОБЫТИЯ ====================

@client.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    
    logger.info("=" * 70)
    logger.info(f"✅ Бот подключён: {client.user}")
    logger.info(f"📊 Серверов: {len(client.guilds)}")
    logger.info(f"🆔 ID: {client.user.id}")
    logger.info("=" * 70)
    
    try:
        synced = await client.tree.sync()
        logger.info(f"🔄 Синхронизировано команд: {len(synced)}")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации: {e}")


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
                embed.set_footer(text=f" 1/{len(gifs)} | Giphy")
                
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
    """Поиск картинок на Unsplash - ЛУЧШИЕ фото!"""
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
                await interaction.followup.send(f"❌ Ошибка Unsplash: {resp.status}", ephemeral=True)
    except Exception as e:
        logger.error(f"Image error: {e}")
        await interaction.followup.send(f"❌ Ошибка: {str(e)}", ephemeral=True)


@client.tree.command(name="help", description=" Справка")
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


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    try:
        logger.info(" Запуск бота...")
        logger.info(f"🔑 Использование токена (длина: {len(config.BOT_TOKEN)})")
        client.run(config.BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("❌ Неверный токен! Проверьте BOT_TOKEN в переменных окружения Render")
    except discord.PrivilegedIntentsRequired:
        logger.error("❌ Ошибка привилегированных интентов! Проверьте настройки бота в Lolka")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if session:
            session.close()
            logger.info("🔚 Сессия закрыта")
