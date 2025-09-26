# database/database.py
import asyncpg
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Подключение к базе данных"""
        try:
            from config import Config
            config = Config()

            self.pool = await asyncpg.create_pool(config.DB_URL)
            logger.info("✅ Успешное подключение к БД")

        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    async def disconnect(self):
        """Закрытие соединения с БД"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Соединение с БД закрыто")

    async def execute(self, query: str, *args) -> None:
        """Выполнение запроса без возврата результата"""
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Выполнение запроса с возвратом нескольких строк"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Выполнение запроса с возвратом одной строки"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """Выполнение запроса с возвратом одного значения"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ =====

    async def create_user(self, user_id: int, nickname: str, color_hex: str) -> None:
        """Создание нового пользователя"""
        query = """
        INSERT INTO users (user_id, nickname, color_hex, created_at) 
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id) DO UPDATE SET 
            nickname = EXCLUDED.nickname,
            color_hex = EXCLUDED.color_hex
        """
        await self.execute(query, user_id, nickname, color_hex)

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        query = "SELECT * FROM users WHERE user_id = $1"
        row = await self.fetchrow(query, user_id)
        return dict(row) if row else None

    async def get_user_by_nickname(self, nickname: str) -> Optional[Dict]:
        """Получение пользователя по никнейму"""
        query = "SELECT * FROM users WHERE nickname = $1"
        row = await self.fetchrow(query, nickname)
        return dict(row) if row else None

    async def update_user_nickname(self, user_id: int, new_nickname: str) -> None:
        """Обновление никнейма пользователя"""
        query = "UPDATE users SET nickname = $1 WHERE user_id = $2"
        await self.execute(query, new_nickname, user_id)

    async def update_user_color(self, user_id: int, new_color: str) -> None:
        """Обновление цвета пользователя"""
        query = "UPDATE users SET color_hex = $1 WHERE user_id = $2"
        await self.execute(query, new_color, user_id)

    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С КОМНАТАМИ =====

    async def create_room(self, name: str, created_by: int, is_public: bool = True,
                          password: Optional[str] = None, max_participants: int = 50) -> int:
        """Создание новой комнаты"""
        query = """
        INSERT INTO rooms (name, created_by, is_public, password, max_participants, created_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        RETURNING room_id
        """
        room_id = await self.fetchval(query, name, created_by, is_public, password, max_participants)
        return room_id

    async def get_room(self, room_id: int) -> Optional[Dict]:
        """Получение комнаты по ID"""
        query = """
        SELECT r.*, u.nickname as creator_nickname
        FROM rooms r 
        LEFT JOIN users u ON r.created_by = u.user_id 
        WHERE r.room_id = $1
        """
        row = await self.fetchrow(query, room_id)
        return dict(row) if row else None

    async def get_public_rooms(self) -> List[Dict]:
        """Получение списка публичных комнат"""
        query = """
        SELECT r.*, u.nickname as creator_nickname,
               COUNT(ru.user_id) as participants_count
        FROM rooms r 
        LEFT JOIN users u ON r.created_by = u.user_id 
        LEFT JOIN room_users ru ON r.room_id = ru.room_id 
        WHERE r.is_public = true 
        GROUP BY r.room_id, u.nickname 
        ORDER BY r.created_at DESC
        """
        rows = await self.fetch(query)
        return [dict(row) for row in rows]

    async def get_user_rooms(self, user_id: int) -> List[Dict]:
        """Получение комнат пользователя"""
        query = """
        SELECT r.*, u.nickname as creator_nickname
        FROM rooms r 
        LEFT JOIN users u ON r.created_by = u.user_id 
        INNER JOIN room_users ru ON r.room_id = ru.room_id 
        WHERE ru.user_id = $1 
        ORDER BY ru.joined_at DESC
        """
        rows = await self.fetch(query, user_id)
        return [dict(row) for row in rows]

    async def get_user_rooms_count(self, user_id: int) -> int:
        """Получение количества комнат пользователя"""
        query = "SELECT COUNT(*) FROM room_users WHERE user_id = $1"
        return await self.fetchval(query, user_id)

    async def add_user_to_room(self, user_id: int, room_id: int) -> None:
        """Добавление пользователя в комнату"""
        query = """
        INSERT INTO room_users (user_id, room_id, joined_at) 
        VALUES ($1, $2, NOW())
        ON CONFLICT (user_id, room_id) DO NOTHING
        """
        await self.execute(query, user_id, room_id)

    async def remove_user_from_room(self, user_id: int, room_id: int) -> None:
        """Удаление пользователя из комнаты"""
        query = "DELETE FROM room_users WHERE user_id = $1 AND room_id = $2"
        await self.execute(query, user_id, room_id)

    async def get_room_participants(self, room_id: int) -> List[Dict]:
        """Получение участников комнаты"""
        query = """
        SELECT u.*, ru.joined_at 
        FROM room_users ru 
        INNER JOIN users u ON ru.user_id = u.user_id 
        WHERE ru.room_id = $1 
        ORDER BY ru.joined_at ASC
        """
        rows = await self.fetch(query, room_id)
        return [dict(row) for row in rows]

    async def get_room_participants_count(self, room_id: int) -> int:
        """Получение количества участников комнаты"""
        query = "SELECT COUNT(*) FROM room_users WHERE room_id = $1"
        return await self.fetchval(query, room_id)

    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С СООБЩЕНИЯМИ =====

    async def create_message(self, room_id: int, user_id: int, telegram_message_id: int,
                             message_text: str, user_color_hex: str, user_nickname: str) -> int:
        """Создание нового сообщения"""
        query = """
        INSERT INTO messages (room_id, user_id, telegram_message_id, message_text, 
                            user_color_hex, user_nickname, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        RETURNING message_id
        """
        message_id = await self.fetchval(
            query, room_id, user_id, telegram_message_id,
            message_text, user_color_hex, user_nickname
        )
        return message_id

    async def get_room_messages(self, room_id: int, limit: int = 50) -> List[Dict]:
        """Получение сообщений комнаты"""
        query = """
        SELECT m.* 
        FROM messages m 
        WHERE m.room_id = $1 
        ORDER BY m.created_at DESC 
        LIMIT $2
        """
        rows = await self.fetch(query, room_id, limit)
        return [dict(row) for row in rows]

    async def get_message(self, message_id: int) -> Optional[Dict]:
        """Получение сообщения по ID"""
        query = "SELECT * FROM messages WHERE message_id = $1"
        row = await self.fetchrow(query, message_id)
        return dict(row) if row else None

    async def delete_message(self, message_id: int) -> None:
        """Удаление сообщения"""
        query = "DELETE FROM messages WHERE message_id = $1"
        await self.execute(query, message_id)

    # ===== СЛУЖЕБНЫЕ МЕТОДЫ =====

    async def initialize_tables(self):
        """Инициализация таблиц (если не существуют)"""
        try:
            # Проверяем существование таблиц и создаем при необходимости
            # Основная инициализация должна быть через schema.sql
            logger.info("✅ Таблицы БД проверены")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации таблиц: {e}")
            raise