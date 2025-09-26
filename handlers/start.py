# handlers/start.py
from typing import Tuple
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.models import db
from utils.nick_generator import generate_nickname, generate_multiple_nicks
from utils.avatars import get_user_avatar, regenerate_user_avatar, generate_color
import os

# Создаем роутер для команд
dp = Router()

# Кеш для хранения путей к аватаркам (чтобы не генерировать повторно в рамках одной сессии)
avatar_cache = {}

# Состояния для FSM (Finite State Machine)
class NicknameStates(StatesGroup):
    waiting_for_nickname = State()

def get_cached_avatar_path(nickname: str, size: int = 512) -> Tuple[str, str]:
    """
    Получает аватарку из кеша или создает новую.
    Возвращает путь к файлу и основной цвет.
    """
    cache_key = f"{nickname}_{size}"

    if cache_key in avatar_cache:
        return avatar_cache[cache_key]

    # Получаем аватарку (будет создана или взята из файлового кеша)
    avatar_path, color = get_user_avatar(nickname, size)
    avatar_cache[cache_key] = (avatar_path, color)

    return avatar_path, color

async def send_avatar_message(message: types.Message, nickname: str, text: str, size: int = 512):
    """
    Универсальная функция для отправки сообщения с аватаркой.
    Использует кеширование для избежания лишней генерации.
    """
    try:
        # Получаем аватарку из кеша
        avatar_path, color = get_cached_avatar_path(nickname, size)

        # Проверяем существование файла
        if os.path.exists(avatar_path):
            photo = FSInputFile(avatar_path)
            await message.answer_photo(
                photo=photo,
                caption=text
            )
        else:
            # Если файл не найден, отправляем только текст
            await message.answer(text)

    except Exception as e:
        print(f"Ошибка отправки аватарки: {e}")
        # Fallback - отправляем только текст
        await message.answer(text)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start с выбором способа создания никнейма"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Пользователь"

    # Проверяем, есть ли пользователь в базе
    existing_user = await db.get_user(user_id)

    if existing_user:
        # Пользователь уже существует
        welcome_text = f"""
👋 С возвращением, {first_name}!

Твой текущий анонимный ник: <b>{existing_user['nickname']}</b>
Цвет твоего ника: {existing_user['color_hex']}

Используй команды:
/profile - Посмотреть профиль
/avatar - Сгенерировать новую аватарку
/random_nick - Сгенерировать случайный ник
/nick_options - Выбрать из вариантов ников
/nick - Сменить никнейм вручную
        """

        # Отправляем сообщение с аватаркой (будет использована кешированная)
        await send_avatar_message(
            message,
            existing_user['nickname'],
            welcome_text,
            size=512
        )

    else:
        # Новый пользователь - предлагаем выбор
        welcome_text = f"""
🎉 Добро пожаловать в NOIS, {first_name}!

NOIS - это анонимный чат в реальном времени. 
Для начала выбери, как хочешь создать свой анонимный ник:

1. 🎲 <b>Автоматически</b> - система сама придумает крутой ник
2. ✏️ <b>Вручную</b> - придумай ник сам

Выбери вариант ниже 👇
        """

        # Создаем клавиатуру с выбором
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎲 Автоматический ник",
                    callback_data="auto_nick"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Выбрать ник вручную",
                    callback_data="manual_nick"
                )
            ]
        ])

        await message.answer(welcome_text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data == "auto_nick")
