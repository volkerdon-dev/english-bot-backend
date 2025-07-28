#!/usr/bin/env python3
# encoding: utf-8
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_environment():
    """Проверяем переменные окружения"""
    print("🔧 Environment Variables Check:")
    print("=" * 50)
    
    # Проверяем основные переменные
    env_vars = [
        "TELEGRAM_API_TOKEN",
        "RAILWAY_PUBLIC_URL", 
        "PORT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Скрываем токен для безопасности
            if var == "TELEGRAM_API_TOKEN":
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
    
    print("=" * 50)
    
    # Проверяем дополнительные переменные
    additional_vars = [
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PROJECT_ID",
        "RAILWAY_SERVICE_ID"
    ]
    
    print("\n🔧 Additional Railway Variables:")
    for var in additional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: Not set")
    
    print("=" * 50)
    
    # Проверяем рабочую директорию
    print(f"\n📁 Working directory: {os.getcwd()}")
    
    # Проверяем файлы в директории
    print("\n📄 Files in directory:")
    try:
        files = os.listdir(".")
        for file in sorted(files):
            if file.endswith(('.py', '.json', '.txt')):
                print(f"  - {file}")
    except Exception as e:
        print(f"❌ Error listing files: {e}")

if __name__ == "__main__":
    check_environment() 