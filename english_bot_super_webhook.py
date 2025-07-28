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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
PORT = int(os.getenv("PORT", 8000))

if not API_TOKEN:
    logging.error("❌ TELEGRAM_API_TOKEN is missing! Exiting.")
    exit(1)

bot = Bot(token=API_TOKEN)
Bot.set_current(bot)
dp = Dispatcher(bot)
Dispatcher.set_current(dp)

# --- Загрузка данных ---
main_menu_data, grammar_data, ielts_tests_data, words_of_the_day_data = {}, {}, {}, []
vocabulary_topic_packs_data, idioms_phrasal_verbs_data, collocations_data, synonyms_antonyms_data = {}, {}, {}, {}
irregular_verbs_data = [] # Инициализация как список, т.к. irregular_verbs.json - список
games_data = {} # Инициализация как словарь, т.к. games.json - словарь

# НОВЫЕ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ КОНТЕНТА УПРАЖНЕНИЙ
# Обновление: Добавлены переменные для новых категорий грамматических упражнений
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
    # ОБНОВЛЕНИЕ: ДОБАВЛЕНИЕ НОВЫХ ГЛОБАЛЬНЫХ ПЕРЕМЕННЫХ для упражнений
    global tenses_drills_data, parts_of_speech_drills_data, sentence_structure_drills_data, constructions_drills_data, common_mistakes_drills_data
    global vocabulary_quizzes_data, sentence_building_data, listening_comprehension_data, daily_challenges_data

    files_to_load = {
        "main_menu_data": "main_menu_structure.json", "grammar_data": "grammar_categories_tree.json",
        "ielts_tests_data": "ielts_practice_tests.json", "words_of_the_day_data": "words_of_the_day.json",
        "vocabulary_topic_packs_data": "vocabulary_topic_packs.json", "idioms_phrasal_verbs_data": "idioms_phrasal_verbs.json",
        "collocations_data": "collocations.json", "synonyms_antonyms_data": "synonyms_antonyms.json",
        "irregular_verbs_data": "irregular_verbs.json", "games_data": "games.json",
        # НОВЫЕ ПУТИ К ФАЙЛАМ УПРАЖНЕНИЙ (разделены по категориям)
        "tenses_drills_data": "exercises_data/general_practice/tenses_drills.json",
        "parts_of_speech_drills_data": "exercises_data/general_practice/parts_of_speech_drills.json",
        "sentence_structure_drills_data": "exercises_data/general_practice/sentence_structure_drills.json",
        "constructions_drills_data": "exercises_data/general_practice/constructions_drills.json",
        "common_mistakes_drills_data": "exercises_data/general_practice/common_mistakes_drills.json",
        
        "vocabulary_quizzes_data": "exercises_data/general_practice/vocabulary_quizzes.json",
        "sentence_building_data": "exercises_data/interactive_challenges/sentence_building.json",
        "listening_comprehension_data": "exercises_data/interactive_challenges/listening_comprehension.json",
        "daily_challenges_data": "exercises_data/daily_challenges.json", # ПУТЬ СОГЛАСНО ВАШЕМУ ПОСЛЕДНЕМУ УТОЧНЕНИЮ (напрямую в exercises_data)
    }
    for var_name, filename in files_to_load.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                globals()[var_name] = json.load(f)
        except Exception as e:
            logging.error(f"❌ Error loading {filename}: {e}")

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

# ===============================================
# БЛОК ФУНКЦИЙ-ХЕЛПЕРОВ
# ===============================================

async def get_irregular_verbs_telegraph_link():
    global irregular_verbs_telegraph_url
    if irregular_verbs_telegraph_url is None:
        if not irregular_verbs_data: logging.error("Irregular verbs data is not loaded."); return None
        try:
            irregular_verbs_telegraph_url = await create_telegraph_page_for_verbs(
                verbs_data=irregular_verbs_data, title="Неправильные глаголы английского языка"
            )
            return irregular_verbs_telegraph_url
        except Exception as e:
            logging.error(f"Failed to create Telegraph page: {e}", exc_info=True); return None
    return irregular_verbs_telegraph_url

def get_word_of_the_day() -> dict:
    if not words_of_the_day_data: return None
    return random.choice(words_of_the_day_data)