async def process_auto_nick(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора автоматического ника"""
    try:
        user_id = callback.from_user.id
        first_name = callback.from_user.first_name or "Пользователь"

        # Генерируем случайный никнейм
        new_nickname = generate_nickname()
        new_color = generate_color()

        # Создаем пользователя в базе
        user = await db.create_user(user_id, new_nickname, new_color)

        welcome_text = f"""
🎲 <b>Отличный выбор!</b>

Система сгенерировала для тебя анонимный ник:
<b>{new_nickname}</b>

✨ <b>Что это значит:</b>
• Твой ник полностью анонимен
• Цвет ника уникален и постоянен
• Можешь сменить ник в любой момент

🚀 <b>Команды для начала:</b>
/rooms - Посмотреть публичные комнаты
/create - Создать свою комнату
/random_nick - Сгенерировать новый случайный ник
/nick_options - Выбрать из вариантов ников

Твой цвет: {new_color}
        """

        await callback.message.delete()  # Удаляем сообщение с кнопками
        await send_avatar_message(callback.message, new_nickname, welcome_text, 512)
        await callback.answer()

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            # Если callback устарел, просто отправляем новое сообщение
            await callback.message.answer("❌ Время выбора истекло. Используй /start для начала.")
        else:
            raise e
    except Exception as e:
        print(f"Ошибка в process_auto_nick: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуй снова.")


@dp.callback_query(lambda c: c.data == "manual_nick")
async def process_manual_nick(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора ручного ввода ника"""
    try:
        instruction_text = """
✏️ <b>Выбран ручной ввод ника</b>

Придумай себе анонимный никнейм и отправь его сообщением.

💡 <b>Требования к нику:</b>
• От 3 до 20 символов
• Может содержать буквы, цифры, дефисы, подчеркивания
• Будет отображаться в чатах

📝 <b>Примеры хороших ников:</b>
• ShadowRunner
• CosmicTraveler
• TechWizard
• MysticDreamer
• QuantumExplorer

🎯 <b>Отправь свой никнейм:</b>
        """

        await callback.message.edit_text(instruction_text)
        await state.set_state(NicknameStates.waiting_for_nickname)
        await callback.answer()

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            await callback.message.answer("❌ Время выбора истекло. Используй /start для начала.")
        else:
            raise e
    except Exception as e:
        print(f"Ошибка в process_manual_nick: {e}")
        await callback.answer("❌ Произошла ошибка. Попробуй снова.")


@dp.callback_query(lambda c: c.data.startswith("select_nick_"))
async def process_nick_selection(callback: types.CallbackQuery):
    """Обработка выбора ника из вариантов"""
    try:
        user_id = callback.from_user.id
        selected_nick = callback.data.replace("select_nick_", "")

        # Проверяем, зарегистрирован ли пользователь
        user = await db.get_user(user_id)
        if not user:
            await callback.answer("❌ Сначала запусти бота командой /start", show_alert=True)
            return

        # Обновляем никнейм
        success = await db.update_user_nickname(user_id, selected_nick)

        if success:
            # Обновляем аватарку
            try:
                avatar_path, color = regenerate_user_avatar(selected_nick, size=512)
                cache_key = f"{selected_nick}_512"
                avatar_cache[cache_key] = (avatar_path, color)
            except Exception as e:
                print(f"Ошибка обновления аватарки: {e}")

            await callback.message.edit_text(
                f"✅ <b>Никнейм изменен!</b>\n\n"
                f"Старый ник: <b>{user['nickname']}</b>\n"
                f"Новый ник: <b>{selected_nick}</b>\n\n"
                f"💡 Аватарка автоматически обновлена.\n"
                f"🎨 Используй /profile чтобы увидеть изменения."
            )

        else:
            await callback.message.edit_text("❌ Ошибка при изменении никнейма")

        await callback.answer()

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            # Не пытаемся отвечать на устаревший callback
            pass
        else:
            raise e
    except Exception as e:
        print(f"Ошибка в process_nick_selection: {e}")
        try:
            await callback.answer("❌ Ошибка при выборе ника", show_alert=True)
        except:
            pass


@dp.callback_query(lambda c: c.data == "more_nicks")
async def process_more_nicks(callback: types.CallbackQuery):
    """Генерация новых вариантов ников"""
    try:
        nicks = generate_multiple_nicks(5)

        nicks_text = "🎲 <b>Новые варианты ников</b>\n\n"
        nicks_text += "Выбери понравившийся вариант:\n\n"

        for i, nick in enumerate(nicks, 1):
            nicks_text += f"{i}. <code>{nick}</code>\n"

        nicks_text += "\n💡 Нажми кнопку под понравившимся ником"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for i, nick in enumerate(nicks, 1):
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🎯 Выбрать вариант {i}",
                    callback_data=f"select_nick_{nick}"
                )
            ])

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🎲 Еще варианты", callback_data="more_nicks")
        ])

        await callback.message.edit_text(nicks_text, reply_markup=keyboard)
        await callback.answer()

    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            # Пропускаем устаревшие callback'и
            pass
        else:
            raise e
    except Exception as e:
        print(f"Ошибка в process_more_nicks: {e}")
        try:
            await callback.answer("❌ Ошибка при генерации ников", show_alert=True)
        except:
            pass

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    """Команда для просмотра профиля (использует кешированную аватарку)"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    profile_text = f"""
👤 <b>Твой профиль NOIS</b>

