# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.BOT_TOKEN = self._get_env_var("BOT_TOKEN")
        self.DB_URL = self._get_env_var("DB_URL")
        self.ADMIN_IDS = self._get_admin_ids()

    def _get_env_var(self, var_name: str) -> str:
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Переменная окружения {var_name} не установлена")
        return value

    def _get_admin_ids(self) -> list[int]:
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if not admin_ids_str:
            return []

        try:
            return [int(id.strip()) for id in admin_ids_str.split(",")]
        except ValueError:
            print("⚠️ Ошибка парсинга ADMIN_IDS. Использую пустой список.")
            return []


# Создаем глобальный экземпляр конфига
config = Config()