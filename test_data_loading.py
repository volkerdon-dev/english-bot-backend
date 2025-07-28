#!/usr/bin/env python3
# encoding: utf-8
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data():
    """Тестовая функция загрузки данных"""
    files_to_load = {
        "main_menu_data": "main_menu_structure.json", 
        "grammar_data": "grammar_categories_tree.json",
        "ielts_tests_data": "ielts_practice_tests.json", 
        "words_of_the_day_data": "words_of_the_day.json",
        "vocabulary_topic_packs_data": "vocabulary_topic_packs.json", 
        "idioms_phrasal_verbs_data": "idioms_phrasal_verbs.json",
        "collocations_data": "collocations.json", 
        "synonyms_antonyms_data": "synonyms_antonyms.json",
        "irregular_verbs_data": "irregular_verbs.json", 
        "games_data": "games.json",
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
    
    loaded_data = {}
    errors = []
    
    for var_name, filename in files_to_load.items():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                loaded_data[var_name] = data
                logging.info(f"✅ Successfully loaded {filename}")
        except Exception as e:
            error_msg = f"❌ Error loading {filename}: {e}"
            logging.error(error_msg)
            errors.append(error_msg)
    
    return loaded_data, errors

def test_main_menu_building(loaded_data):
    """Тест построения главного меню"""
    try:
        main_menu_data = loaded_data.get("main_menu_data", {})
        if not main_menu_data:
            logging.error("❌ main_menu_data is empty!")
            return False
            
        # Проверяем структуру главного меню
        expected_keys = ["grammar", "ielts", "vocabulary", "exercises", "games", "settings"]
        for key in expected_keys:
            if key not in main_menu_data:
                logging.error(f"❌ Missing key '{key}' in main_menu_data")
                return False
            else:
                logging.info(f"✅ Found key '{key}' in main_menu_data")
        
        # Проверяем, что у каждого раздела есть title
        for key, value in main_menu_data.items():
            if isinstance(value, dict) and "title" in value:
                logging.info(f"✅ Section '{key}' has title: {value['title']}")
            else:
                logging.warning(f"⚠️ Section '{key}' missing title")
        
        return True
    except Exception as e:
        logging.error(f"❌ Error testing main menu: {e}")
        return False

def main():
    logging.info("🚀 Starting data loading test...")
    
    # Загружаем данные
    loaded_data, errors = load_data()
    
    if errors:
        logging.error(f"❌ Found {len(errors)} errors during data loading:")
        for error in errors:
            logging.error(f"  - {error}")
    else:
        logging.info("✅ All data files loaded successfully!")
    
    # Тестируем построение главного меню
    if test_main_menu_building(loaded_data):
        logging.info("✅ Main menu building test passed!")
    else:
        logging.error("❌ Main menu building test failed!")
    
    # Выводим статистику
    logging.info(f"📊 Loaded {len(loaded_data)} data files")
    for name, data in loaded_data.items():
        if isinstance(data, dict):
            logging.info(f"  - {name}: {len(data)} items")
        elif isinstance(data, list):
            logging.info(f"  - {name}: {len(data)} items")
        else:
            logging.info(f"  - {name}: {type(data)}")

if __name__ == "__main__":
    main() 