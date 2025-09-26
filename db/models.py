# db/models.py
import asyncpg
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# Загружаем переменные окружения из .env
load_dotenv()


class Database:
    """Класс для работы с базой данных PostgreSQL"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Создает пул подключений к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(os.getenv('DB_URL'))
            print("✅ Подключение к базе данных установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            raise

    async def disconnect(self):
        """Закрывает пул подключений"""
        if self.pool:
            await self.pool.close()
            print("✅ Подключение к базе данных закрыто")

    # === МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, nickname, color_hex, created_at FROM nois.users WHERE user_id = $1",
                user_id
            )
            return dict(row) if row else None

    async def create_user(self, user_id: int, nickname: str, color_hex: str) -> Dict[str, Any]:
        """Создает нового пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO nois.users (user_id, nickname, color_hex) 
                VALUES ($1, $2, $3) 
                RETURNING user_id, nickname, color_hex, created_at
                """,
                user_id, nickname, color_hex
            )
            return dict(row)

    async def update_user_nickname(self, user_id: int, new_nickname: str) -> bool:
        """Обновляет никнейм пользователя"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE nois.users SET nickname = $1 WHERE user_id = $2",
                new_nickname, user_id
            )
            return "UPDATE 1" in result

    # === МЕТОДЫ ДЛЯ КОМНАТ ===

    async def create_room(self, name: str, created_by: int, is_public: bool = True,
                          password: str = None, max_participants: int = 50) -> Dict[str, Any]:
        """Создает новую комнату"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO nois.rooms (name, created_by, is_public, password, max_participants) 
                VALUES ($1, $2, $3, $4, $5) 
                RETURNING room_id, name, created_by, is_public, password, max_participants, created_at
                """,
                name, created_by, is_public, password, max_participants
            )
            return dict(row)

    async def get_room(self, room_id: int) -> Optional[Dict[str, Any]]:
        """Получает комнату по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT r.*, u.nickname as creator_nickname
                FROM nois.rooms r
                LEFT JOIN nois.users u ON r.created_by = u.user_id
                WHERE r.room_id = $1 AND r.is_active = TRUE
                """,
                room_id
            )
            return dict(row) if row else None

    async def get_public_rooms(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает список публичных комнат"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT r.*, u.nickname as creator_nickname,
                       COUNT(ru.user_id) as participant_count
                FROM nois.rooms r
                LEFT JOIN nois.users u ON r.created_by = u.user_id
                LEFT JOIN nois.room_users ru ON r.room_id = ru.room_id
                WHERE r.is_public = TRUE AND r.is_active = TRUE
                GROUP BY r.room_id, u.nickname
                ORDER BY r.created_at DESC
                LIMIT $1
                """,
                limit
            )
            return [dict(row) for row in rows]

    async def update_room_telegram_id(self, room_id: int, telegram_chat_id: int) -> bool:
        """Обновляет ID Telegram чата для комнаты"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE nois.rooms SET telegram_chat_id = $1 WHERE room_id = $2",
                telegram_chat_id, room_id
            )
            return "UPDATE 1" in result

    # === МЕТОДЫ ДЛЯ УЧАСТНИКОВ КОМНАТ ===

    async def add_user_to_room(self, user_id: int, room_id: int) -> bool:
        """Добавляет пользователя в комнату"""
        async with self.pool.acquire() as conn:
            # Проверяем, не является ли пользователь уже участником
            existing = await conn.fetchrow(
                "SELECT 1 FROM nois.room_users WHERE user_id = $1 AND room_id = $2",
                user_id, room_id
            )

            if existing:
                return False  # Уже участник

            # Проверяем количество участников
            participant_count = await conn.fetchval(
                "SELECT COUNT(*) FROM nois.room_users WHERE room_id = $1",
                room_id
            )

            # Получаем лимит комнаты
            max_participants = await conn.fetchval(
                "SELECT max_participants FROM nois.rooms WHERE room_id = $1",
                room_id
            )

            if participant_count >= max_participants:
                return False  # Комната заполнена

            # Добавляем пользователя
            await conn.execute(
                "INSERT INTO nois.room_users (user_id, room_id) VALUES ($1, $2)",
                user_id, room_id
            )
            return True

    async def remove_user_from_room(self, user_id: int, room_id: int) -> bool:
        """Удаляет пользователя из комнаты"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM nois.room_users WHERE user_id = $1 AND room_id = $2",
                user_id, room_id
            )
            return "DELETE 1" in result

    async def get_room_participants(self, room_id: int) -> List[Dict[str, Any]]:
        """Получает список участников комнаты"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT u.user_id, u.nickname, u.color_hex, ru.joined_at
                FROM nois.room_users ru
                JOIN nois.users u ON ru.user_id = u.user_id
                WHERE ru.room_id = $1
                ORDER BY ru.joined_at
                """,
                room_id
            )
            return [dict(row) for row in rows]

    async def get_user_rooms(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает комнаты, в которых состоит пользователь"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT r.*, u.nickname as creator_nickname
                FROM nois.room_users ru
                JOIN nois.rooms r ON ru.room_id = r.room_id
                LEFT JOIN nois.users u ON r.created_by = u.user_id
                WHERE ru.user_id = $1 AND r.is_active = TRUE
                ORDER BY ru.joined_at DESC
                """,
                user_id
            )
            return [dict(row) for row in rows]

    async def is_user_in_room(self, user_id: int, room_id: int) -> bool:
        """Проверяет, является ли пользователь участником комнаты"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM nois.room_users WHERE user_id = $1 AND room_id = $2",
                user_id, room_id
            )
            return bool(row)

    async def create_message(self, room_id: int, user_id: int, telegram_message_id: int,
                             message_text: str, user_nickname: str, user_color_hex: str) -> Dict[str, Any]:
        """Создает запись о сообщении в базе"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO nois.messages 
                (room_id, user_id, telegram_message_id, message_text, user_nickname, user_color_hex) 
                VALUES ($1, $2, $3, $4, $5, $6) 
                RETURNING message_id, room_id, user_id, telegram_message_id, message_text, 
                          user_nickname, user_color_hex, created_at
                """,
                room_id, user_id, telegram_message_id, message_text, user_nickname, user_color_hex
            )
            return dict(row)

    async def get_room_messages(self, room_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает последние сообщения комнаты"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT m.*, u.nickname as current_nickname
                FROM nois.messages m
                LEFT JOIN nois.users u ON m.user_id = u.user_id
                WHERE m.room_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
                """,
                room_id, limit
            )
            return [dict(row) for row in reversed(rows)]  # Возвращаем в правильном порядке

    async def get_message_by_telegram_id(self, room_id: int, telegram_message_id: int) -> Optional[Dict[str, Any]]:
        """Находит сообщение по ID Telegram сообщения"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM nois.messages WHERE room_id = $1 AND telegram_message_id = $2",
                room_id, telegram_message_id
            )
            return dict(row) if row else None

    async def delete_user_messages(self, user_id: int) -> int:
        """Удаляет все сообщения пользователя (для функции очистки данных)"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM nois.messages WHERE user_id = $1",
                user_id
            )
            # Возвращаем количество удаленных сообщений
            if "DELETE" in result:
                return int(result.split()[1])
            return 0

    # === МЕТОДЫ ДЛЯ СООБЩЕНИЙ ===

    async def create_message(self, room_id: int, user_id: int, telegram_message_id: int,
                             message_text: str, user_nickname: str, user_color_hex: str) -> Dict[str, Any]:
        """Создает запись о сообщении в базе"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO nois.messages 
                (room_id, user_id, telegram_message_id, message_text, user_nickname, user_color_hex) 
                VALUES ($1, $2, $3, $4, $5, $6) 
                RETURNING message_id, room_id, user_id, telegram_message_id, message_text, 
                          user_nickname, user_color_hex, created_at
                """,
                room_id, user_id, telegram_message_id, message_text, user_nickname, user_color_hex
            )
            return dict(row)

    async def get_room_messages(self, room_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает последние сообщения комнаты"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT m.*, u.nickname as current_nickname
                FROM nois.messages m
                LEFT JOIN nois.users u ON m.user_id = u.user_id
                WHERE m.room_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
                """,
                room_id, limit
            )
            return [dict(row) for row in reversed(rows)]  # Возвращаем в правильном порядке

    async def get_message_by_telegram_id(self, room_id: int, telegram_message_id: int) -> Optional[Dict[str, Any]]:
        """Находит сообщение по ID Telegram сообщения"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM nois.messages WHERE room_id = $1 AND telegram_message_id = $2",
                room_id, telegram_message_id
            )
            return dict(row) if row else None

    async def delete_user_messages(self, user_id: int) -> int:
        """Удаляет все сообщения пользователя (для функции очистки данных)"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM nois.messages WHERE user_id = $1",
                user_id
            )
            # Возвращаем количество удаленных сообщений
            if "DELETE" in result:
                return int(result.split()[1])
            return 0


# Создаем глобальный экземпляр базы данных
db = Database()