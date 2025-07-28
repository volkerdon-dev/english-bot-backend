# encoding: utf-8
import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types

# Простое логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Переменные окружения
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
PORT = int(os.getenv("PORT", 8000))

logger.info(f"Starting bot with token: {API_TOKEN[:10] if API_TOKEN else 'None'}...")
logger.info(f"Railway URL: {RAILWAY_URL}")

if not API_TOKEN:
    logger.error("TELEGRAM_API_TOKEN is missing!")
    exit(1)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Простой обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logger.info(f"Received /start from user {message.from_user.id}")
    await message.answer("Привет! Бот работает!")

# Обработчик всех текстовых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    logger.info(f"Received text: '{message.text}' from user {message.from_user.id}")
    await message.answer(f"Вы написали: {message.text}")

# Webhook обработчик
async def handle_webhook(request):
    logger.info("Webhook received")
    try:
        update_data = await request.json()
        logger.info(f"Update data: {update_data}")
        
        update = types.Update.to_object(update_data)
        await dp.process_update(update)
        
        logger.info("Webhook processed successfully")
        return web.Response(text="ok")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return web.Response(status=500, text=str(e))

# Health check
async def health_check(request):
    return web.Response(text="OK")

# Startup
async def on_startup(app):
    logger.info("Starting bot...")
    
    if RAILWAY_URL:
        clean_url = RAILWAY_URL.rstrip('/')
        webhook_url = f"{clean_url}/webhook"
        
        await bot.delete_webhook()
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    
    logger.info("Bot started!")

# Shutdown
async def on_shutdown(app):
    logger.info("Shutting down bot...")
    await bot.delete_webhook()

# Создаем приложение
app = web.Application()
app.router.add_post("/webhook", handle_webhook)
app.router.add_get("/health", health_check)
app.router.add_get("/", lambda r: web.Response(text="Bot is running"))

app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    logger.info("Starting application...")
    web.run_app(app, host="0.0.0.0", port=PORT) 