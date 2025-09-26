# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database.database import Database
from services.chat_manager import ChatManager
from handlers import main_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NOISBot:
    def __init__(self):
        self.config = Config()
        self.storage = MemoryStorage()
        self.bot = Bot(
            token=self.config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.dp = Dispatcher(storage=self.storage)
        self.db = Database()
        self.chat_manager = ChatManager(self.bot, self.db)

    async def setup_dependencies(self):
        """Инициализация зависимостей и передача в обработчики"""
        await self.db.connect()

        # Инициализируем обработчики с зависимостями
        from handlers.start import setup_start_handlers
        from handlers.rooms import setup_room_handlers
        from handlers.messages import setup_message_handlers

        setup_start_handlers(main_router, self.db, self.chat_manager)
        setup_room_handlers(main_router, self.db, self.chat_manager)
        setup_message_handlers(main_router, self.db, self.chat_manager)

    async def start(self):
        """Запуск бота"""
        try:
            logger.info("Инициализация NOIS бота...")

            await self.setup_dependencies()
            self.dp.include_router(main_router)

            logger.info("Бот запускается...")
            await self.dp.start_polling(self.bot)

        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            raise
        finally:
            await self.db.disconnect()
            await self.bot.session.close()


async def main():
    bot = NOISBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())