def get_node(data: dict, current_path: list):
    temp_data = data
    node = temp_data # Инициализируем node здесь, чтобы она всегда была определена

    for key in current_path:
        # 1. Находим следующий узел в текущем уровне данных
        if not isinstance(temp_data, dict) or key not in temp_data:
            return None
        node = temp_data[key]

        # 2. Проверяем, не является ли ЭТОТ узел внешней ссылкой
        if isinstance(node, dict) and node.get("type") == "external":
            # Если да, загружаем внешние данные и заменяем ими temp_data для СЛЕДУЮЩЕЙ итерации
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
                # ОБНОВЛЕНИЕ: ДОБАВЛЕНИЕ НОВЫХ ПУТЕЙ К ФАЙЛАМ УПРАЖНЕНИЙ В data_map
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
            ext_data = data_map.get(source_file, {})
            # Если category указана, мы хотим перейти глубже в ext_data.
            # Если category нет, ext_data сама является тем, что нам нужно.
            if category:
                temp_data = ext_data.get(category)
            else:
                temp_data = ext_data
        else:
            # Если это не внешняя ссылка, просто переходим на уровень глубже
            temp_data = node
    
    # После завершения цикла, temp_data содержит конечный результат
    return temp_data

# ===============================================
# БЛОК ФУНКЦИЙ: Построение клавиатур
# ===============================================

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
    
def build_question_markup(question_options: list) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    for opt in question_options:
        markup.add(InlineKeyboardButton(text=opt, callback_data=f"ans_{opt}"))
    return markup

def build_test_actions_markup(test_key: str) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton(text="🏠 В начало", callback_data="go_to_main_menu"))
    markup.add(InlineKeyboardButton(text="🔄 Начать тест заново", callback_data=f"restart_test_{test_key}"))
    return markup
    
def build_true_false_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(text="✅ True", callback_data="game_ans_True"),
        InlineKeyboardButton(text="❌ False", callback_data="game_ans_False")
    )
    return markup

# ===============================================
# Функции отправки контента
# ===============================================

async def send_list_content(chat_id: int, path: list, header_emoji: str):
    node = get_node(main_menu_data, path)
    category_key = path[-1]
    
    # Извлекаем список контента в зависимости от структуры
    content_list = []
    if isinstance(node, list):  # Для простых структур (идиомы, коллокации, или списки тем упражнений)
        content_list = node
    elif isinstance(node, dict) and 'words' in node:  # Для тематических наборов
        content_list = node['words']
    
    if not content_list:
        await bot.send_message(chat_id, "Не удалось найти контент для этой категории.")
        return

    message_parts = [f"{header_emoji} *{category_key}*\n"]
    
    current_section_key = path[-1] 
    parent_of_current_section = path[-2] if len(path) > 1 else ''

    # Handle vocabulary sections (Topic Packs, Idioms, Collocations, Synonyms & Antonyms)
    if parent_of_current_section == 'Topic Packs':
        for item in content_list:
            message_parts.append(f"• *{item.get('word', 'N/A')}* `{item.get('transcription', '')}` – {item.get('translation', 'N/A')}")
    elif parent_of_current_section == 'Idioms & Phrasal Verbs':
        for i, item in enumerate(content_list):
            message_parts.append(f"*{i+1}. {item.get('phrase', 'N/A')}* `{item.get('transcription', '')}`\n   Перевод: {item.get('translation', 'N/A')}\n"
                           f"   Значение: {item.get('meaning', 'N/A')}\n   Пример: _{item.get('example_sentence', '')}_\n")
    elif parent_of_current_section == 'Collocations':
        for i, item_data in enumerate(content_list):
            message_parts.append(f"*{i+1}. {item_data.get('collocation', 'N/A')}* – {item_data.get('translation', 'N/A')}\n"
                               f"   Пример: _{item_data.get('example_sentence', '')}_\n")
    elif parent_of_current_section == 'Synonyms & Antonyms':
         for i, item_data in enumerate(content_list):
            synonyms = ", ".join(item_data.get('synonyms', [])) or 'N/A'
            antonyms = ", ".join(item_data.get('antonyms', [])) or 'N/A'
            message_parts.append(f"*{i+1}. {item_data.get('word', 'N/A')}* [{item_data.get('transcription', '')}] – {item_data.get('translation', 'N/A')}\n"
                               f"   *Синонимы:* {synonyms}\n"
                               f"   *Антонимы:* {antonyms}\n")
    # Handle new grammar drill subcategories (which are lists of topics)
    elif current_section_key in ['Tenses Drills', 'Parts of Speech Drills', 'Sentence Structure Drills', 'Constructions Drills', 'Common Mistakes Drills']:
        # This branch should ideally not be reached if build_menu_from_dict is called for topic lists.
        # But if it is, format it as a list of topics with question counts.
        for i, item_data in enumerate(content_list):
            if isinstance(item_data, dict) and 'topic' in item_data:
                 message_parts.append(f"*{i+1}. {item_data.get('topic', 'N/A')}* - {len(item_data.get('questions', []))} вопросов")
            else:
                message_parts.append(f"• {item_data}") # Fallback for unexpected list item type
    else: # Default behavior for other lists (e.g., if any new flat lists are introduced)
        for i, item_data in enumerate(content_list):
            if isinstance(item_data, dict) and 'topic' in item_data: # If it looks like a list of topics
                message_parts.append(f"*{i+1}. {item_data.get('topic', 'N/A')}*")
            elif isinstance(item_data, str): # If it's a simple list of strings
                message_parts.append(f"• {item_data}")
            else: # Generic representation
                message_parts.append(f"• {item_data}")


    full_message = "\n".join(message_parts)
    if len(full_message) > 4096:
        for chunk in [full_message[i:i + 4000] for i in range(0, len(full_message), 4000)]:
            await bot.send_message(chat_id, chunk, parse_mode="Markdown")
    else:
        await bot.send_message(chat_id, full_message, parse_mode="Markdown")

