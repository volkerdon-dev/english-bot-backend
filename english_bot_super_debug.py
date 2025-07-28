# encoding: utf-8
import os
import json
import time
import random
import logging
import asyncio
import signal
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiohttp import web

# Максимально детальное логирование
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_super_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Проверяем переменные окружения
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
PORT = int(os.getenv("PORT", 8000))

logger.info("=" * 60)
logger.info("🚀 BOT STARTUP - SUPER DEBUG MODE")
logger.info("=" * 60)

logger.info(f"🔧 Environment variables:")
logger.info(f"  - API_TOKEN: {'✅ Set (' + API_TOKEN[:10] + '...)' if API_TOKEN else '❌ Missing'}")
logger.info(f"  - RAILWAY_URL: {'✅ Set (' + RAILWAY_URL + ')' if RAILWAY_URL else '❌ Missing'}")
logger.info(f"  - PORT: {PORT}")

if not API_TOKEN:
    logger.error("❌ TELEGRAM_API_TOKEN is missing! Exiting.")
    exit(1)

if not RAILWAY_URL:
    logger.error("❌ RAILWAY_PUBLIC_URL is missing! Exiting.")
    exit(1)

logger.info("✅ Environment variables check passed")

# Инициализация бота
try:
    bot = Bot(token=API_TOKEN)
    Bot.set_current(bot)
    dp = Dispatcher(bot)
    Dispatcher.set_current(dp)
    logger.info("✅ Bot and Dispatcher initialized successfully")
except Exception as e:
    logger.error(f"❌ Error initializing bot: {e}", exc_info=True)
    exit(1)

# Загружаем только основные данные для тестирования
def load_basic_data():
    try:
        with open("main_menu_structure.json", "r", encoding="utf-8") as f:
            main_menu_data = json.load(f)
            logger.info(f"✅ Loaded main_menu_structure.json with {len(main_menu_data)} sections")
            return main_menu_data
    except Exception as e:
        logger.error(f"❌ Error loading main_menu_structure.json: {e}")
        return {}

main_menu_data = load_basic_data()

def build_main_menu(data: dict) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    for item_key, item_value in data.items():
        button_text = item_value.get("title", item_key)
        markup.add(KeyboardButton(text=button_text))
    return markup

# Обработчики команд с максимальным логированием
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logger.info("=" * 40)
    logger.info(f"🎯 START COMMAND RECEIVED")
    logger.info(f"  - User ID: {message.from_user.id}")
    logger.info(f"  - Chat ID: {message.chat.id}")
    logger.info(f"  - Message text: '{message.text}'")
    logger.info(f"  - Message date: {message.date}")
    logger.info("=" * 40)
    
    try:
        chat_id = message.chat.id
        
        # Отправляем простое сообщение без клавиатуры
        response = await message.answer("👋 Привет! Бот работает!")
        logger.info(f"✅ Simple response sent to chat_id: {chat_id}")
        
        # Отправляем сообщение с клавиатурой
        markup = build_main_menu(main_menu_data)
        response2 = await message.answer("Выберите раздел:", reply_markup=markup)
        logger.info(f"✅ Menu response sent to chat_id: {chat_id}")
        
        return response
    except Exception as e:
        logger.error(f"❌ Error in start command: {e}", exc_info=True)
        try:
            await message.answer("Произошла ошибка при запуске бота. Попробуйте еще раз.")
        except Exception as e2:
            logger.error(f"❌ Error sending error message: {e2}")

@dp.message_handler(commands=["test"])
async def test_command(message: types.Message):
    logger.info(f"🧪 TEST COMMAND RECEIVED from user {message.from_user.id}")
    await message.answer("✅ Тестовая команда работает!")

@dp.message_handler(commands=["ping"])
async def ping_command(message: types.Message):
    logger.info(f"🏓 PING COMMAND RECEIVED from user {message.from_user.id}")
    await message.answer("🏓 Pong! Бот отвечает!")

