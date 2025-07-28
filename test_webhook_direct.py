#!/usr/bin/env python3
# encoding: utf-8
import asyncio
import aiohttp
import json
import os

async def test_webhook_directly():
    """Тестируем webhook напрямую"""
    
    RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
    if not RAILWAY_URL:
        print("❌ RAILWAY_PUBLIC_URL not set")
        return
    
    clean_url = RAILWAY_URL.rstrip('/')
    webhook_url = f"{clean_url}/webhook"
    
    print(f"🌐 Testing webhook URL: {webhook_url}")
    
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
            print(f"📡 Sending test update to webhook...")
            async with session.post(webhook_url, json=test_update) as response:
                print(f"📡 Response status: {response.status}")
                response_text = await response.text()
                print(f"📡 Response text: {response_text}")
                
                if response.status == 200:
                    print("✅ Webhook responded successfully")
                else:
                    print(f"❌ Webhook failed with status {response.status}")
                    
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

async def test_health_endpoint():
    """Тестируем health endpoint"""
    
    RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_URL")
    if not RAILWAY_URL:
        print("❌ RAILWAY_PUBLIC_URL not set")
        return
    
    clean_url = RAILWAY_URL.rstrip('/')
    health_url = f"{clean_url}/health"
    
    print(f"🏥 Testing health URL: {health_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                print(f"🏥 Health response status: {response.status}")
                response_text = await response.text()
                print(f"🏥 Health response: {response_text}")
                
                if response.status == 200:
                    print("✅ Health endpoint working")
                else:
                    print(f"❌ Health endpoint failed")
                    
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")

async def main():
    print("🚀 Starting webhook tests...")
    
    await test_health_endpoint()
    print("-" * 40)
    await test_webhook_directly()

if __name__ == "__main__":
    asyncio.run(main()) 