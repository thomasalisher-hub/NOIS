# utils/nick_generator.py
import random

# Расширенные списки для генерации креативных ников
ADJECTIVES = [
    # Основные прилагательные
    "Happy", "Swift", "Clever", "Brave", "Calm", "Daring", "Eager", "Gentle",
    "Jolly", "Lucky", "Mighty", "Proud", "Silent", "Witty", "Young", "Bright",
    "Cool", "Fierce", "Golden", "Noble", "Quick", "Solar", "Urban", "Vivid",

    # Природа и стихии
    "Ancient", "Blazing", "Cosmic", "Crimson", "Crystal", "Diamond", "Eternal",
    "Frozen", "Galactic", "Golden", "Infernal", "Lunar", "Mystic", "Oceanic",
    "Radiant", "Sapphire", "Solar", "Thunder", "Volcanic", "Wild", "Arctic",
    "Blizzard", "Cyclone", "Desert", "Forest", "Mountain", "River", "Tropical",

    # Технологии и наука
    "Atomic", "Binary", "Cyber", "Digital", "Electronic", "Future", "Hyper",
    "Neon", "Quantum", "Robotic", "Synth", "Virtual", "Android", "Nano",
    "Pixel", "Code", "Data", "AI", "Machine", "Network", "Cyber", "Digital",

    # Мистика и фэнтези
    "Arcane", "Celestial", "Dark", "Divine", "Dragon", "Enchanted", "Ethereal",
    "Ghost", "Magic", "Phantom", "Shadow", "Spectral", "Spirit", "Undead",
    "Vampire", "Wizard", "Mythic", "Legend", "Epic", "Heroic", "Mystic",

    # Цвета и свет
    "Azure", "Amber", "Ebony", "Emerald", "Ivory", "Jade", "Onyx", "Ruby",
    "Silver", "Violet", "Amethyst", "Topaz", "Bronze", "Copper", "Platinum",

    # Абстрактные понятия
    "Abstract", "Chaos", "Dream", "Echo", "Infinite", "Nova", "Omega", "Prime",
    "Random", "Secret", "Ultimate", "Velocity", "Zen", "Alpha", "Omega"
]

NOUNS = [
    # Животные и существа
    "Fox", "Wolf", "Eagle", "Lion", "Tiger", "Bear", "Hawk", "Shark", "Dragon",
    "Falcon", "Owl", "Panther", "Rabbit", "Deer", "Horse", "Whale", "Phoenix",
    "Griffin", "Unicorn", "Pegasus", "Basilisk", "Kraken", "Yeti", "Manticore",

    # Профессии и роли
    "Knight", "Wizard", "Warrior", "Explorer", "Pioneer", "Traveler", "Hunter",
    "Guardian", "Samurai", "Ninja", "Viking", "Pirate", "Astronaut", "Detective",
    "Scientist", "Engineer", "Artist", "Musician", "Explorer", "Vision", "Dreamer",
    "Thinker", "Creator", "Builder", "Coder", "Pilot", "Captain", "Agent",

    # Технологии
    "Byte", "Code", "Data", "Chip", "Node", "Net", "Cloud", "AI", "Bot", "Drone",
    "Robot", "Android", "Cyborg", "Program", "Algorithm", "Server", "Database",
    "Firewall", "Protocol", "Interface", "Widget", "Gadget", "Device",

    # Космос и наука
    "Star", "Planet", "Comet", "Nova", "Orbit", "Galaxy", "Quasar", "Pulsar",
    "Nebula", "BlackHole", "Asteroid", "Cosmos", "Universe", "Dimension", "Quantum",
    "Atom", "Proton", "Neutron", "Electron", "Molecule", "Element", "Compound",

    # Мифология и легенды
    "Titan", "God", "Deity", "Spirit", "Demon", "Angel", "Genie", "Djinn",
    "Valkyrie", "Centaur", "Minotaur", "Sphinx", "Hydra", "Leviathan", "Behemoth",

    # Природа и стихии
    "Storm", "Blaze", "Flame", "Ice", "Water", "Earth", "Stone", "Mountain",
    "River", "Ocean", "Forest", "Desert", "Volcano", "Tsunami", "Hurricane",
    "Aurora", "Rainbow", "Lightning", "Thunder", "Cyclone", "Typhoon",

    # Абстрактные понятия
    "Chaos", "Order", "Time", "Space", "Reality", "Dream", "Nightmare", "Vision",
    "Echo", "Shadow", "Light", "Dark", "Balance", "Force", "Energy", "Power",
    "Wisdom", "Knowledge", "Secret", "Mystery", "Puzzle", "Riddle", "Enigma",

    # Оружие и артефакты
    "Blade", "Sword", "Shield", "Bow", "Arrow", "Axe", "Hammer", "Spear",
    "Dagger", "Staff", "Wand", "Orb", "Crystal", "Amulet", "Talisman", "Relic",
    "Artifact", "Treasure", "Gold", "Silver", "Diamond", "Ruby", "Emerald"
]

