# handlers/__init__.py
from aiogram import Router

# Создаем главный роутер
main_router = Router()

# Импортируем обработчики из всех модулей
from . import users, rooms, messages

# Включаем все роутеры в главный
main_router.include_router(users.router)
main_router.include_router(rooms.router)
main_router.include_router(messages.router)