# encoding: utf-8
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types

# Простое логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Переменные окружения
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
PORT = int(os.getenv("PORT", 8000))

logger.info(f"Starting polling bot with token: {API_TOKEN[:10] if API_TOKEN else 'None'}...")

if not API_TOKEN:
    logger.error("TELEGRAM_API_TOKEN is missing!")
    exit(1)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logger.info("Bot and Dispatcher initialized successfully")

# Простой обработчик команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logger.info(f"Received /start from user {message.from_user.id}")
    await message.answer("Привет! Бот работает с polling!")

# Обработчик всех текстовых сообщений
@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    logger.info(f"Received text: '{message.text}' from user {message.from_user.id}")
    await message.answer(f"Вы написали: {message.text}")

# Обработчик команды /test
@dp.message_handler(commands=["test"])
async def test_command(message: types.Message):
    logger.info(f"Received /test from user {message.from_user.id}")
    await message.answer("✅ Тестовая команда работает!")

# Обработчик команды /ping
@dp.message_handler(commands=["ping"])
async def ping_command(message: types.Message):
    logger.info(f"Received /ping from user {message.from_user.id}")
    await message.answer("🏓 Pong! Бот отвечает!")

async def main():
    logger.info("Starting polling bot...")
    
    # Удаляем webhook если он был установлен
    await bot.delete_webhook()
    logger.info("Deleted webhook")
    
    # Запускаем polling
    logger.info("Starting polling...")
    await dp.start_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}") 