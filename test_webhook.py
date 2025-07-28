#!/usr/bin/env python3
# encoding: utf-8
import os
import asyncio
import logging
from aiogram import Bot

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_bot_connection():
    """Тест подключения к боту"""
    API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
    RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
    
    if not API_TOKEN:
        logging.error("❌ TELEGRAM_API_TOKEN is missing!")
        return False
    
    if not RAILWAY_URL:
        logging.error("❌ RAILWAY_PUBLIC_URL is missing!")
        return False
    
    logging.info(f"🔑 API Token: {API_TOKEN[:10]}...")
    logging.info(f"🌐 Railway URL: {RAILWAY_URL}")
    
    try:
        bot = Bot(token=API_TOKEN)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logging.info(f"✅ Bot info: @{bot_info.username} ({bot_info.first_name})")
        
        # Проверяем текущий webhook
        webhook_info = await bot.get_webhook_info()
        logging.info(f"📡 Webhook URL: {webhook_info.url}")
        logging.info(f"📡 Webhook allowed updates: {webhook_info.allowed_updates}")
        logging.info(f"📡 Webhook has custom certificate: {webhook_info.has_custom_certificate}")
        logging.info(f"📡 Webhook pending update count: {webhook_info.pending_update_count}")
        
        # Удаляем webhook для тестирования
        await bot.delete_webhook()
        logging.info("🗑️ Deleted webhook")
        
        # Устанавливаем webhook
        clean_url = RAILWAY_URL.rstrip('/')
        webhook_url = f"{clean_url}/webhook"
        await bot.set_webhook(webhook_url)
        logging.info(f"✅ Set webhook to: {webhook_url}")
        
        # Проверяем webhook снова
        webhook_info = await bot.get_webhook_info()
        logging.info(f"📡 New webhook URL: {webhook_info.url}")
        
        await bot.session.close()
        return True
        
    except Exception as e:
        logging.error(f"❌ Error testing bot connection: {e}")
        return False

async def test_webhook_endpoint():
    """Тест webhook endpoint'а"""
    import aiohttp
    from aiohttp import web
    
    RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
    if not RAILWAY_URL:
        logging.error("❌ RAILWAY_PUBLIC_URL is missing!")
        return False
    
    clean_url = RAILWAY_URL.rstrip('/')
    webhook_url = f"{clean_url}/webhook"
    
    # Создаем тестовый update
    test_update = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "testuser",
                "type": "private"
            },
            "date": 1234567890,
            "text": "/start"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=test_update) as response:
                logging.info(f"📡 Webhook response status: {response.status}")
                response_text = await response.text()
                logging.info(f"📡 Webhook response: {response_text}")
                return response.status == 200
    except Exception as e:
        logging.error(f"❌ Error testing webhook endpoint: {e}")
        return False

async def main():
    logging.info("🚀 Starting webhook test...")
    
    # Тест подключения к боту
    if await test_bot_connection():
        logging.info("✅ Bot connection test passed!")
    else:
        logging.error("❌ Bot connection test failed!")
        return
    
    # Тест webhook endpoint'а
    if await test_webhook_endpoint():
        logging.info("✅ Webhook endpoint test passed!")
    else:
        logging.error("❌ Webhook endpoint test failed!")

if __name__ == "__main__":
    asyncio.run(main()) 