# handlers/rooms.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.models import db
import re

# Создаем роутер для комнат
dp = Router()


@dp.message(Command("create"))
async def cmd_create(message: types.Message):
    """Создание новой комнаты"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем название комнаты из команды
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("""
❌ Укажи название комнаты:

Пример:
<code>/create Мой чат для общения</code>
<code>/create Игры вечером</code>
<code>/create Обсуждение проектов</code>

Максимум 100 символов.
        """)
        return

    room_name = args[1].strip()

    # Проверяем длину названия
    if len(room_name) > 100:
        await message.answer("❌ Название комнаты должно быть не длиннее 100 символов")
        return

    if len(room_name) < 3:
        await message.answer("❌ Название комнаты должно быть не короче 3 символов")
        return

    # Создаем комнату в базе данных
    try:
        room = await db.create_room(
            name=room_name,
            created_by=user_id,
            is_public=True,
            max_participants=50
        )

        # Добавляем создателя в комнату
        await db.add_user_to_room(user_id, room['room_id'])

        await message.answer(f"""
✅ <b>Комната создана!</b>

🏠 <b>Название:</b> {room_name}
🆔 <b>ID комнаты:</b> <code>{room['room_id']}</code>
👥 <b>Максимум участников:</b> {room['max_participants']}
🌐 <b>Статус:</b> Публичная

💡 <b>Что дальше:</b>
1. Поделись ID комнаты с друзьями: <code>{room['room_id']}</code>
2. Или используй команду: <code>/join {room['room_id']}</code>
3. Список комнат: /rooms

🚀 Комната готова к использованию!
        """)

    except Exception as e:
        print(f"Ошибка создания комнаты: {e}")
        await message.answer("❌ Ошибка при создании комнаты. Попробуй позже.")


@dp.message(Command("join"))
async def cmd_join(message: types.Message):
    """Присоединение к комнате"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем ID комнаты из команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("""
❌ Укажи ID комнаты:

Пример:
<code>/join 123</code>
<code>/join 456</code>

💡 ID комнаты можно получить у друга или из списка комнат: /rooms
        """)
        return

    # Пробуем извлечь ID комнаты
    try:
        room_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID комнаты должен быть числом")
        return

    # Проверяем существование комнаты
    room = await db.get_room(room_id)
    if not room:
        await message.answer("❌ Комната не найдена. Проверь ID.")
        return

    # Проверяем, не является ли пользователь уже участником
    if await db.is_user_in_room(user_id, room_id):
        await message.answer(f"❌ Ты уже состоишь в комнате \"{room['name']}\"")
        return

    # Добавляем пользователя в комнату
    success = await db.add_user_to_room(user_id, room_id)

    if success:
        # Получаем количество участников
        participants = await db.get_room_participants(room_id)

        await message.answer(f"""
✅ <b>Присоединился к комнате!</b>

🏠 <b>Комната:</b> {room['name']}
🆔 <b>ID:</b> <code>{room_id}</code>
👥 <b>Участников:</b> {len(participants)}/{room['max_participants']}
👤 <b>Создатель:</b> {room['creator_nickname']}

🎉 Теперь ты участник этой комнаты!
💡 Используй команду /myrooms чтобы увидеть свои комнаты.
        """)
    else:
        await message.answer("❌ Не удалось присоединиться к комнате. Возможно, она заполнена.")


@dp.message(Command("rooms"))
async def cmd_rooms(message: types.Message):
    """Список публичных комнат"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем список публичных комнат
    rooms = await db.get_public_rooms(limit=10)

    if not rooms:
        await message.answer("""
🏠 <b>Публичные комнаты</b>

📭 Пока нет активных публичных комнат.

💡 Ты можешь создать первую комнату:
<code>/create Название твоей комнаты</code>

Или присоединиться к приватной комнате по ID.
        """)
        return

    rooms_text = "🏠 <b>Публичные комнаты</b>\n\n"

    for i, room in enumerate(rooms, 1):
        participant_count = room.get('participant_count', 0)
        rooms_text += f"{i}. <b>{room['name']}</b>\n"
        rooms_text += f"   🆔 ID: <code>{room['room_id']}</code>\n"
        rooms_text += f"   👥 Участников: {participant_count}/{room['max_participants']}\n"
        rooms_text += f"   👤 Создатель: {room['creator_nickname']}\n"
        rooms_text += f"   📅 Создана: {room['created_at'].strftime('%d.%m.%Y')}\n\n"

    rooms_text += "💡 <b>Чтобы присоединиться:</b>\n"
    rooms_text += "<code>/join ID_комнаты</code>\n\n"
    rooms_text += "🔧 <b>Управление комнатами:</b>\n"
    rooms_text += "/myrooms - Мои комнаты\n"
    rooms_text += "/create - Создать комнату"

    await message.answer(rooms_text)


