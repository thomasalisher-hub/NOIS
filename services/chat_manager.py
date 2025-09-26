# services/chat_manager.py
from aiogram import Bot
from aiogram.types import ChatPermissions
from db.models import db
import logging

logger = logging.getLogger(__name__)


class ChatManager:
    """Управляет Telegram чатами для комнат"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def create_room_chat(self, room_id: int, room_name: str) -> int:
        """
        Создает Telegram чат для комнаты
        Returns: ID созданного чата
        """
        try:
            # Временно заглушка - будем реализовывать позже
            logger.info(f"Запрос на создание чата для комнаты {room_id}: {room_name}")

            # Пока возвращаем заглушку
            fake_chat_id = room_id + 1000000000  # Временное решение

            # Сохраняем ID чата в базе
            await db.update_room_telegram_id(room_id, fake_chat_id)

            logger.info(f"Создан виртуальный чат для комнаты {room_id}: {fake_chat_id}")
            return fake_chat_id

        except Exception as e:
            logger.error(f"Ошибка создания чата для комнаты {room_id}: {e}")
            raise

    async def add_user_to_chat(self, chat_id: int, user_id: int) -> bool:
        """Добавляет пользователя в чат комнаты (заглушка)"""
        try:
            logger.info(f"Запрос на добавление пользователя {user_id} в чат {chat_id}")

            # Временная заглушка
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Виртуальный доступ к чату комнаты!\n\nID чата: {chat_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {user_id} в чат {chat_id}: {e}")
            return False

    async def send_message_to_room(self, chat_id: int, user_nickname: str,
                                   user_color: str, message_text: str) -> int:
        """
        Отправляет сообщение в чат комнаты с оформлением
        Returns: ID отправленного сообщения
        """
        try:
            # Временная реализация - отправляем сообщение обратно пользователю
            formatted_message = f"💬 <b>Сообщение в комнату (ID: {chat_id})</b>\n\n"
            formatted_message += f"<b><font color='{user_color}'>{user_nickname}</font></b>: {message_text}"

            message = await self.bot.send_message(
                chat_id=user_id,  # Временно отправляем пользователю
                text=formatted_message,
                parse_mode='HTML'
            )

            logger.info(f"Отправлено виртуальное сообщение от {user_nickname} в чат {chat_id}")
            return message.message_id

        except Exception as e:
            logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
            # Fallback: отправляем пользователю
            try:
                message = await self.bot.send_message(
                    chat_id=user_id,
                    text=f"💬 <b>Ваше сообщение:</b> {message_text}",
                    parse_mode='HTML'
                )
                return message.message_id
            except:
                raise

    async def pin_webapp_message(self, chat_id: int, webapp_text: str) -> int:
        """Закрепляет WebApp сообщение в чате (заглушка)"""
        try:
            logger.info(f"Запрос на закрепление WebApp в чате {chat_id}")
            return 1
        except Exception as e:
            logger.error(f"Ошибка закрепления WebApp сообщения в чате {chat_id}: {e}")
            return 0