async def send_next_question(chat_id: int):
    user_data = user_state.get(chat_id)
    if not user_data or "active_test" not in user_data: return

    all_questions = user_data.get("all_questions_for_test", [])
    current_q_index = user_data["current_question_index"]

    if current_q_index < len(all_questions):
        question = all_questions[current_q_index]
        question_header = f"✍️ *Вопрос {current_q_index + 1} из {len(all_questions)}*\n\n"
        await bot.send_message(chat_id, f"{question_header}{question['text']}", reply_markup=build_question_markup(question["options"]), parse_mode="Markdown")
    else:
        score = user_data["score"]
        summary_msg = f"🎉 Тест завершен! Ваш результат: {score}/{len(all_questions)}"
        await bot.send_message(chat_id, summary_msg, reply_markup=build_test_actions_markup(user_data["active_test"]))
        user_state[chat_id] = {}


# ===============================================
# ЛОГИКА ИГР
# ===============================================

async def send_next_game_prompt(chat_id: int):
    state = user_state.get(chat_id, {})
    game_key = state.get("active_game")
    if not game_key: return

    game_data = games_data.get(game_key)
    current_index = state.get("game_item_index", 0)
    game_items = game_data.get("items", [])

    if current_index >= len(game_items):
        score = state.get("game_score", 0)
        await bot.send_message(chat_id, f"🎉 Игра \"{game_key}\" окончена!\nВаш счет: {score}/{len(game_items)}",
                             reply_markup=build_menu_from_dict(games_data))
        user_state[chat_id] = {}
        # Возвращаем пользователя в меню игр
        path = user_paths.get(chat_id, [])
        if path: path.pop()
        user_paths[chat_id] = path # Убедиться, что путь обновлен
        return

    item = game_items[current_index]
    game_type = game_data.get("type")

    if game_type == "game_emoji_guess":
        await bot.send_message(chat_id, f"Угадай слово по эмодзи:\n\n{item['emoji']}")
    elif game_type == "game_anagram":
        await bot.send_message(chat_id, f"Собери слово из букв:\n\n`{item['task']}`", parse_mode="Markdown")
    elif game_type == "game_true_false":
        await bot.send_message(chat_id, f"Правда или ложь?\n\n_{item['statement']}_",
                             parse_mode="Markdown", reply_markup=build_true_false_markup())

async def process_game_answer(message: types.Message):
    chat_id = message.chat.id
    state = user_state.get(chat_id, {})
    game_key = state.get("active_game")
    if not game_key: return

    game_data = games_data.get(game_key)
    current_index = state.get("game_item_index", 0)
    item = game_data["items"][current_index]
    
    correct = False
    user_answer = message.text.lower().strip()
    correct_answers = [ans.lower() for ans in item.get("answers", [])] or [item.get("answer", "").lower()]

    if user_answer in correct_answers:
        correct = True
    
    if correct:
        state["game_score"] = state.get("game_score", 0) + 1
        await message.answer(f"✅ Правильно! Это '{correct_answers[0]}'.")
    else:
        await message.answer(f"❌ Неверно. Правильный ответ: '{correct_answers[0]}'.")

    state["game_item_index"] = current_index + 1
    await send_next_game_prompt(chat_id)

# ===============================================
# БЛОК ХЕНДЛЕРОВ TELEGRAM
# ===============================================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    logging.info(f"Start command received from user {message.from_user.id} (chat_id: {message.chat.id})")
    try:
        chat_id = message.chat.id
        user_paths[chat_id] = []
        user_state[chat_id] = {}
        logging.info(f"User paths and state initialized for chat_id: {chat_id}")
        
        response = await message.answer("👋 Добро пожаловать! Пожалуйста, выберите раздел:", reply_markup=build_main_menu(main_menu_data))
        logging.info(f"Start message sent successfully to chat_id: {chat_id}")
        return response
    except Exception as e:
        logging.error(f"Error in start command: {e}", exc_info=True)
        await message.answer("Произошла ошибка при запуске бота. Попробуйте еще раз.")

