# test_bot.py
import asyncio
from db.models import db
from utils.nick_generator import generate_nickname
from utils.avatars import generate_color, create_avatar


async def test_database():
    """Тестируем работу с базой данных"""
    print("=== ТЕСТ БАЗЫ ДАННЫХ ===")

    try:
        await db.connect()

        # Тест создания пользователя
        test_user_id = 123456789
        nick = generate_nickname()
        color = generate_color()

        user = await db.create_user(test_user_id, nick, color)
        print(f"✅ Создан пользователь: {user}")

        # Тест получения пользователя
        found_user = await db.get_user(test_user_id)
        print(f"✅ Найден пользователь: {found_user}")

        # Тест обновления никнейма
        new_nick = "TestUser123"
        success = await db.update_user_nickname(test_user_id, new_nick)
        print(f"✅ Обновление никнейма: {success}")

        updated_user = await db.get_user(test_user_id)
        print(f"✅ Обновленный пользователь: {updated_user}")

        # Тест аватарки
        avatar_path = create_avatar(new_nick, color)
        print(f"✅ Создана аватарка: {avatar_path}")

        await db.disconnect()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(test_database())