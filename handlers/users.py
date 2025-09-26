# handlers/users.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


# Зависимости будут передаваться через мидлварь
class UserHandlers:
    def __init__(self, db, chat_manager):
        self.db = db
        self.chat_manager = chat_manager

    async def start_handler(self, message: Message):
        """Обработчик команды /start"""
        user_id = message.from_user.id

        # Проверяем, зарегистрирован ли пользователь
        user = await self.db.get_user(user_id)

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

            await self.db.create_user(user_id, nickname, color_hex)

            welcome_text = f"""
🎉 Добро пожаловать в NOIS!

Твой анонимный профиль:
👤 Никнейм: {nickname}
🎨 Цвет: #{color_hex}

Ты автоматически зарегистрирован в системе. 
Для смены ника используй /nick или /random_nick

Используй /help для списка команд
            """

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔄 Сгенерировать новый ник", callback_data="random_nick")
            keyboard.button(text="🎨 Сгенерировать аватарку", callback_data="generate_avatar")

            await message.answer(welcome_text, reply_markup=keyboard.as_markup())

    async def profile_handler(self, message: Message):
        """Просмотр профиля"""
        user_id = message.from_user.id
        user = await self.db.get_user(user_id)

        if not user:
            await message.answer("❌ Ты не зарегистрирован. Используй /start")
            return

        profile_text = f"""
📊 Твой профиль NOIS:

👤 Никнейм: {user['nickname']}
🎨 Цвет: #{user['color_hex']}
📅 Регистрация: {user['created_at'].strftime('%d.%m.%Y')}
🏠 Активных комнат: {await self.db.get_user_rooms_count(user_id)}

Изменить профиль:
/nick - сменить ник вручную
/random_nick - случайный ник
/avatar - перегенерировать аватарку
        """

        # Генерируем аватарку
        from utils.avatars import AvatarGenerator
        avatar_generator = AvatarGenerator()
        avatar_path = await avatar_generator.generate_avatar(user['nickname'], user['color_hex'])

        with open(avatar_path, 'rb') as photo:
            await message.answer_photo(photo, caption=profile_text)

    async def nick_handler(self, message: Message):
        """Смена ника вручную"""
        user_id = message.from_user.id
        user = await self.db.get_user(user_id)

        if not user:
            await message.answer("❌ Ты не зарегистрирован. Используй /start")
            return

        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Укажи новый никнейм: /nick НовыйНик")
            return

        new_nick = args[1].strip()

        # Валидация ника
        if len(new_nick) < 2 or len(new_nick) > 32:
            await message.answer("❌ Никнейм должен быть от 2 до 32 символов")
            return

        if not all(c.isalnum() or c in ['-', '_'] for c in new_nick):
            await message.answer("❌ Никнейм может содержать только буквы, цифры, дефисы и подчеркивания")
            return

        # Проверяем уникальность ника
        existing_user = await self.db.get_user_by_nickname(new_nick)
        if existing_user and existing_user['user_id'] != user_id:
            await message.answer("❌ Этот никнейм уже занят")
            return

        # Обновляем ник
        await self.db.update_user_nickname(user_id, new_nick)
        await message.answer(f"✅ Никнейм изменен на: {new_nick}")

    async def random_nick_handler(self, message: Message):
        """Генерация случайного ника"""
        user_id = message.from_user.id
        user = await self.db.get_user(user_id)

        if not user:
            await message.answer("❌ Ты не зарегистрирован. Используй /start")
            return

        from utils.nick_generator import NickGenerator
        nick_generator = NickGenerator()
        new_nick = nick_generator.generate_random()

        # Проверяем уникальность
        while await self.db.get_user_by_nickname(new_nick):
            new_nick = nick_generator.generate_random()

        await self.db.update_user_nickname(user_id, new_nick)
        await message.answer(f"✅ Сгенерирован новый ник: {new_nick}")

    async def help_handler(self, message: Message):
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


# Функция для инициализации обработчиков
def setup_user_handlers(router, db, chat_manager):
    handlers = UserHandlers(db, chat_manager)

    router.message.register(handlers.start_handler, Command("start"))
    router.message.register(handlers.profile_handler, Command("profile"))
    router.message.register(handlers.nick_handler, Command("nick"))
    router.message.register(handlers.random_nick_handler, Command("random_nick"))
    router.message.register(handlers.help_handler, Command("help"))