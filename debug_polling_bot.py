# encoding: utf-8
import os
import json
import time
import random
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# Детальное логирование
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Переменные окружения
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
PORT = int(os.getenv("PORT", 8000))

logger.info(f"Starting debug polling bot with token: {API_TOKEN[:10] if API_TOKEN else 'None'}...")

if not API_TOKEN:
    logger.error("TELEGRAM_API_TOKEN is missing!")
    exit(1)

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logger.info("Bot and Dispatcher initialized successfully")

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

def build_main_menu(data: dict) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
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

def get_node(data: dict, current_path: list):
    temp_data = data
    node = temp_data

    for key in current_path:
        if not isinstance(temp_data, dict) or key not in temp_data:
            return None
        node = temp_data[key]

        if isinstance(node, dict) and node.get("type") == "external":
            source_file = node.get("source")
            category = node.get("category")
            data_map = {
                "grammar_categories_tree.json": grammar_data,
                "ielts_practice_tests.json": ielts_tests_data,
                "vocabulary_topic_packs.json": vocabulary_topic_packs_data,
                "idioms_phrasal_verbs.json": idioms_phrasal_verbs_data,
                "collocations.json": collocations_data,
                "synonyms_antonyms.json": synonyms_antonyms_data,
                "games.json": games_data,
                "exercises_data/general_practice/tenses_drills.json": tenses_drills_data,
                "exercises_data/general_practice/parts_of_speech_drills.json": parts_of_speech_drills_data,
                "exercises_data/general_practice/sentence_structure_drills.json": sentence_structure_drills_data,
                "exercises_data/general_practice/constructions_drills.json": constructions_drills_data,
                "exercises_data/general_practice/common_mistakes_drills.json": common_mistakes_drills_data,
                "exercises_data/general_practice/vocabulary_quizzes.json": vocabulary_quizzes_data,
                "exercises_data/interactive_challenges/sentence_building.json": sentence_building_data,
                "exercises_data/interactive_challenges/listening_comprehension.json": listening_comprehension_data,
                "exercises_data/daily_challenges.json": daily_challenges_data,
            }
            
            if source_file in data_map:
                temp_data = data_map[source_file]
                if category and isinstance(temp_data, dict):
                    temp_data = temp_data.get(category, temp_data)
            else:
                return None

    return node

# Обработчики команд
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logger.info(f"🎯 START COMMAND RECEIVED from user {message.from_user.id}")
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
    logger.info(f"🧪 TEST COMMAND RECEIVED from user {message.from_user.id}")
    await message.answer("✅ Тестовая команда работает!")

@dp.message_handler(commands=["status"])
async def status_command(message: types.Message):
    logger.info(f"📊 STATUS COMMAND RECEIVED from user {message.from_user.id}")
    
    status_info = f"""
🤖 **Статус бота:**
✅ Бот активен и отвечает
📊 Загружено разделов: {len(main_menu_data)}
⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}
🔧 Режим: DEBUG POLLING
"""
    await message.answer(status_info, parse_mode="Markdown")

# Основной обработчик навигации с детальным логированием
@dp.message_handler(content_types=types.ContentType.TEXT)
async def navigate(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip()
    logger.info(f"📝 Processing text message: '{text}' from {chat_id}")
    
    path = user_paths.get(chat_id, [])
    logger.info(f"🔍 Current path: {path}")
    logger.info(f"🔍 Available main menu keys: {list(main_menu_data.keys())}")
    
    # Обработка специальных кнопок
    if text == "🏠 В начало":
        logger.info("🏠 Going to main menu")
        await start(message)
        return
    
    if text == "🔙 Назад":
        logger.info("🔙 Going back")
        if len(path) > 0:
            path.pop()
            user_paths[chat_id] = path
            logger.info(f"🔍 New path after back: {path}")
            if len(path) == 0:
                await start(message)
            else:
                current_data_level = get_node(main_menu_data, path)
                if current_data_level:
                    await message.answer("Вы вернулись назад:", reply_markup=build_menu_from_dict(current_data_level))
                else:
                    await start(message)
        return
    
    # Обработка команд
    if text.startswith('/'):
        logger.info("❌ Command detected, asking to use menu")
        await message.answer("Используйте кнопки меню для навигации.")
        return
    
    # Если мы в корне меню
    if len(path) == 0:
        logger.info(f"🔍 Checking if '{text}' is in main menu")
        if text in main_menu_data:
            logger.info(f"✅ '{text}' found in main menu")
            path.append(text)
            user_paths[chat_id] = path
            current_data_level = get_node(main_menu_data, path)
            logger.info(f"🔍 Current data level type: {type(current_data_level)}")
            if current_data_level:
                logger.info(f"✅ Sending submenu for '{text}'")
                await message.answer(f"Вы выбрали: *{main_menu_data[text]['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))
            else:
                logger.error(f"❌ No data found for '{text}'")
                await message.answer("Раздел не найден.")
        else:
            logger.warning(f"⚠️ '{text}' not found in main menu")
            await message.answer("Пожалуйста, используйте кнопки меню.")
    else:
        # Мы в подменю
        logger.info(f"🔍 In submenu, current path: {path}")
        current_data_level = get_node(main_menu_data, path)
        logger.info(f"🔍 Current data level keys: {list(current_data_level.keys()) if isinstance(current_data_level, dict) else 'Not a dict'}")
        
        if current_data_level and text in current_data_level:
            logger.info(f"✅ '{text}' found in current submenu")
            path.append(text)
            user_paths[chat_id] = path
            next_data_level = get_node(main_menu_data, path)
            logger.info(f"🔍 Next data level type: {type(next_data_level)}")
            
            if isinstance(next_data_level, dict) and next_data_level.get("type") == "text":
                # Это текстовый контент
                logger.info("📄 Sending text content")
                content = next_data_level.get("content", "Контент не найден.")
                await message.answer(content, parse_mode="Markdown")
            elif isinstance(next_data_level, dict):
                # Это подменю
                logger.info("📋 Sending submenu")
                await message.answer(f"Выберите подраздел:", reply_markup=build_menu_from_dict(next_data_level))
            elif isinstance(next_data_level, list):
                # Это список контента
                logger.info("📝 Sending list content")
                content_text = f"*{text}*\n\n"
                for i, item in enumerate(next_data_level[:10], 1):
                    if isinstance(item, dict):
                        content_text += f"{i}. {item.get('title', item.get('word', str(item)))}\n"
                    else:
                        content_text += f"{i}. {item}\n"
                await message.answer(content_text, parse_mode="Markdown")
            else:
                logger.warning(f"⚠️ Unknown data type: {type(next_data_level)}")
                await message.answer("Контент не найден.")
        else:
            logger.warning(f"⚠️ '{text}' not found in current submenu")
            await message.answer("Пожалуйста, используйте кнопки меню.")

async def main():
    logger.info("🚀 Starting debug polling bot...")
    
    # Удаляем webhook если он был установлен
    await bot.delete_webhook()
    logger.info("🗑️ Deleted webhook")
    
    # Устанавливаем команды бота
    await bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("test", "Тестовая команда"),
        BotCommand("status", "Статус бота"),
    ])
    logger.info("✅ Bot commands set")
    
    # Запускаем polling
    logger.info("🔄 Starting polling...")
    await dp.start_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}") 