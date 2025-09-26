# handlers/__init__.py
from aiogram import Router

# Главный роутер для объединения всех обработчиков
main_router = Router()

# Импортируем все обработчики (будет настроено в bot.py)