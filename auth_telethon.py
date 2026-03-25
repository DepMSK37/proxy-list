"""
Запусти этот скрипт ОДИН РАЗ вручную в терминале:
    python auth_telethon.py

Он создаст файл 'proxy_checker.session' — после этого
update.bat будет работать полностью автоматически без вопросов.
"""

import asyncio
from telethon import TelegramClient

API_ID   = 34790560
API_HASH = "225525bde9d579260411ee09cd1ee5a6"
SESSION  = "proxy_checker"  # имя .session файла

async def main():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()  # здесь попросит телефон и код
    me = await client.get_me()
    print(f"\n✅ Авторизация успешна! Аккаунт: {me.first_name} (@{me.username})")
    print(f"✅ Файл '{SESSION}.session' создан — теперь update.bat работает автоматически.")
    await client.disconnect()

asyncio.run(main())
