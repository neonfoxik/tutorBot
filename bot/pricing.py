# Конфигурация цен для разных классов обучения

PRICING_CONFIG = {
    # Младшие классы (5-6)
    '5': {
        'name': '5 класс',
        'price': 2950,
        'description': '1 час / 1 раз в нед',
        'keywords': ['5', '5 класс']
    },
    '6': {
        'name': '6 класс',
        'price': 2950,
        'description': '1 час / 1 раз в нед',
        'keywords': ['6', '6 класс']
    },

    # 7 класс
    '7': {
        'name': '7 класс',
        'price': 5650,
        'description': '2 часа / 1 раз в нед',
        'keywords': ['7', '7 класс']
    },

    # 8 класс
    '8': {
        'name': '8 класс (Алгебра + Геометрия)',
        'price': 5650,
        'description': '2 часа / 1 раз в нед',
        'keywords': ['8', '8 класс']
    },

    # 9 класс ОГЭ
    '9': {
        'name': 'ОГЭ (9 класс)',
        'price': 5650,
        'description': '4 раза по 2 часа',
        'keywords': ['9', '9 класс']
    },

    # 10 класс
    '10': {
        'name': '10 класс (База)',
        'price': 5650,
        'description': '4 раза по 2 часа',
        'keywords': ['10', '10 класс']
    },
    '10_profile': {
        'name': '10 класс (Профиль)',
        'price': 7000,
        'description': '3 часа в нед',
        'keywords': ['10_profile']
    },

    # 11 класс
    '11': {
        'name': '11 класс (База)',
        'price': 5650,
        'description': '4 раза по 2 часа',
        'keywords': ['11', '11 класс']
    },
    '11_profile': {
        'name': '11 класс (Профиль)',
        'price': 7900,
        'description': '4 часа в нед + дом.зад + возможно Зум онлайн занятие 1 раз/нед',
        'keywords': ['11_profile']
    }
}

def get_price_by_class(class_info):
    """
    Получить цену по информации о классе пользователя
    
    Args:
        class_info (str): Информация о классе пользователя
    
    Returns:
        dict: Словарь с информацией о цене или None если не найдено
    """
    if not class_info:
        return None
    
    # Проверяем точное совпадение
    if class_info in PRICING_CONFIG:
        price_data = PRICING_CONFIG[class_info]
        return {
            'key': class_info,
            'name': price_data['name'],
            'price': price_data['price'],
            'description': price_data['description']
        }
    
    # Если точного совпадения нет, ищем по ключевым словам
    class_info_lower = class_info.lower().strip()
    for price_key, price_data in PRICING_CONFIG.items():
        for keyword in price_data['keywords']:
            if keyword in class_info_lower:
                return {
                    'key': price_key,
                    'name': price_data['name'],
                    'price': price_data['price'],
                    'description': price_data['description']
                }
    
    return None

def get_all_price_options():
    """
    Получить все доступные варианты цен
    
    Returns:
        list: Список всех ценовых планов
    """
    return [
        {
            'key': key,
            'name': data['name'],
            'price': data['price'],
            'description': data['description']
        }
        for key, data in PRICING_CONFIG.items()
    ]