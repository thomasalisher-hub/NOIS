# utils/avatars.py
from typing import Tuple
import os
import random
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

# Создаем папку для кеширования аватарок, если её нет
AVATARS_DIR = "data/avatars"
os.makedirs(AVATARS_DIR, exist_ok=True)


def generate_color() -> str:
    """
    Генерирует случайный цвет в HEX-формате.
    Избегаем слишком светлых цветов для лучшей читаемости текста.

    Returns:
        str: HEX-код цвета (например, "#FF5733")
    """
    # Генерируем достаточно яркие, но не белые цвета
    r = random.randint(50, 200)
    g = random.randint(50, 200)
    b = random.randint(50, 200)

    return f"#{r:02X}{g:02X}{b:02X}"


def generate_beautiful_color_pair(nickname: str) -> Tuple[str, str]:
    """
    Генерирует детерминированную пару цветов на основе никнейма.
    Один и тот же никнейм всегда будет иметь одинаковые цвета.
    """
    # Создаем хэш от никнейма для детерминированности
    hash_obj = hashlib.md5(nickname.encode())
    hash_int = int(hash_obj.hexdigest()[:8], 16)

    # Красивые цветовые пары
    color_pairs = [
        ("#667eea", "#764ba2"),  # Синий градиент
        ("#f093fb", "#f5576c"),  # Розово-красный
        ("#4facfe", "#00f2fe"),  # Голубой градиент
        ("#43e97b", "#38f9d7"),  # Зеленый градиент
        ("#fa709a", "#fee140"),  # Оранжево-розовый
        ("#a8edea", "#fed6e3"),  # Пастельный
        ("#d299c2", "#fef9d7"),  # Лавандовый
        ("#89f7fe", "#66a6ff"),  # Аквамарин
        ("#ff9a9e", "#fecfef"),  # Нежный розовый
        ("#a1c4fd", "#c2e9fb"),  # Светло-голубой
        ("#ffecd2", "#fcb69f"),  # Персиковый
        ("#84fab0", "#8fd3f4"),  # Мятно-голубой
    ]

    # Выбираем пару на основе хэша
    pair_index = hash_int % len(color_pairs)
    return color_pairs[pair_index]


def generate_random_color_pair() -> Tuple[str, str]:
    """
    Генерирует случайную пару цветов для градиента.
    Не зависит от никнейма - каждый раз новые цвета.
    """
    # Все доступные цветовые пары
    all_color_pairs = [
        ("#667eea", "#764ba2"),  # Синий градиент
        ("#f093fb", "#f5576c"),  # Розово-красный
        ("#4facfe", "#00f2fe"),  # Голубой градиент
        ("#43e97b", "#38f9d7"),  # Зеленый градиент
        ("#fa709a", "#fee140"),  # Оранжево-розовый
        ("#a8edea", "#fed6e3"),  # Пастельный
        ("#d299c2", "#fef9d7"),  # Лавандовый
        ("#89f7fe", "#66a6ff"),  # Аквамарин
        ("#ff9a9e", "#fecfef"),  # Нежный розовый
        ("#a1c4fd", "#c2e9fb"),  # Светло-голубой
        ("#ffecd2", "#fcb69f"),  # Персиковый
        ("#84fab0", "#8fd3f4"),  # Мятно-голубой
    ]

    # Случайный выбор пары цветов
    return random.choice(all_color_pairs)


def create_gradient_background(size: int, color1: str, color2: str) -> Image.Image:
    """Создает градиентный фон максимального качества"""
    # Увеличиваем размер для супер-качества
    super_size = size * 4  # Рендерим в 4 раза больше

    image = Image.new("RGBA", (super_size, super_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Создаем радиальный градиент с плавными переходами
    center_x, center_y = super_size // 2, super_size // 2
    max_radius = int(math.sqrt(center_x ** 2 + center_y ** 2))

    # Оптимизированный алгоритм с плавными переходами
    steps = min(200, max_radius)  # Ограничиваем количество шагов для производительности

    for i in range(steps):
        radius = max_radius * (1 - i / steps)
        ratio = i / steps

        # Плавная интерполяция цветов
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        r = int(r1 * (1 - ratio) + r2 * ratio)
        g = int(g1 * (1 - ratio) + g2 * ratio)
        b = int(b1 * (1 - ratio) + b2 * ratio)

        color = f"#{r:02x}{g:02x}{b:02x}"
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], fill=color)

    # Уменьшаем до целевого размера с премиальным антиалиасингом
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image


