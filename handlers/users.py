# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Создаем роутер
start_router = Router()


def setup_start_handlers(router, db, chat_manager):
    """Настройка обработчиков старта с зависимостями"""

    @router.message(Command("start"))
    async def start_handler(message: Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id

        try:
            # Проверяем, зарегистрирован ли пользователь
            user = await db.get_user(user_id)

            if user:
                welcome_text = f"""
👋 С возвращением, {user['nickname']}!

Твой цвет: #{user['color_hex']}
Твой ID: {user_id}

Используй /help для списка команд
                """
                await message.answer(welcome_text)
            else:
                # Регистрация нового пользователя
                from utils.nick_generator import NickGenerator
                from utils.avatars import AvatarGenerator

                nick_generator = NickGenerator()
                nickname = nick_generator.generate_random()

                avatar_generator = AvatarGenerator()
                color_hex = avatar_generator.generate_color_from_nick(nickname)

                # Создаем пользователя в БД
                await db.create_user(user_id, nickname, color_hex)

                welcome_text = f"""
🎉 Добро пожаловать в NOIS!

Твой анонимный профиль:
👤 Никнейм: {nickname}
🎨 Цвет: #{color_hex}

Ты автоматически зарегистрирован в системе. 
Для смены ника используй /nick или /random_nick

Используй /help для списка команд
                """

                # Клавиатура с быстрыми действиями
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔄 Сгенерировать новый ник", callback_data="random_nick")
                keyboard.button(text="🎨 Сгенерировать аватарку", callback_data="generate_avatar")
                keyboard.button(text="🏠 Создать комнату", callback_data="create_room")

                await message.answer(welcome_text, reply_markup=keyboard.as_markup())

        except Exception as e:
            logger.error(f"Ошибка в start_handler: {e}")
            await message.answer("❌ Произошла ошибка при регистрации. Попробуйте позже.")

    @router.message(Command("help"))
    async def help_handler(message: Message):
        """Справка по командам"""
        help_text = """
📚 Доступные команды NOIS:

👤 Профиль:
/start - Начало работы
/profile - Просмотр профиля
/nick - Смена ника
/random_nick - Случайный ник
/nick_options - Тематические ники
/avatar - Аватарка

🏠 Комнаты:
/rooms - Список публичных комнат
/myrooms - Мои комнаты
/create - Создать комнату
/join - Присоединиться к комнате
/leave - Покинуть комнату

💬 Сообщения:
/chat - Отправить сообщение в комнату
/history - История сообщений

❓ Помощь:
/help - Эта справка
        """

        await message.answer(help_text)

    # Регистрируем обработчики в основном роутере
    router.message.register(start_handler, Command("start"))
    router.message.register(help_handler, Command("help"))