@dp.message(Command("myrooms"))
async def cmd_myrooms(message: types.Message):
    """Список комнат пользователя"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем комнаты пользователя
    rooms = await db.get_user_rooms(user_id)

    if not rooms:
        await message.answer("""
🏠 <b>Мои комнаты</b>

📭 Ты пока не состоишь ни в одной комнате.

💡 Присоединяйся к существующим комнатам:
<code>/rooms</code> - Список публичных комнат
<code>/join ID</code> - Присоединиться по ID

Или создай свою комнату:
<code>/create Название комнаты</code>
        """)
        return

    rooms_text = f"🏠 <b>Мои комнаты</b> ({len(rooms)})\n\n"

    for i, room in enumerate(rooms, 1):
        # Получаем количество участников для каждой комнаты
        participants = await db.get_room_participants(room['room_id'])

        rooms_text += f"{i}. <b>{room['name']}</b>\n"
        rooms_text += f"   🆔 ID: <code>{room['room_id']}</code>\n"
        rooms_text += f"   👥 Участников: {len(participants)}/{room['max_participants']}\n"
        rooms_text += f"   👤 Создатель: {room['creator_nickname']}\n"
        rooms_text += f"   🌐 Статус: {'Публичная' if room['is_public'] else 'Приватная'}\n\n"

    rooms_text += "💡 <b>Команды:</b>\n"
    rooms_text += "/rooms - Все публичные комнаты\n"
    rooms_text += "/create - Создать новую комнату\n"
    rooms_text += "/join ID - Присоединиться к комнате"

    await message.answer(rooms_text)


@dp.message(Command("leave"))
async def cmd_leave(message: types.Message):
    """Выход из комнаты"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем ID комнаты из команды
    args = message.text.split()
    if len(args) < 2:
        # Если ID не указан, показываем список комнат для выхода
        rooms = await db.get_user_rooms(user_id)

        if not rooms:
            await message.answer("❌ Ты не состоишь ни в одной комнате")
            return

        rooms_text = "🚪 <b>Выход из комнаты</b>\n\n"
        rooms_text += "Выбери комнату для выхода:\n\n"

        for i, room in enumerate(rooms, 1):
            rooms_text += f"{i}. <b>{room['name']}</b> (ID: <code>{room['room_id']}</code>)\n"

        rooms_text += "\n💡 Используй: <code>/leave ID_комнаты</code>"
        await message.answer(rooms_text)
        return

    # Пробуем извлечь ID комнаты
    try:
        room_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID комнаты должен быть числом")
        return

    # Проверяем, состоит ли пользователь в комнате
    if not await db.is_user_in_room(user_id, room_id):
        await message.answer("❌ Ты не состоишь в этой комнате")
        return

    # Получаем информацию о комнате
    room = await db.get_room(room_id)
    if not room:
        await message.answer("❌ Комната не найдена")
        return

    # Выходим из комнаты
    success = await db.remove_user_from_room(user_id, room_id)

    if success:
        await message.answer(f"""
🚪 <b>Вышел из комнаты</b>

🏠 Комната: <b>{room['name']}</b>
🆔 ID: <code>{room_id}</code>

✅ Ты больше не участник этой комнаты.
        """)
    else:
        await message.answer("❌ Ошибка при выходе из комнаты")