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

from telegraph_utils import create_telegraph_page_for_verbs

# Улучшенное логирование
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Проверяем переменные окружения
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
PORT = int(os.getenv("PORT", 8000))

logger.info(f"🔧 Environment variables:")
logger.info(f"  - API_TOKEN: {'✅ Set' if API_TOKEN else '❌ Missing'}")
logger.info(f"  - RAILWAY_URL: {'✅ Set' if RAILWAY_URL else '❌ Missing'}")
logger.info(f"  - PORT: {PORT}")

if not API_TOKEN:
    logger.error("❌ TELEGRAM_API_TOKEN is missing! Exiting.")
    exit(1)

if not RAILWAY_URL:
    logger.error("❌ RAILWAY_PUBLIC_URL is missing! Exiting.")
    exit(1)

bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)
Dispatcher.set_current(dp)

# --- Загрузка данных ---
main_menu_data, grammar_data, ielts_tests_data, words_of_the_day_data = {}, {}, {}, []
vocabulary_topic_packs_data, idioms_phrasal_verbs_data, collocations_data, synonyms_antonyms_data = {}, {}, {}, {}
irregular_verbs_data = []
games_data = {}

# НОВЫЕ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ КОНТЕНТА УПРАЖНЕНИЙ
tenses_drills_data = {}
parts_of_speech_drills_data = {}
sentence_structure_drills_data = {}
constructions_drills_data = {}
common_mistakes_drills_data = {}

vocabulary_quizzes_data = {}
sentence_building_data = {}
listening_comprehension_data = {}
daily_challenges_data = {}

def load_data():
    global main_menu_data, grammar_data, ielts_tests_data, words_of_the_day_data, vocabulary_topic_packs_data
    global idioms_phrasal_verbs_data, collocations_data, synonyms_antonyms_data, irregular_verbs_data, games_data
    global tenses_drills_data, parts_of_speech_drills_data, sentence_structure_drills_data, constructions_drills_data, common_mistakes_drills_data
    global vocabulary_quizzes_data, sentence_building_data, listening_comprehension_data, daily_challenges_data

    files_to_load = {
        "main_menu_data": "main_menu_structure.json", "grammar_data": "grammar_categories_tree.json",
        "ielts_tests_data": "ielts_practice_tests.json", "words_of_the_day_data": "words_of_the_day.json",
        "vocabulary_topic_packs_data": "vocabulary_topic_packs.json", "idioms_phrasal_verbs_data": "idioms_phrasal_verbs.json",
        "collocations_data": "collocations.json", "synonyms_antonyms_data": "synonyms_antonyms.json",
        "irregular_verbs_data": "irregular_verbs.json", "games_data": "games.json",
        "tenses_drills_data": "exercises_data/general_practice/tenses_drills.json",
        "parts_of_speech_drills_data": "exercises_data/general_practice/parts_of_speech_drills.json",
        "sentence_structure_drills_data": "exercises_data/general_practice/sentence_structure_drills.json",
        "constructions_drills_data": "exercises_data/general_practice/constructions_drills.json",
        "common_mistakes_drills_data": "exercises_data/general_practice/common_mistakes_drills.json",
        "vocabulary_quizzes_data": "exercises_data/general_practice/vocabulary_quizzes.json",
        "sentence_building_data": "exercises_data/interactive_challenges/sentence_building.json",
        "listening_comprehension_data": "exercises_data/interactive_challenges/listening_comprehension.json",
        "daily_challenges_data": "exercises_data/daily_challenges.json",
    }
    
    loaded_count = 0
    for var_name, filename in files_to_load.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                globals()[var_name] = json.load(f)
                loaded_count += 1
                logger.info(f"✅ Loaded {filename}")
        except Exception as e:
            logger.error(f"❌ Error loading {filename}: {e}")

    logger.info(f"📊 Loaded {loaded_count}/{len(files_to_load)} data files")

load_data()

user_paths = {}
user_state = {}
irregular_verbs_telegraph_url = None