def get_avatar_filename(nickname: str, size: int) -> str:
    """Генерирует имя файла аватарки на основе никнейма и размера"""
    safe_nickname = "".join(c for c in nickname if c.isalnum() or c in ('-', '_'))
    # Добавляем хэш для уникальности и кеширования
    content_hash = hashlib.md5(f"{nickname}_{size}".encode()).hexdigest()[:8]
    return f"{safe_nickname}_{content_hash}.png"


def create_beautiful_avatar(nickname: str, size: int = 512, force_regenerate: bool = False) -> Tuple[str, str]:
    """
    Создает или возвращает существующую красивую аватарку.

    Args:
        nickname: Никнейм пользователя
        size: Размер аватарки (рекомендуется 512 или 1024)
        force_regenerate: Принудительно перегенерировать аватарку

    Returns:
        Tuple[str, str]: (путь к файлу, основной цвет)
    """
    # Генерируем имя файла
    filename = get_avatar_filename(nickname, size)
    filepath = os.path.join(AVATARS_DIR, filename)

    # Если аватарка уже существует и не нужно пересоздавать - возвращаем её
    if not force_regenerate and os.path.exists(filepath):
        color1, _ = generate_beautiful_color_pair(nickname)
        return filepath, color1

    # Извлекаем первую букву никнейма (в верхнем регистре)
    first_letter = nickname[0].upper()

    # Увеличиваем размер для максимального качества
    scale_factor = 4  # Рендерим в 4 раза больше
    render_size = size * scale_factor

    # Генерируем детерминированные цвета
    color1, color2 = generate_beautiful_color_pair(nickname)

    # Создаем градиентный фон максимального качества
    gradient_bg = create_gradient_background(render_size, color1, color2)

    # Добавляем тень с размытием
    shadow_size = render_size + 80
    shadow = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    # Рисуем тень с градиентом
    shadow_radius = shadow_size // 2
    for i in range(50, 0, -5):
        alpha = max(5, 50 - i)
        shadow_draw.ellipse([
            shadow_radius - i, shadow_radius - i,
            shadow_radius + i, shadow_radius + i
        ], fill=(0, 0, 0, alpha))

    shadow = shadow.filter(ImageFilter.GaussianBlur(25))

    # Собираем финальное изображение
    final_image = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
    final_image.paste(shadow, (0, 0), shadow)

    # Размещаем градиент по центру
    gradient_pos = (shadow_size - render_size) // 2
    final_image.paste(gradient_bg, (gradient_pos, gradient_pos), gradient_bg)

    # Рисуем букву с максимальным качеством
    try:
        # Используем большой размер шрифта для качества
        font_size = int(render_size * 0.6)

        # Пробуем разные шрифты
        font_paths = [
            "arialbd.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\Arial\\arialbd.ttf",
            "/System/Library/Fonts/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]

        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue

        if font is None:
            # Fallback на стандартный шрифт
            font = ImageFont.load_default()

    except Exception as e:
        font = ImageFont.load_default()

    # Рисуем букву по центру
    center_x, center_y = shadow_size // 2, shadow_size // 2
    draw_final = ImageDraw.Draw(final_image)

    # Тень текста для лучшей читаемости
    shadow_offset = int(render_size * 0.02)  # 2% от размера
    shadow_color = (0, 0, 0, 120)
    draw_final.text(
        (center_x + shadow_offset, center_y + shadow_offset),
        first_letter,
        fill=shadow_color,
        font=font,
        anchor="mm"
    )

    # Основной текст
    text_color = (255, 255, 255, 255)
    draw_final.text((center_x, center_y), first_letter, fill=text_color, font=font, anchor="mm")

    # Уменьшаем до целевого размера с премиальным антиалиасингом
    final_image = final_image.resize((size, size), Image.Resampling.LANCZOS)

    # Сохраняем с максимальным качеством
    final_image.save(filepath, "PNG", optimize=True, quality=95)
    return filepath, color1


def create_random_avatar(nickname: str, size: int = 512) -> Tuple[str, str]:
    """
    Создает аватарку со СЛУЧАЙНЫМИ цветами градиента.
    Цвета не зависят от никнейма - каждый раз новые.
    """
    first_letter = nickname[0].upper()

    # Увеличиваем размер для качества
    scale_factor = 4
    render_size = size * scale_factor

    # Генерируем СЛУЧАЙНЫЕ цвета (не зависящие от никнейма)
    color1, color2 = generate_random_color_pair()

    # Создаем градиентный фон
    gradient_bg = create_gradient_background(render_size, color1, color2)

    # Добавляем тень с размытием
    shadow_size = render_size + 80
    shadow = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    # Рисуем тень
    shadow_radius = shadow_size // 2
    for i in range(50, 0, -5):
        alpha = max(5, 50 - i)
        shadow_draw.ellipse([
            shadow_radius - i, shadow_radius - i,
            shadow_radius + i, shadow_radius + i
        ], fill=(0, 0, 0, alpha))

    shadow = shadow.filter(ImageFilter.GaussianBlur(25))

    # Собираем финальное изображение
    final_image = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
    final_image.paste(shadow, (0, 0), shadow)
    final_image.paste(gradient_bg, (40, 40), gradient_bg)  # 40 = (shadow_size - render_size) // 2

    # Рисуем букву
    try:
        font_size = int(render_size * 0.6)
        font_paths = [
            "arialbd.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "/System/Library/Fonts/Arial Bold.ttf",
        ]

        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
    except Exception as e:
        font = ImageFont.load_default()

    # Рисуем букву по центру
    center_x, center_y = shadow_size // 2, shadow_size // 2
    draw_final = ImageDraw.Draw(final_image)

    # Тень текста
    shadow_offset = int(render_size * 0.02)
    draw_final.text(
        (center_x + shadow_offset, center_y + shadow_offset),
        first_letter,
        fill=(0, 0, 0, 120),
        font=font,
        anchor="mm"
    )

    # Основной текст
    draw_final.text((center_x, center_y), first_letter, fill="white", font=font, anchor="mm")

    # Уменьшаем до целевого размера
    final_image = final_image.resize((size, size), Image.Resampling.LANCZOS)

    # Сохраняем с уникальным именем (добавляем timestamp для уникальности)
    import time
    safe_nickname = "".join(c for c in nickname if c.isalnum() or c in ('-', '_'))
    timestamp = int(time.time())
    filename = f"{safe_nickname}_{timestamp}.png"
    filepath = os.path.join(AVATARS_DIR, filename)

    final_image.save(filepath, "PNG", optimize=True, quality=95)
    return filepath, color1


def get_user_avatar(nickname: str, size: int = 512) -> Tuple[str, str]:
    """
    Получает аватарку пользователя (из кеша или создает новую).
    Используется для обычного показа аватарки.
    """
    return create_beautiful_avatar(nickname, size, force_regenerate=False)


def regenerate_user_avatar(nickname: str, size: int = 512) -> Tuple[str, str]:
    """
    Принудительно пересоздает аватарку пользователя.
    Используется когда пользователь хочет новую аватарку.
    """
    return create_beautiful_avatar(nickname, size, force_regenerate=True)


def regenerate_user_avatar_random(nickname: str, size: int = 512) -> Tuple[str, str]:
    """
    Принудительно пересоздает аватарку со СЛУЧАЙНЫМИ цветами.
    Для команды /avatar - каждый раз новые цвета градиента.
    """
    return create_random_avatar(nickname, size)


def hex_to_rgb(color_hex: str) -> Tuple[int, int, int]:
    """Конвертирует HEX-цвет в RGB."""
    color_hex = color_hex.lstrip('#')
    return tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4))


