# bot.py - ИСПРАВЛЕНИЕ ПЕРЕДАЧИ БД
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from aiogram.filters import ExceptionTypeFilter
from dotenv import load_dotenv
import os
import sys
import asyncpg

# Загружаем переменные окружения
load_dotenv()


# --- КОНФИГУРАЦИЯ ---
class Config:
    """Конфигурация приложения"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DB_URL = os.getenv('DB_URL')

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.DB_URL:
            raise ValueError("DB_URL не установлен в .env файле")
        return cls


# --- НАСТРОЙКА ЛОГГИРОВАНИЯ ---
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
try:
    config = Config.validate()
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
except ValueError as e:
    logger.critical(f"Ошибка конфигурации: {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Ошибка инициализации бота: {e}")
    sys.exit(1)


# --- ОБРАБОТЧИКИ ОШИБОК ---
async def database_error_handler(event: ErrorEvent):
    logger.error(f"Ошибка БД: {event.exception}", exc_info=True)
    if event.update.message:
        await event.update.message.answer("🔧 Временные проблемы с базой данных. Попробуйте через минуту.")


async def validation_error_handler(event: ErrorEvent):
    logger.warning(f"Ошибка валидации: {event.exception}")
    if event.update.message:
        await event.update.message.answer("❌ Неверный формат данных. Проверьте ввод и попробуйте снова.")


async def general_error_handler(event: ErrorEvent):
    logger.error(f"Необработанная ошибка: {event.exception}", exc_info=True)
    if event.update.message:
        await event.update.message.answer("⚠️ Произошла непредвиденная ошибка. Разработчик уже уведомлен.")


# --- РЕГИСТРАЦИЯ ROUTERS С ПЕРЕДАЧЕЙ БД ---
async def register_handlers(db_instance):
    """Регистрация routers с передачей экземпляра БД"""
    try:
        # Импортируем routers
        from handlers.start import dp as start_router
        from handlers.rooms import dp as rooms_router
        from handlers.messages import dp as messages_router
        from handlers.webapp import dp as webapp_router

        # Передаем БД в каждый router через диспетчер
        dp['db'] = db_instance

        # Включаем routers
        dp.include_router(start_router)
        dp.include_router(rooms_router)
        dp.include_router(messages_router)
        dp.include_router(webapp_router)

        logger.info("✅ Все routers зарегистрированы с передачей БД")

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта routers: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации routers: {e}")
        raise


# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
async def setup_database():
    try:
        from db.models import Database
        db = Database()
        await db.connect()
        logger.info("✅ База данных подключена")
        return db
    except Exception as e:
        logger.critical(f"❌ Ошибка подключения к БД: {e}")
        raise


# --- ОСНОВНАЯ ФУНКЦИЯ ---
async def main():
    db = None
    try:
        # Подключаем базу данных
        db = await setup_database()

        # Регистрируем обработчики ошибок
        dp.error.register(database_error_handler, ExceptionTypeFilter(asyncpg.PostgresError))
        dp.error.register(validation_error_handler, ExceptionTypeFilter(ValueError))
        dp.error.register(general_error_handler)

        # Регистрируем routers с передачей БД
        await register_handlers(db)

        logger.info("🎯 Бот NOIS запускается...")
        bot_info = await bot.get_me()
        logger.info(f"🤖 ID бота: {bot_info.id}")
        logger.info(f"👤 Username бота: @{bot_info.username}")

        # Запускаем polling
        await dp.start_polling(bot, skip_updates=True)

    except KeyboardInterrupt:
        logger.info("⏹️ Остановка бота по запросу пользователя")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка в main(): {e}", exc_info=True)
        raise
    finally:
        logger.info("🏁 Завершение работы...")
        if db:
            await db.disconnect()
            logger.info("✅ База данных отключена")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 До свидания!")
    except Exception as e:
        logger.critical(f"💀 Фатальная ошибка: {e}", exc_info=True)
        sys.exit(1)