@dp.message_handler(commands=["status"])
async def status_command(message: types.Message):
    logger.info(f"📊 STATUS COMMAND RECEIVED from user {message.from_user.id}")
    
    status_info = f"""
🤖 **Статус бота:**
✅ Бот активен и отвечает
📊 Загружено разделов: {len(main_menu_data)}
🌐 Webhook URL: {RAILWAY_URL}/webhook
⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}
🔧 Режим: SUPER DEBUG
"""
    await message.answer(status_info, parse_mode="Markdown")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    logger.info(f"📝 TEXT MESSAGE RECEIVED: '{message.text}' from user {message.from_user.id}")
    
    if message.text.startswith('/'):
        await message.answer("Команда не распознана. Используйте /start для начала работы.")
    else:
        await message.answer(f"Вы написали: {message.text}")

# Webhook обработчик с максимальным логированием
async def handle_webhook(request):
    logger.info("=" * 50)
    logger.info(f"📡 WEBHOOK RECEIVED")
    logger.info(f"  - Method: {request.method}")
    logger.info(f"  - Path: {request.path}")
    logger.info(f"  - Headers: {dict(request.headers)}")
    logger.info("=" * 50)
    
    try:
        # Читаем тело запроса
        body = await request.read()
        logger.info(f"📡 Request body length: {len(body)} bytes")
        
        # Проверяем, что тело не пустое
        if not body:
            logger.error("❌ Empty request body")
            return web.Response(status=400, text="Empty request body")
        
        # Парсим JSON
        try:
            update_data = await request.json()
            logger.info(f"📡 Update data: {json.dumps(update_data, indent=2)}")
        except Exception as json_error:
            logger.error(f"❌ JSON parsing error: {json_error}")
            logger.error(f"📡 Raw body: {body.decode('utf-8', errors='ignore')}")
            return web.Response(status=400, text=f"JSON parsing error: {str(json_error)}")
        
        # Создаем объект Update
        update = types.Update.to_object(update_data)
        logger.info(f"📡 Update object created successfully")
        
        # Обрабатываем update
        await dp.process_update(update)
        logger.info("✅ Webhook processed successfully")
        
        return web.Response(text="ok", status=200)
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        # Возвращаем более подробную информацию об ошибке
        return web.Response(status=500, text=f"error: {str(e)}")

async def keep_alive_task():
    """Периодически логирует активность"""
    counter = 0
    while True:
        counter += 1
        logger.info(f"🔄 Bot is alive and running (heartbeat #{counter})")
        await asyncio.sleep(60)

async def on_startup(app):
    logger.info("=" * 60)
    logger.info("🚀 STARTUP SEQUENCE BEGINNING")
    logger.info("=" * 60)
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot info: @{bot_info.username} ({bot_info.first_name})")
        
        # Удаляем старый webhook
        await bot.delete_webhook()
        logger.info("🗑️ Deleted old webhook")
        
        # Устанавливаем новый webhook
        clean_url = RAILWAY_URL.rstrip('/')
        webhook_url = f"{clean_url}/webhook"
        await bot.set_webhook(webhook_url)
        logger.info(f"✅ Set webhook to: {webhook_url}")
        
        # Проверяем webhook
        webhook_info = await bot.get_webhook_info()
        logger.info(f"📡 Webhook info:")
        logger.info(f"  - URL: {webhook_info.url}")
        logger.info(f"  - Pending updates: {webhook_info.pending_update_count}")
        logger.info(f"  - Has custom certificate: {webhook_info.has_custom_certificate}")
        
        # Устанавливаем команды бота
        await bot.set_my_commands([
            BotCommand("start", "Запустить бота"),
            BotCommand("test", "Тестовая команда"),
            BotCommand("ping", "Проверка связи"),
            BotCommand("status", "Статус бота"),
        ])
        logger.info("✅ Bot commands set")
        
        # Запускаем keep-alive задачу
        asyncio.create_task(keep_alive_task())
        
        logger.info("✅ Bot started successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}", exc_info=True)

async def on_shutdown(app):
    logger.info("🛑 Shutting down bot...")
    await bot.delete_webhook()
    session = await bot.get_session()
    if session and not session.closed: 
        await session.close()
    logger.info("✅ Bot shutdown complete")

# Создаем приложение
app = web.Application()

# Добавляем маршруты
app.router.add_post("/webhook", handle_webhook)
app.router.add_get("/health", lambda r: web.Response(text="OK"))
app.router.add_get("/", lambda r: web.Response(text="Bot is running"))

# Добавляем обработчики событий
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"📡 Received signal {signum}, shutting down gracefully...")

if __name__ == "__main__":
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        logger.info("🚀 Starting bot application...")
        web.run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True) 