# Функция для совместимости со старым кодом
def create_avatar(nickname: str, color_hex: str = None, size: int = 512) -> str:
    """Совместимость со старым кодом"""
    avatar_path, _ = get_user_avatar(nickname, size)
    return avatar_path


# Тестируем функцию если файл запущен напрямую
if __name__ == "__main__":
    print("=== ТЕСТ АВАТАРОК МАКСИМАЛЬНОГО КАЧЕСТВА ===")
    print(f"Папка для аватарок: {os.path.abspath(AVATARS_DIR)}")

    test_nicks = ["HappyFox123", "BraveDragon42", "SwiftWolf99"]

    for i, nick in enumerate(test_nicks):
        # Тестируем кеширование
        print(f"\n{i + 1}. Тестируем ник: {nick}")

        # Первое создание
        avatar_path1, color1 = get_user_avatar(nick, size=512)
        print(f"   Создана аватарка 512x512: {os.path.basename(avatar_path1)}")

        # Второй запрос - должна вернуться из кеша
        avatar_path2, color2 = get_user_avatar(nick, size=512)
        print(f"   Из кеша: {os.path.basename(avatar_path2)}")
        print(f"   Пути совпадают: {avatar_path1 == avatar_path2}")

        # Принудительное пересоздание
        avatar_path3, color3 = regenerate_user_avatar(nick, size=512)
        print(f"   Пересоздана: {os.path.basename(avatar_path3)}")
        print(f"   Цвет: {color1}")

        # Тестируем случайные аватарки
        avatar_path4, color4 = regenerate_user_avatar_random(nick, size=512)
        print(f"   Случайная: {os.path.basename(avatar_path4)}")
        print(f"   Случайный цвет: {color4}")

    print(f"\n=== ТЕСТ ЗАВЕРШЕН ===")
    print("Аватарки сохранены в папке data/avatars/")