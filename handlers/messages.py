# handlers/messages.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandObject, Command
from db.models import db
from services.chat_manager import ChatManager
import logging

logger = logging.getLogger(__name__)

# СОЗДАЕМ РОУТЕР - добавляем эту строку
dp = Router()

# Глобальная переменная для менеджера чатов (будет инициализирована позже)
chat_manager = None


def setup_chat_manager(bot):
    """Инициализирует менеджер чатов"""
    global chat_manager
    chat_manager = ChatManager(bot)


@dp.message(Command("chat"))
async def cmd_chat(message: Message, command: CommandObject = None):
    """Отправка сообщения в комнату"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем аргументы команды: /chat <room_id> <текст сообщения>
    if not command or not command.args:
        await message.answer("""
💬 <b>Отправка сообщения в комнату</b>

Используй:
<code>/chat ID_комнаты Текст сообщения</code>

Пример:
<code>/chat 123 Привет всем!</code>
<code>/chat 456 Как дела?</code>

💡 Сначала присоединись к комнате: /join ID
📋 Список твоих комнат: /myrooms
        """)
        return

    # Парсим аргументы
    args = command.args.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажи ID комнаты и текст сообщения")
        return

    try:
        room_id = int(args[0])
        message_text = args[1].strip()
    except ValueError:
        await message.answer("❌ ID комнаты должен быть числом")
        return

    # Проверяем, состоит ли пользователь в комнате
    if not await db.is_user_in_room(user_id, room_id):
        await message.answer("❌ Ты не состоишь в этой комнате. Используй /join")
        return

    # Получаем информацию о комнате
    room = await db.get_room(room_id)
    if not room or not room.get('telegram_chat_id'):
        await message.answer("❌ Чат комнаты не настроен. Обратись к создателю комнаты.")
        return

    # Проверяем длину сообщения
    if len(message_text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (максимум 1000 символов)")
        return

    if len(message_text) < 1:
        await message.answer("❌ Сообщение не может быть пустым")
        return

    # Отправляем сообщение в чат комнаты
    try:
        telegram_message_id = await chat_manager.send_message_to_room(
            chat_id=room['telegram_chat_id'],
            user_nickname=user['nickname'],
            user_color=user['color_hex'],
            message_text=message_text
        )

        # Сохраняем сообщение в базе
        await db.create_message(
            room_id=room_id,
            user_id=user_id,
            telegram_message_id=telegram_message_id,
            message_text=message_text,
            user_nickname=user['nickname'],
            user_color_hex=user['color_hex']
        )

        await message.answer(f"""
✅ <b>Сообщение отправлено!</b>

🏠 Комната: <b>{room['name']}</b>
💬 Текст: {message_text}

📨 Сообщение доставлено в чат комнаты.
        """)

    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        await message.answer("❌ Ошибка при отправке сообщения. Попробуй позже.")


@dp.message(Command("history"))
async def cmd_history(message: Message, command: CommandObject = None):
    """Показывает историю сообщений комнаты"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем ID комнаты из аргументов
    if not command or not command.args:
        await message.answer("""
📜 <b>История сообщений комнаты</b>

Используй:
<code>/history ID_комнаты</code>

Пример:
<code>/history 123</code>

💡 Можно также использовать: <code>/history</code> для последней комнаты
        """)
        return

    try:
        room_id = int(command.args)
    except ValueError:
        await message.answer("❌ ID комнаты должен быть числом")
        return

    # Проверяем, состоит ли пользователь в комнате
    if not await db.is_user_in_room(user_id, room_id):
        await message.answer("❌ Ты не состоишь в этой комнате")
        return

    # Получаем историю сообщений
    messages = await db.get_room_messages(room_id, limit=20)

    if not messages:
        await message.answer("""
📜 <b>История сообщений</b>

В этой комнате пока нет сообщений.

💡 Напиши первое сообщение:
<code>/chat {room_id} Твое сообщение</code>
        """.format(room_id=room_id))
        return

    # Формируем текст истории
    room = await db.get_room(room_id)
    history_text = f"📜 <b>История сообщений: {room['name']}</b>\n\n"

    for msg in messages:
        # Форматируем время
        time_str = msg['created_at'].strftime('%H:%M')

        history_text += f"<b><font color='{msg['user_color_hex']}'>{msg['user_nickname']}</font></b> ({time_str}):\n"
        history_text += f"{msg['message_text']}\n\n"

    history_text += f"💡 Всего сообщений: {len(messages)}\n"
    history_text += f"💬 Новое сообщение: <code>/chat {room_id} текст</code>"

    await message.answer(history_text)


@dp.message(F.text)
async def handle_text_messages(message: Message):
    """Обрабатывает текстовые сообщения (не команды)"""
    # Игнорируем сообщения, которые не начинаются с /
    if not message.text.startswith('/'):
        await message.answer("""
💡 <b>Используй команды для работы с ботом:</b>

🏠 <b>Комнаты:</b>
/create Название - Создать комнату
/join ID - Присоединиться к комнате
/rooms - Список комнат
/myrooms - Мои комнаты

💬 <b>Сообщения:</b>
/chat ID текст - Отправить сообщение
/history ID - История сообщений

👤 <b>Профиль:</b>
/profile - Мой профиль
/avatar - Новая аватарка
/nick НовыйНик - Сменить ник
/random_nick - Случайный ник
/nick_options - Варианты ников

❓ /help - Помощь по всем командам
        """)