# Специализированные тематические наборы
TECH_NOUNS = [
    "Algorithm", "Blockchain", "Firewall", "Framework", "Function", "Hash",
    "Iterator", "Kernel", "Lambda", "Matrix", "Network", "Protocol", "Query",
    "Script", "Syntax", "Template", "Variable", "Vector", "Zip", "Cache"
]

MYTHICAL_NOUNS = [
    "Basilisk", "Cerberus", "Chimera", "Fenrir", "Griffin", "Hippogriff",
    "Kraken", "Leviathan", "Phoenix", "Sphinx", "Thunderbird", "Wyvern",
    "Zombie", "Golem", "Banshee", "Doppelganger", "Ghost", "Poltergeist"
]

SPACE_NOUNS = [
    "Asteroid", "BlackHole", "Comet", "Constellation", "Crater", "Eclipse",
    "Galaxy", "Meteor", "Nebula", "Orbit", "Planet", "Quasar", "Rocket",
    "Satellite", "Supernova", "Telescope", "Universe", "Wormhole"
]

FANTASY_NOUNS = [
    "Amulet", "Castle", "Dungeon", "Elixir", "Forest", "Goblin", "Hydra",
    "Island", "Jewel", "Kingdom", "Labyrinth", "Monster", "Necromancer",
    "Obelisk", "Portal", "Quest", "Ruins", "Spell", "Tower", "Undead"
]

GAMING_NOUNS = [
    "Avatar", "Boss", "Character", "Damage", "Experience", "Game", "Health",
    "Item", "Jump", "Kill", "Level", "Mission", "NPC", "Quest", "Rank",
    "Skill", "Target", "Upgrade", "Victory", "Weapon", "XP", "Zone"
]

# Дополнительные прилагательные для комбинаций
PREFIXES = [
    "Alpha", "Beta", "Gamma", "Delta", "Omega", "Sigma", "Theta", "Zeta",
    "Cyber", "Hyper", "Mega", "Super", "Ultra", "Multi", "Omni", "Poly",
    "Neo", "Proto", "Retro", "Techno", "Digital", "Virtual", "Quantum"
]

SUFFIXES = [
    "Master", "Lord", "King", "Queen", "Prince", "Princess", "Warrior", "Mage",
    "Expert", "Pro", "Elite", "Legend", "Champion", "Hero", "Veteran", "Novice",
    "Builder", "Maker", "Creator", "Designer", "Artist", "Writer", "Coder"
]


def generate_nickname() -> str:
    """
    Генерирует случайный никнейм с улучшенной логикой комбинирования.
    Примеры: "QuantumShadow", "NeonDragon42", "CyberPhoenix", "MysticTraveler"

    Returns:
        str: Сгенерированный никнейм
    """
    # Выбираем основную схему генерации
    scheme = random.choice([
        "adjective_noun",  # Прилагательное + Существительное
        "prefix_noun",  # Префикс + Существительное
        "adjective_suffix",  # Прилагательное + Суффикс
        "theme_noun",  # Тематическое существительное
        "double_adjective",  # Двойное прилагательное
        "mythical_creature"  # Мифическое существо
    ])

    if scheme == "adjective_noun":
        adjective = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        nickname = f"{adjective}{noun}"

    elif scheme == "prefix_noun":
        prefix = random.choice(PREFIXES)
        noun = random.choice(NOUNS)
        nickname = f"{prefix}{noun}"

    elif scheme == "adjective_suffix":
        adjective = random.choice(ADJECTIVES)
        suffix = random.choice(SUFFIXES)
        nickname = f"{adjective}{suffix}"

    elif scheme == "theme_noun":
        # Выбираем тематическую группу
        theme = random.choice(["tech", "space", "fantasy", "gaming", "mythical"])
        if theme == "tech":
            noun = random.choice(TECH_NOUNS)
        elif theme == "space":
            noun = random.choice(SPACE_NOUNS)
        elif theme == "fantasy":
            noun = random.choice(FANTASY_NOUNS)
        elif theme == "gaming":
            noun = random.choice(GAMING_NOUNS)
        else:
            noun = random.choice(MYTHICAL_NOUNS)

        # Добавляем прилагательное с вероятностью 70%
        if random.random() < 0.7:
            adjective = random.choice(ADJECTIVES)
            nickname = f"{adjective}{noun}"
        else:
            nickname = noun

    elif scheme == "double_adjective":
        adj1 = random.choice(ADJECTIVES)
        adj2 = random.choice(ADJECTIVES)
        while adj2 == adj1:  # Избегаем повторений
            adj2 = random.choice(ADJECTIVES)
        nickname = f"{adj1}{adj2}"

    else:  # mythical_creature
        creature = random.choice(MYTHICAL_NOUNS)
        # Добавляем эпитет с вероятностью 60%
        if random.random() < 0.6:
            adjective = random.choice(ADJECTIVES)
            nickname = f"{adjective}{creature}"
        else:
            nickname = creature

    # Добавляем число с вероятностью 40%
    if random.random() < 0.4:
        # Выбираем формат числа
        number_format = random.choice([
            lambda: random.randint(1, 999),  # 42
            lambda: random.randint(1000, 9999),  # 2042
            lambda: random.randint(1970, 2025),  # 2023
            lambda: int(str(random.randint(1, 99)) + str(random.randint(0, 99))),  # 1337
        ])
        number = number_format()
        nickname = f"{nickname}{number}"

    # Иногда добавляем специальные символы (10% случаев)
    if random.random() < 0.1:
        symbol = random.choice(["X", "Z", "Pro", "Max", "HD", "VR", "AI"])
        nickname = f"{nickname}{symbol}"

    # Обеспечиваем длину никнейма в пределах 3-20 символов
    if len(nickname) > 20:
        nickname = nickname[:20]
    elif len(nickname) < 3:
        nickname = nickname + str(random.randint(10, 99))

    return nickname