# WebApp functionality temporarily disabled
# @dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
# async def handle_webapp_command(message: types.Message):
#     cmd = message.web_app_data.data
#     if cmd == 'grammar':
#         await message.answer("📚 Открываем раздел Grammar...")
#     elif cmd == 'vocabulary':
#         await message.answer("🧠 Вот ваш словарь...")
#     elif cmd == 'practice':
#         await message.answer("✍️ Готовы к практике!")
#     elif cmd == 'games':
#         await message.answer("🎮 Игры пока в разработке...")
#     elif cmd == 'full_version':
#         await message.answer("🔐 В полной версии будет больше контента и функционала!")
#     else:
#         await message.answer(f"🤖 Неизвестная команда: {cmd}")


# НОВЫЕ ХЕНДЛЕРЫ ДЛЯ КОМАНД
@dp.message_handler(commands=["grammar"])
async def show_grammar(message: types.Message):
    chat_id = message.chat.id
    user_paths[chat_id] = [] # Сбрасываем путь до корня
    user_paths[chat_id].append('grammar') # Устанавливаем путь в 'grammar'
    current_data_level = get_node(main_menu_data, user_paths[chat_id])
    await message.answer(f"Вы выбрали: *{main_menu_data['grammar']['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))

@dp.message_handler(commands=["ielts"])
async def show_ielts(message: types.Message):
    chat_id = message.chat.id
    user_paths[chat_id] = []
    user_paths[chat_id].append('ielts')
    current_data_level = get_node(main_menu_data, user_paths[chat_id])
    await message.answer(f"Вы выбрали: *{main_menu_data['ielts']['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))

@dp.message_handler(commands=["vocabulary"])
async def show_vocabulary(message: types.Message):
    chat_id = message.chat.id
    user_paths[chat_id] = []
    user_paths[chat_id].append('vocabulary')
    current_data_level = get_node(main_menu_data, user_paths[chat_id])
    await message.answer(f"Вы выбрали: *{main_menu_data['vocabulary']['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))

@dp.message_handler(commands=["exercises"])
async def show_exercises(message: types.Message):
    chat_id = message.chat.id
    user_paths[chat_id] = []
    user_paths[chat_id].append('exercises')
    current_data_level = get_node(main_menu_data, user_paths[chat_id])
    await message.answer(f"Вы выбрали: *{main_menu_data['exercises']['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))

@dp.message_handler(commands=["games"])
async def show_games(message: types.Message):
    chat_id = message.chat.id
    user_paths[chat_id] = []
    user_paths[chat_id].append('games')
    current_data_level = get_node(main_menu_data, user_paths[chat_id])
    await message.answer(f"Вы выбрали: *{main_menu_data['games']['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))

@dp.message_handler(commands=["settings"])
async def show_settings(message: types.Message):
    chat_id = message.chat.id
    user_paths[chat_id] = []
    user_paths[chat_id].append('settings')
    current_data_level = get_node(main_menu_data, user_paths[chat_id])
    await message.answer(f"Вы выбрали: *{main_menu_data['settings']['title']}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(current_data_level))


@dp.message_handler(content_types=types.ContentType.TEXT)
async def navigate(message: types.Message):
    chat_id = message.chat.id
    text = message.text.strip()
    logging.info(f"Processing text message: '{text}' from {chat_id}")
    path = user_paths.get(chat_id, [])
    parent_path = path[:] # Инициализация parent_path в начале функции

    if user_state.get(chat_id, {}).get("active_game"):
        await process_game_answer(message)
        return

    if text == "🏠 В начало":
        await start(message)
        return
    
    if text == "🔙 Назад":
        if path:
            path.pop()
        current_data_level = get_node(main_menu_data, path) if path else main_menu_data
        menu_title = "Главное меню"
        if path:
            parent_node = get_node(main_menu_data, path[:-1]) if len(path) > 1 else main_menu_data
            if parent_node and path[-1] in parent_node:
                menu_title = parent_node[path[-1]].get("title", path[-1])
        await message.answer(f"🔙 {menu_title}:", reply_markup=build_menu_from_dict(current_data_level))
        user_paths[chat_id] = path # Обновляем путь после pop
        return

    # --- НОВОЕ: Обработка выбора темы из подменю упражнений (ПЕРЕНЕСЕНО ВВЕРХ) ---
    # Проверяем, что мы уже находимся внутри категории упражнений, где ожидается выбор темы
    exercises_topic_categories = [
        'Tenses Drills', 'Parts of Speech Drills', 'Sentence Structure Drills',
        'Constructions Drills', 'Common Mistakes Drills',
        'Vocabulary Quizzes', 'Sentence Building', 'Listening Comprehension',
        'Daily Challenges'
    ]
    if parent_path and parent_path[-1] in exercises_topic_categories:
        
        # current_data_level в этом случае уже содержит данные из external-файла (список тем)
        current_exercises_topics = get_node(main_menu_data, parent_path) # Получаем сам список тем
        
        selected_topic_data = None
        if isinstance(current_exercises_topics, list): # Убедимся, что это список тем
            for topic_item in current_exercises_topics:
                if isinstance(topic_item, dict) and topic_item.get('topic', '') == text:
                    selected_topic_data = topic_item
                    break
        
        if selected_topic_data and selected_topic_data.get("questions"):
            # Запускаем тест по выбранной теме
            test_key = f"{parent_path[-1]}_{text}" # Уникальный ключ для теста
            user_state[chat_id] = {"active_test": test_key, "current_question_index": 0, "score": 0,
                                 "all_questions_for_test": selected_topic_data["questions"], "test_type": "exercise_topic"}
            await message.answer(f"Начинаем упражнение: *{selected_topic_data['topic']}*!", reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
            await send_next_question(chat_id)
            return
        else:
            await message.answer("❌ Тема или вопросы не найдены. Пожалуйста, выберите из списка или попробуйте '🔙 Назад'.")
            return
    # --- КОНЕЦ ОБРАБОТКИ ВЫБОРА ТЕМЫ ---

    # Продолжаем основную логику навигации, если не обработали как выбор темы
    current_data_level = get_node(main_menu_data, path) if path else main_menu_data # Перезагружаем на случай, если path изменился
    if not isinstance(current_data_level, dict):
        # Если сюда попали, значит, 'current_data_level' не является словарем, и это не выбор темы.
        # Вероятно, это ошибка, или неподдерживаемый тип контента.
        await message.answer("❌ Ошибка навигации или неподдерживаемый контент. Попробуйте /start")
        return

    target_node_key = None
    for key, value in current_data_level.items():
        if isinstance(value, dict) and value.get("title", "").strip() == text:
            target_node_key = key
            break
        elif key.strip() == text: # Проверяем также по ключу, если title не указан
            target_node_key = key
            break
    
    if target_node_key:
        
        # Специальные обработчики для разделов Smart Vocabulary, которые показывают список
        if parent_path == ['vocabulary', 'Topic Packs'] or \
           parent_path == ['vocabulary', 'Idioms & Phrasal Verbs'] or \
           parent_path == ['vocabulary', 'Collocations'] or \
           parent_path == ['vocabulary', 'Synonyms & Antonyms']:
            
            emoji_map = {
                'Topic Packs': "📚", 'Idioms & Phrasal Verbs': "💡",
                'Collocations': "🤝", 'Synonyms & Antonyms': "↔️"
            }
            await send_list_content(chat_id, parent_path + [target_node_key], emoji_map.get(parent_path[-1], "✨"))
            # Не меняем путь, чтобы пользователь мог сразу выбирать другие темы
            user_paths[chat_id] = parent_path
            return
        
        # ДОБАВЛЕНО: Обработка для разделов упражнений, которые ведут к подменю тем
        # Это сработает, когда пользователь нажимает "Грамматические Упражнения" или "Викторины по Словарю"
        if parent_path and (parent_path[-1] == 'General Practice' or parent_path[-1] == 'Interactive Challenges' or parent_path[-1] == 'Premium Tools'): # Добавил Premium Tools на всякий случай
            node_for_new_exercise = current_data_level.get(target_node_key)
            if node_for_new_exercise and isinstance(node_for_new_exercise, dict) and node_for_new_exercise.get("type") == "external":
                
                new_path = path + [target_node_key] # Формируем новый путь
                external_content = get_node(main_menu_data, new_path) # Получаем содержимое внешнего файла
                
                if isinstance(external_content, list) and all(isinstance(item, dict) and 'topic' in item for item in external_content):
                    # Если внешний контент - это список тем, создаем кнопки для тем
                    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                    for item in external_content:
                        markup.add(KeyboardButton(text=item['topic']))
                    markup.add(KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 В начало"))
                    await message.answer(f"Выберите тему для '{node_for_new_exercise.get('title', target_node_key)}':", parse_mode="Markdown", reply_markup=markup)
                    user_paths[chat_id] = new_path # Обновляем путь пользователя
                    return
                # Если это просто список элементов или другой конечный контент, который send_list_content может обработать
                elif isinstance(external_content, (list, dict)):
                    emoji_map = {
                        'Grammar Drills': "📚", 'Vocabulary Quizzes': "📖",
                        'Sentence Building': "🧩", 'Listening Comprehension': "🎧",
                        'Daily Challenges': "🏆",
                        # Добавьте сюда эмодзи для Premium Tools, если они будут показывать списки
                        'Essay Checker': "✍️", 'Progress Tracking': "📊", 'Customizable Quizzes': "🛠"
                    }
                    await send_list_content(chat_id, new_path, emoji_map.get(target_node_key, "✨"))
                    user_paths[chat_id] = new_path # Обновляем путь пользователя
                    return


        # Запуск игры
        if parent_path == ['games']:
            game_data = games_data.get(target_node_key)
            if game_data:
                user_paths[chat_id].append(target_node_key)
                user_state[chat_id] = {"active_game": target_node_key, "game_item_index": 0, "game_score": 0}
                await message.answer(f"Начинаем игру: *{target_node_key}*!\n\n_{game_data.get('rules', '')}_",
                                     parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
                await send_next_game_prompt(chat_id)
                return

        # --- Общая логика для всех остальных меню ---
        # Здесь мы добавляем target_node_key к пути только если он не был добавлен выше
        if target_node_key not in path: # Проверяем, чтобы избежать дублирования в пути
            path.append(target_node_key)
        
        next_node = current_data_level[target_node_key]
        node_type = next_node.get("type") if isinstance(next_node, dict) else "submenu"
        menu_title = next_node.get("title", target_node_key)
        
        if node_type == "function_call" and next_node.get("function") == "send_word_of_the_day":
            word_data = get_word_of_the_day()
            if word_data:
                message_text = (f"📅 *Слово дня:*\n\n"
                                f"🇬🇧 *{word_data.get('word', 'N/A')}*\n"
                                f"🗣️ Транскрипция: `{word_data.get('transcription', 'N/A')}`\n"
                                f"🇷🇺 Перевод: *{word_data.get('translation', 'N/A')}*\n\n"
                                f"📖 Определение: {word_data.get('definition', 'N/A')}\n\n"
                                f"📝 Пример: _{word_data.get('example_sentence', 'N/A')}_")
                await message.answer(message_text, parse_mode="Markdown")
            else:
                await message.answer("❌ Не удалось загрузить слово дня.")
            path.pop() # Возвращаемся в предыдущее меню
        elif node_type == "grammar_test":
            user_state[chat_id] = {"active_test": target_node_key, "current_question_index": 0, "score": 0,
                                 "all_questions_for_test": next_node.get("questions", []), "test_type": "grammar_test"}
            await message.answer("Запуск теста...", reply_markup=types.ReplyKeyboardRemove())
            await bot.send_message(chat_id, f"✍️ *Инструкции:*\n\n{next_node.get('instructions', '')}", parse_mode="Markdown")
            await send_next_question(chat_id)
        elif node_type == "content_from_file" and next_node.get("file") == "irregular_verbs.json":
            await message.answer("Пожалуйста, подождите, генерирую страницу с глаголами...")
            telegraph_link = await get_irregular_verbs_telegraph_link()
            if telegraph_link:
                await message.answer(f"📝 *Неправильные глаголы:*\n\nТаблица со всеми формами доступна по ссылке ниже:\n"
                                     f"[{menu_title}]({telegraph_link})", parse_mode="Markdown", disable_web_page_preview=False)
            else:
                await message.answer("🛠 К сожалению, не удалось загрузить таблицу.")
            path.pop()
        elif node_type == "text":
            await message.answer(next_node.get("content", "Нет данных."), parse_mode="Markdown")
            path.pop()
        else: 
            data_for_next_menu = get_node(main_menu_data, path) # Перезагружаем data_for_next_menu, так как path изменился
            # Если data_for_next_menu - это список тем (как в grammar_drills.json),
            # нужно создать кнопки для каждой темы.
            # В текущей реализации build_menu_from_dict ожидает словарь.
            # Если data_for_next_menu - это список, это может вызвать ошибку.
            # Нужно будет адаптировать build_menu_from_dict или добавить отдельную функцию для списков тем.
            if isinstance(data_for_next_menu, list) and all(isinstance(item, dict) and 'topic' in item for item in data_for_next_menu):
                markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
                for item in data_for_next_menu:
                    markup.add(KeyboardButton(text=item['topic']))
                markup.add(KeyboardButton(text="🔙 Назад"), KeyboardButton(text="🏠 В начало"))
                await message.answer(f"Вы выбрали: *{menu_title}*. Выберите тему:", parse_mode="Markdown", reply_markup=markup)
            else:
                await message.answer(f"Вы выбрали: *{menu_title}*", parse_mode="Markdown", reply_markup=build_menu_from_dict(data_for_next_menu))
        
        user_paths[chat_id] = path # ОБНОВЛЯЕМ ПУТЬ ПОЛЬЗОВАТЕЛЯ ЗДЕСЬ
    else:
        # Если target_node_key не найден, и это не было обработано как выбор темы,
        # то это неизвестная команда/текст.
        await message.answer("❌ Пожалуйста, используйте кнопки меню.")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('game_ans_'))
async def process_game_callback_answer(callback_query: types.CallbackQuery):
    # Отвечаем на callback_query немедленно, чтобы избежать таймаута
    await bot.answer_callback_query(callback_query.id)

    message = callback_query.message
    chat_id = callback_query.message.chat.id
    state = user_state.get(chat_id, {})
    game_key = state.get("active_game")
    if not game_key: return

    game_data = games_data.get(game_key)
    current_index = state.get("game_item_index", 0)
    item = game_data["items"][current_index]
    
    correct = False
    user_answer = callback_query.data.replace("game_ans_", "").lower().strip()
    correct_answers = [ans.lower() for ans in item.get("answers", [])] or [item.get("answer", "").lower()]

    if user_answer in correct_answers:
        correct = True
    
    if correct:
        state["game_score"] = state.get("game_score", 0) + 1
        await message.answer(f"✅ Правильно! Это '{correct_answers[0]}'.")
    else:
        await message.answer(f"❌ Неверно. Правильный ответ: '{correct_answers[0]}'.")

    state["game_item_index"] = current_index + 1
    await send_next_game_prompt(chat_id)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('ans_'))
async def process_answer(callback_query: types.CallbackQuery):
    """
    Хендлер для обработки ответов на вопросы теста (inline-кнопки).
    """
    # Отвечаем на callback_query немедленно, чтобы избежать таймаута
    await bot.answer_callback_query(callback_query.id) 

    chat_id = callback_query.message.chat.id
    user_data = user_state.get(chat_id)

    if not user_data or "active_test" not in user_data:
        await bot.send_message(chat_id, "❌ Состояние теста не найдено. Начните тест заново.")
        try:
            await bot.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=None,
            )
        except Exception as e:
            logging.debug(f"Ignored edit_message_reply_markup error: {e}")
        return

    current_q_index_overall = user_data["current_question_index"]
    all_questions = user_data["all_questions_for_test"]

    if current_q_index_overall >= len(all_questions):
        await bot.send_message(chat_id, "Тест уже завершен.")
        try:
            await bot.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=None,
            )
        except Exception as e:
            logging.debug(f"Ignored edit_message_reply_markup error: {e}")
        return

    question = all_questions[current_q_index_overall]
    user_answer_text = callback_query.data.replace("ans_", "")
    correct_answer_text = question["correct_answer"]
    explanation = question.get("explanation", "Объяснение не предоставлено.")

    is_correct = (user_answer_text == correct_answer_text)

    if is_correct:
        user_data["score"] += 1
    else:
        pass 
    
    response_detail = (
        f"\n   Ваш ответ: `{escape_markdown(user_answer_text)}`\n"
        f"   Правильный ответ: `{escape_markdown(correct_answer_text)}`\n"
        f"\n💡 *Объяснение:*\n{escape_markdown(explanation)}"
    )

    try:
        await bot.edit_message_text(
            text=escape_markdown(callback_query.message.text) + "\n\n" + ("✅ *Правильно!*" if is_correct else "❌ *Неправильно.*") + response_detail,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown",
            reply_markup=None
        )
    except Exception as e:
        logging.error(f"Error editing message in process_answer: {e}")

    user_data["current_question_index"] += 1
    await send_next_question(chat_id)


def find_test_data_by_key(test_key: str): 
    # Эта функция ищет тест по ключу в grammar_data и теперь также в новых данных упражнений
    # Проверяем в grammar_data
    for category_key, category_value in grammar_data.items():
        if isinstance(category_value, dict):
            for subcategory_key, subcategory_value in category_value.items():
                if subcategory_key == test_key and isinstance(subcategory_value, dict) and subcategory_value.get("type") == "grammar_test":
                    return subcategory_value
    
    # НОВОЕ: Проверяем в данных упражнений
    # Например, если test_key это "Grammar Drills_Present Simple"
    if "_" in test_key:
        parent_category, topic_name = test_key.rsplit("_", 1)
        # Маппинг для поиска в нужной глобальной переменной
        exercise_data_map = {
            "Tenses Drills": tenses_drills_data,
            "Parts of Speech Drills": parts_of_speech_drills_data,
            "Sentence Structure Drills": sentence_structure_drills_data,
            "Constructions Drills": constructions_drills_data,
            "Common Mistakes Drills": common_mistakes_drills_data,
            "Vocabulary Quizzes": vocabulary_quizzes_data,
            "Sentence Building": sentence_building_data,
            "Listening Comprehension": listening_comprehension_data,
            "Daily Challenges": daily_challenges_data,
        }
        source_data = exercise_data_map.get(parent_category)
        if source_data and isinstance(source_data, list):
            for item in source_data:
                if isinstance(item, dict) and item.get('topic') == topic_name:
                    return {"type": "grammar_test", "title": item['topic'], "instructions": "Пожалуйста, ответьте на вопросы.", "questions": item['questions']}
    
    return None

@dp.callback_query_handler(lambda c: c.data and c.data == 'go_to_main_menu')
async def go_to_main_menu_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id) 
    chat_id = callback_query.message.chat.id
    user_state[chat_id] = {}
    user_paths[chat_id] = []
    await bot.send_message(chat_id, "🔝 Главное меню:", reply_markup=build_main_menu(main_menu_data))

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('restart_test_'))
async def restart_test(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id) 
    chat_id = callback_query.message.chat.id
    test_key_to_restart = callback_query.data.replace("restart_test_", "")
    test_data = find_test_data_by_key(test_key_to_restart)
            
    if not test_data:
        await bot.send_message(chat_id, text="Ошибка: тест не найден для перезапуска.")
        try:
            await bot.edit_message_reply_markup(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                reply_markup=None,
            )
        except Exception as e:
            logging.debug(f"Ignored edit_message_reply_markup error: {e}")
        return

    user_state[chat_id] = {
        "active_test": test_key_to_restart, "test_type": test_data.get("type", "grammar_test"),
        "current_question_index": 0, "score": 0, "answers": {},
        "start_time": time.time(), "full_test_data": test_data,
        "all_questions_for_test": test_data.get("questions", [])
    }
    
    instructions = test_data.get("instructions", "Начало теста. Удачи!")
    prefix = "✍️"
    await bot.send_message(chat_id, f"🔄 Тест '{test_data.get('title', test_key_to_restart)}' перезапущен.\n\n{prefix} *Инструкции:*\n\n{instructions}", parse_mode="Markdown")
    await send_next_question(chat_id)


# ===============================================
# WEBHOOK И ЗАПУСК ПРИЛОЖЕНИЯ
# ===============================================

async def handle_webhook(request):
    try:
        logging.info(f"Received webhook request: {request.method} {request.path}")
        update_data = await request.json()
        logging.info(f"Update data: {update_data}")
        
        # Проверяем, есть ли сообщение в update
        if 'message' in update_data:
            message_data = update_data['message']
            chat_id = message_data.get('chat', {}).get('id')
            text = message_data.get('text', '')
            logging.info(f"Processing message: chat_id={chat_id}, text='{text}'")
        
        update = types.Update.to_object(update_data)
        await dp.process_update(update)
        logging.info("Webhook processed successfully")
        return web.Response(text="ok")
    except Exception as e:
        logging.error(f"Error processing webhook: {e}", exc_info=True)
        return web.Response(status=500)

async def keep_alive_task():
    """Периодически логирует активность"""
    while True:
        logging.info("Bot is alive and running")
        await asyncio.sleep(60)  # Логируем каждую минуту

async def on_startup(app):
    await bot.delete_webhook()
    if RAILWAY_URL:
        # Убираем лишние слеши в конце URL
        clean_url = RAILWAY_URL.rstrip('/')
        await bot.set_webhook(f"{clean_url}/webhook")
    
    # ОБНОВЛЕНИЕ: УСТАНОВКА НОВЫХ КОМАНД БОТА
    await bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("grammar", "📘 Грамматика"),
        BotCommand("ielts", "🎓 IELTS & Экзамены"),
        BotCommand("vocabulary", "🧠 Словарный запас"),
        BotCommand("exercises", "✍️ Упражнения и Практика"),
        BotCommand("games", "🎮 Игры"),
        BotCommand("settings", "⚙️ Настройки"),
    ])
    
    logging.info("Bot started successfully and webhook set")
    
    # Запускаем keep-alive задачу
    asyncio.create_task(keep_alive_task())

async def on_shutdown(app):
    await bot.delete_webhook()
    session = await bot.get_session()
    if session and not session.closed: await session.close()

# Функция для обслуживания статических файлов WebApp
async def serve_webapp(request):
    path = request.match_info['path']
    if not path:
        path = 'index.html'
    
    # Путь к файлам WebApp (теперь в корне)
    webapp_path = Path(path)
    
    if webapp_path.exists() and webapp_path.is_file():
        return web.FileResponse(str(webapp_path))
    else:
        # Если файл не найден, возвращаем index.html
        index_path = Path('index.html')
        if index_path.exists():
            return web.FileResponse(str(index_path))
        else:
            return web.Response(text="WebApp not found", status=404)

@web.middleware
async def logging_middleware(request, handler):
    """Middleware для логирования всех запросов"""
    logging.info(f"Request: {request.method} {request.path}")
    response = await handler(request)
    logging.info(f"Response: {response.status}")
    return response

app = web.Application(middlewares=[logging_middleware])
app.router.add_post("/webhook", handle_webhook)
app.router.add_get("/webapp/{path:.*}", serve_webapp)
app.router.add_get("/", lambda r: web.HTTPFound("/webapp/"))
async def health_check(request):
    logging.info("Health check requested")
    return web.Response(text="OK")

app.router.add_get("/health", health_check)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logging.info(f"Received signal {signum}, shutting down gracefully...")
    # Не завершаем приложение сразу, даем время на cleanup

if __name__ == "__main__":
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        logging.info("Starting bot application...")
        web.run_app(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