# Helper to escape Telegram Markdown special characters
def escape_markdown(text: str) -> str:
    """Escape Markdown special characters for Telegram."""
    for ch in "_*`":
        text = text.replace(ch, f"\\{ch}")
    return text

def build_main_menu(data: dict) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Добавляем остальные кнопки
    for item_key, item_value in data.items():
        button_text = item_value.get("title", item_key)
        markup.add(KeyboardButton(text=button_text))
    return markup

def build_menu_from_dict(data: dict) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for key, item_value in data.items():
        if not isinstance(item_value, (dict, list)): continue
        item_title = item_value.get("title", key) if isinstance(item_value, dict) else key
        markup.add(KeyboardButton(text=item_title))
    markup.add(KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 В начало"))
    return markup

# Обработчики команд
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logger.info(f"🎯 Start command received from user {message.from_user.id} (chat_id: {message.chat.id})")
    try:
        chat_id = message.chat.id
        user_paths[chat_id] = []
        user_state[chat_id] = {}
        logger.info(f"✅ User paths and state initialized for chat_id: {chat_id}")
        
        response = await message.answer("👋 Добро пожаловать! Пожалуйста, выберите раздел:", reply_markup=build_main_menu(main_menu_data))
        logger.info(f"✅ Start message sent successfully to chat_id: {chat_id}")
        return response
    except Exception as e:
        logger.error(f"❌ Error in start command: {e}", exc_info=True)
        await message.answer("Произошла ошибка при запуске бота. Попробуйте еще раз.")

@dp.message_handler(commands=["test"])
async def test_command(message: types.Message):
    """Тестовая команда для проверки работы бота"""
    logger.info(f"🧪 Test command received from user {message.from_user.id}")
    await message.answer("✅ Бот работает! Тестовая команда выполнена успешно.")

@dp.message_handler(commands=["status"])
async def status_command(message: types.Message):
    """Команда для проверки статуса бота"""
    logger.info(f"📊 Status command received from user {message.from_user.id}")
    
    status_info = f"""
🤖 **Статус бота:**
✅ Бот активен
📊 Загружено данных: {len(main_menu_data)} разделов
🌐 Webhook URL: {RAILWAY_URL}/webhook
⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    await message.answer(status_info, parse_mode="Markdown")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    """Обработчик всех текстовых сообщений"""
    logger.info(f"📝 Text message received: '{message.text}' from user {message.from_user.id}")
    
    if message.text == "/start":
        await start(message)
    elif message.text == "/test":
        await test_command(message)
    elif message.text == "/status":
        await status_command(message)
    else:
        await message.answer("Привет! Используйте /start для начала работы с ботом.")

# Webhook обработчик
async def handle_webhook(request):
    logger.info(f"📡 Webhook received: {request.method} {request.path}")
    try:
        update_data = await request.json()
        logger.info(f"📡 Update data: {update_data}")
        
        update = types.Update.to_object(update_data)
        await dp.process_update(update)
        logger.info("✅ Webhook processed successfully")
        return web.Response(text="ok")
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        return web.Response(status=500)

async def keep_alive_task():
    """Периодически логирует активность"""
    while True:
        logger.info("🔄 Bot is alive and running")
        await asyncio.sleep(60)

async def on_startup(app):
    logger.info("🚀 Starting bot application...")
    
    try:
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
        logger.info(f"📡 Webhook info: {webhook_info.url}")
        logger.info(f"📡 Pending updates: {webhook_info.pending_update_count}")
        
        # Устанавливаем команды бота
        await bot.set_my_commands([
            BotCommand("start", "Запустить бота"),
            BotCommand("test", "Тестовая команда"),
            BotCommand("status", "Статус бота"),
        ])
        logger.info("✅ Bot commands set")
        
        # Запускаем keep-alive задачу
        asyncio.create_task(keep_alive_task())
        
        logger.info("✅ Bot started successfully!")
        
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
app.router.add_post("/webhook", handle_webhook)
app.router.add_get("/health", lambda r: web.Response(text="OK"))
app.router.add_get("/", lambda r: web.Response(text="Bot is running"))

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