def generate_themed_nickname(theme: str) -> str:
    """
    Генерирует никнейм определенной тематики.

    Args:
        theme: tech, space, fantasy, gaming, mythical

    Returns:
        str: Тематический никнейм
    """
    themes = {
        "tech": (TECH_NOUNS, "Cyber", "Net"),
        "space": (SPACE_NOUNS, "Cosmic", "Star"),
        "fantasy": (FANTASY_NOUNS, "Magic", "Dragon"),
        "gaming": (GAMING_NOUNS, "Game", "Player"),
        "mythical": (MYTHICAL_NOUNS, "Ancient", "Mythic")
    }

    if theme not in themes:
        return generate_nickname()

    nouns, default_adj1, default_adj2 = themes[theme]

    # Выбираем схему для тематического ника
    scheme = random.choice([1, 2, 3])

    if scheme == 1:
        # Прилагательное + Тематическое существительное
        adjective = random.choice(ADJECTIVES + [default_adj1, default_adj2])
        noun = random.choice(nouns)
        nickname = f"{adjective}{noun}"
    elif scheme == 2:
        # Тематическое существительное + число
        noun = random.choice(nouns)
        nickname = f"{noun}{random.randint(1, 999)}"
    else:
        # Двойное тематическое
        part1 = random.choice([default_adj1, default_adj2, random.choice(ADJECTIVES)])
        part2 = random.choice(nouns)
        nickname = f"{part1}{part2}"

    return nickname


def generate_multiple_nicks(count: int = 5, theme: str = None) -> list:
    """
    Генерирует несколько вариантов ников для выбора.

    Args:
        count (int): Количество вариантов
        theme (str): Тематика (tech, space, fantasy, gaming, mythical)

    Returns:
        list: Список никнеймов
    """
    nicks = []
    for _ in range(count):
        if theme:
            nick = generate_themed_nickname(theme)
        else:
            nick = generate_nickname()
        nicks.append(nick)
    return nicks


def get_nickname_themes() -> list:
    """Возвращает список доступных тематик"""
    return ["tech", "space", "fantasy", "gaming", "mythical", "random"]


# Тестируем функцию если файл запущен напрямую
if __name__ == "__main__":
    print("=== ТЕСТ УЛУЧШЕННОГО ГЕНЕРАТОРА НИКНЕЙМОВ ===")

    print("\n🎲 10 случайных ников:")
    for i in range(10):
        nick = generate_nickname()
        print(f"{i + 1}. {nick}")

    print("\n🚀 5 космических ников:")
    for i, nick in enumerate(generate_multiple_nicks(5, "space"), 1):
        print(f"{i}. {nick}")

    print("\n💻 5 технологических ников:")
    for i, nick in enumerate(generate_multiple_nicks(5, "tech"), 1):
        print(f"{i}. {nick}")

    print("\n🐉 5 фэнтезийных ников:")
    for i, nick in enumerate(generate_multiple_nicks(5, "fantasy"), 1):
        print(f"{i}. {nick}")

    print("\n🎮 5 игровых ников:")
    for i, nick in enumerate(generate_multiple_nicks(5, "gaming"), 1):
        print(f"{i}. {nick}")

    print(f"\n📊 Всего вариантов прилагательных: {len(ADJECTIVES)}")
    print(f"📊 Всего вариантов существительных: {len(NOUNS)}")
    print(f"🎯 Доступные тематики: {', '.join(get_nickname_themes())}")