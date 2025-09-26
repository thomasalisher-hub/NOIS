# database.py
import asyncpg
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, db_url: str):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(db_url)
            logger.info("✅ Успешное подключение к БД")
            await self._initialize_tables()
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    async def disconnect(self):
        """Закрытие соединения с БД"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Соединение с БД закрыто")

    async def _initialize_tables(self):
        """Инициализация таблиц БД"""
        try:
            # Таблица пользователей
            await self._execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    nickname VARCHAR(32) NOT NULL,
                    color_hex VARCHAR(7) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Таблица комнат
            await self._execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    created_by BIGINT REFERENCES users(user_id),
                    is_public BOOLEAN DEFAULT true,
                    password VARCHAR(100),
                    max_participants INTEGER DEFAULT 50,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Таблица связи пользователей и комнат
            await self._execute("""
                CREATE TABLE IF NOT EXISTS room_users (
                    user_id BIGINT REFERENCES users(user_id),
                    room_id INTEGER REFERENCES rooms(room_id),
                    joined_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user_id, room_id)
                )
            """)

            # Таблица сообщений
            await self._execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id SERIAL PRIMARY KEY,
                    room_id INTEGER REFERENCES rooms(room_id),
                    user_id BIGINT REFERENCES users(user_id),
                    telegram_message_id INTEGER,
                    message_text TEXT NOT NULL,
                    user_color_hex VARCHAR(7) NOT NULL,
                    user_nickname VARCHAR(32) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            logger.info("✅ Таблицы БД инициализированы")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации таблиц: {e}")
            raise

    async def _execute(self, query: str, *args):
        """Выполнение запроса без возврата результата"""
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)

    async def _fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Выполнение запроса с возвратом нескольких строк"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def _fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Выполнение запроса с возвратом одной строки"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def _fetchval(self, query: str, *args) -> Any:
        """Выполнение запроса с возвратом одного значения"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ =====

    async def create_user(self, user_id: int, nickname: str, color_hex: str):
        """Создание нового пользователя"""
        query = """
        INSERT INTO users (user_id, nickname, color_hex, created_at) 
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id) DO UPDATE SET 
            nickname = EXCLUDED.nickname,
            color_hex = EXCLUDED.color_hex
        """
        await self._execute(query, user_id, nickname, color_hex)

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        query = "SELECT * FROM users WHERE user_id = $1"
        row = await self._fetchrow(query, user_id)
        return dict(row) if row else None

    async def get_user_by_nickname(self, nickname: str) -> Optional[Dict]:
        """Получение пользователя по никнейму"""
        query = "SELECT * FROM users WHERE nickname = $1"
        row = await self._fetchrow(query, nickname)
        return dict(row) if row else None

    async def update_user_nickname(self, user_id: int, new_nickname: str):
        """Обновление никнейма пользователя"""
        query = "UPDATE users SET nickname = $1 WHERE user_id = $2"
        await self._execute(query, new_nickname, user_id)

    async def update_user_color(self, user_id: int, new_color: str):
        """Обновление цвета пользователя"""
        query = "UPDATE users SET color_hex = $1 WHERE user_id = $2"
        await self._execute(query, new_color, user_id)

    # ===== МЕТОДЫ ДЛЯ РАБОТЫ С КОМНАТАМИ =====

    async def create_room(self, name: str, created_by: int, is_public: bool = True,
                          password: Optional[str] = None, max_participants: int = 50) -> int:
        """Создание новой комнаты"""
        query = """
        INSERT INTO rooms (name, created_by, is_public, password, max_participants, created_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        RETURNING room_id
        """
        room_id = await self._fetchval(query, name, created_by, is_public, password, max_participants)
        return room_id

    async def get_room(self, room_id: int) -> Optional[Dict]:
        """Получение комнаты по ID"""
        query = "SELECT * FROM rooms WHERE room_id = $1"
        row = await self._fetchrow(query, room_id)
        return dict(row) if row else None

    async def get_public_rooms(self) -> List[Dict]:
        """Получение списка публичных комнат"""
        query = """
        SELECT r.*, COUNT(ru.user_id) as participants_count
        FROM rooms r 
        LEFT JOIN room_users ru ON r.room_id = ru.room_id 
        WHERE r.is_public = true 
        GROUP BY r.room_id 
        ORDER BY r.created_at DESC
        """
        rows = await self._fetch(query)
        return [dict(row) for row in rows]

    async def get_user_rooms(self, user_id: int) -> List[Dict]:
        """Получение комнат пользователя"""
        query = """
        SELECT r.*, COUNT(ru2.user_id) as participants_count
        FROM rooms r 
        INNER JOIN room_users ru ON r.room_id = ru.room_id 
        LEFT JOIN room_users ru2 ON r.room_id = ru2.room_id 
        WHERE ru.user_id = $1 
        GROUP BY r.room_id 
        ORDER BY ru.joined_at DESC
        """
        rows = await self._fetch(query, user_id)
        return [dict(row) for row in rows]

    async def add_user_to_room(self, user_id: int, room_id: int):
        """Добавление пользователя в комнату"""
        query = """
        INSERT INTO room_users (user_id, room_id, joined_at) 
        VALUES ($1, $2, NOW())
        ON CONFLICT (user_id, room_id) DO NOTHING
        """
        await self._execute(query, user_id, room_id)

    async def remove_user_from_room(self, user_id: int, room_id: int):
        """Удаление пользователя из комнаты"""
        query = "DELETE FROM room_users WHERE user_id = $1 AND room_id = $2"
        await self._execute(query, user_id, room_id)

    async def get_room_participants(self, room_id: int) -> List[Dict]:
        """Получение участников комнаты"""
        query = """
        SELECT u.user_id, u.nickname, u.color_hex, ru.joined_at 
        FROM room_users ru 
        INNER JOIN users u ON ru.user_id = u.user_id 
        WHERE ru.room_id = $1 
        ORDER BY ru.joined_at ASC
        """
        rows = await self._fetch(query, room_id)
        return [dict(row) for row in rows]

    async def get_room_participants_count(self, room_id: int) -> int:
        """Получение количества участников комнаты"""
        query = "SELECT COUNT(*) FROM room_users WHERE room_id = $1"
        return await self._fetchval(query, room_id)

    async def is_user_in_room(self, user_id: int, room_id: int) -> bool:
        """Проверка, находится ли пользователь в комнате"""
        query = "SELECT 1 FROM room_users WHERE user_id = $1 AND room_id = $2"
        result = await self._fetchval(query, user_id, room_id)
        return result is not None

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
        message_id = await self._fetchval(
            query, room_id, user_id, telegram_message_id,
            message_text, user_color_hex, user_nickname
        )
        return message_id

    async def get_room_messages(self, room_id: int, limit: int = 50) -> List[Dict]:
        """Получение сообщений комнаты"""
        query = """
        SELECT m.*, u.color_hex as user_color
        FROM messages m 
        LEFT JOIN users u ON m.user_id = u.user_id 
        WHERE m.room_id = $1 
        ORDER BY m.created_at DESC 
        LIMIT $2
        """
        rows = await self._fetch(query, room_id, limit)
        return [dict(row) for row in rows]

    async def get_message(self, message_id: int) -> Optional[Dict]:
        """Получение сообщения по ID"""
        query = "SELECT * FROM messages WHERE message_id = $1"
        row = await self._fetchrow(query, message_id)
        return dict(row) if row else None

    async def delete_message(self, message_id: int):
        """Удаление сообщения"""
        query = "DELETE FROM messages WHERE message_id = $1"
        await self._execute(query, message_id)

    async def get_user_rooms_count(self, user_id: int) -> int:
        """Получение количества комнат пользователя"""
        query = "SELECT COUNT(*) FROM room_users WHERE user_id = $1"
        return await self._fetchval(query, user_id)