📛 Никнейм: <b>{user['nickname']}</b>
🎨 Цвет: {user['color_hex']}
📅 Регистрация: {user['created_at'].strftime('%d.%m.%Y %H:%M')}

💡 <b>Команды для смены ника:</b>
/random_nick - Случайный ник
/nick_options - Выбрать из вариантов
/nick - Сменить вручную

🚀 <b>Комнаты:</b>
/rooms - Список комнат
/myrooms - Мои комнаты
/create - Создать комнату
        """

    # Отправляем профиль с КЕШИРОВАННОЙ аватаркой (не пересоздаем)
    await send_avatar_message(
        message,
        user['nickname'],
        profile_text,
        size=512
    )

@dp.message(Command("avatar"))
async def cmd_avatar(message: types.Message):
    """Команда для принудительной генерации новой аватарки"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Принудительно пересоздаем аватарку
    try:
        avatar_path, color = regenerate_user_avatar(user['nickname'], size=512)

        # Обновляем кеш
        cache_key = f"{user['nickname']}_512"
        avatar_cache[cache_key] = (avatar_path, color)

        if os.path.exists(avatar_path):
            photo = FSInputFile(avatar_path)
            await message.answer_photo(
                photo=photo,
                caption=f"🎨 Новая аватарка сгенерирована!\nНик: <b>{user['nickname']}</b>\nЦвет: {user['color_hex']}"
            )
        else:
            await message.answer("❌ Ошибка при создании аватарки")

    except Exception as e:
        print(f"Ошибка создания аватарки: {e}")
        await message.answer("❌ Ошибка при создании аватарки")

@dp.message(Command("nick"))
async def cmd_nick(message: types.Message):
    """Обработчик команды /nick для смены никнейма"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Сначала запусти бота командой /start")
        return

    # Получаем новый ник из команды (/nick НовыйНик)
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи новый никнейм: /nick твой_ник")
        return

    new_nickname = args[1].strip()

    # Проверяем длину ника
    if len(new_nickname) < 3 or len(new_nickname) > 20:
        await message.answer("❌ Никнейм должен быть от 3 до 20 символов")
        return

    # Обновляем никнейм в базе
    success = await db.update_user_nickname(user_id, new_nickname)

    if success:
        # При смене ника создаем новую аватарку
        try:
            avatar_path, color = regenerate_user_avatar(new_nickname, size=512)

            # Обновляем кеш для нового ника
            cache_key = f"{new_nickname}_512"
            avatar_cache[cache_key] = (avatar_path, color)

            if os.path.exists(avatar_path):
                photo = FSInputFile(avatar_path)
                await message.answer_photo(
                    photo=photo,
                    caption=f"✅ Никнейм изменен на: <b>{new_nickname}</b>\nЦвет остался прежним: {user['color_hex']}"
                )
            else:
                await message.answer(f"✅ Никнейм изменен на: <b>{new_nickname}</b>")

        except Exception as e:
            print(f"Ошибка создания аватарки: {e}")
            await message.answer(f"✅ Никнейм изменен на: <b>{new_nickname}</b>")
    else:
        await message.answer("❌ Ошибка при изменении никнейма")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда помощи"""
    help_text = """
🆘 <b>Помощь по командам NOIS</b>

/start - Начать работу с ботом
/profile - Посмотреть профиль (кешированная аватарка)

🎲 <b>Управление ником:</b>
/random_nick - Сгенерировать случайный ник
/nick_options - Выбрать из вариантов ников
/nick - Сменить ник вручную
/avatar - Новая аватарка

🏠 <b>Комнаты:</b>
/rooms - Список публичных комнат
/myrooms - Мои комнаты
/create - Создать комнату
/join - Присоединиться к комнате

💡 <b>Особенности:</b>
• При регистрации можно выбрать авто/ручной ник
• Есть генератор вариантов для выбора
• Аватарки кешируются для скорости
• Цвета зависят от никнейма
        """

    await message.answer(help_text)

@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    """Простая тестовая команда без фото"""
    await message.answer("✅ Бот работает! Команда /test выполнена успешно.")

# Очистка кеша при перезапуске (опционально)
@dp.startup()
async def on_startup():
    """Очищаем кеш при запуске бота"""
    avatar_cache.clear()
    print("✅ Кеш аватарок очищен")