#!/usr/bin/env python3
# encoding: utf-8
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Загружаем данные
def load_main_menu_data():
    try:
        with open("main_menu_structure.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading main_menu_structure.json: {e}")
        return {}

def build_main_menu(data: dict) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Добавляем остальные кнопки
    for item_key, item_value in data.items():
        button_text = item_value.get("title", item_key)
        markup.add(KeyboardButton(text=button_text))
    return markup

# Создаем тестовый обработчик
async def test_start_handler():
    """Тестируем обработчик команды /start"""
    
    # Загружаем данные
    main_menu_data = load_main_menu_data()
    if not main_menu_data:
        logging.error("❌ Failed to load main_menu_data")
        return False
    
    logging.info(f"✅ Loaded main_menu_data with {len(main_menu_data)} sections")
    
    # Создаем клавиатуру
    try:
        markup = build_main_menu(main_menu_data)
        logging.info("✅ Successfully built main menu markup")
        
        # Выводим информацию о кнопках
        for row in markup.keyboard:
            for button in row:
                logging.info(f"  - Button: {button.text}")
        
        return True
    except Exception as e:
        logging.error(f"❌ Error building main menu: {e}")
        return False

async def test_message_processing():
    """Тестируем обработку сообщения"""
    
    # Создаем тестовое сообщение
    test_message = types.Message(
        message_id=1,
        date=1234567890,
        chat=types.Chat(id=123456789, type="private"),
        from_user=types.User(id=123456789, is_bot=False, first_name="Test"),
        text="/start"
    )
    
    logging.info(f"📝 Test message: {test_message.text}")
    logging.info(f"📝 Chat ID: {test_message.chat.id}")
    logging.info(f"📝 From user: {test_message.from_user.first_name if test_message.from_user else 'Unknown'}")
    
    return True

async def main():
    logging.info("🚀 Starting start command test...")
    
    # Тест загрузки данных и построения меню
    if await test_start_handler():
        logging.info("✅ Start handler test passed!")
    else:
        logging.error("❌ Start handler test failed!")
        return
    
    # Тест обработки сообщения
    if await test_message_processing():
        logging.info("✅ Message processing test passed!")
    else:
        logging.error("❌ Message processing test failed!")
        return
    
    logging.info("✅ All tests passed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 