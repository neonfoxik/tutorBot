from bot.models import User, StudentProfile
from bot import bot
from django.conf import settings
from bot.keyboards import school_classes_markup, main_markup
from bot.texts import (
    REGISTRATION_WELCOME,
    REGISTRATION_CLASS,
    MAIN_TEXT
)
from telebot.types import CallbackQuery, Message
from django.db import transaction

# Словарь для хранения состояния регистрации пользователей
registration_states = {}

def start_registration(message: Message) -> None:
    """Начинает процесс регистрации пользователя"""
    from bot import logger
    logger.info(f"Starting registration for user {message.from_user.id}")
    telegram_id = str(message.from_user.id)
    
    # Проверяем, зарегистрирован ли уже пользователь
    try:
        user = User.objects.get(telegram_id=telegram_id)
        if user.is_registered:
            # Пользователь уже зарегистрирован, показываем главное меню
            from bot.handlers.common import show_main_menu
            show_main_menu(message)
            return
    except User.DoesNotExist:
        # Создаем нового пользователя
        user = User.objects.create(telegram_id=telegram_id)
    
    # Устанавливаем состояние регистрации
    registration_states[telegram_id] = {
        'step': 'waiting_full_name',
        'user_id': user.telegram_id
    }
    
    # Отправляем первый вопрос
    bot.send_message(message.chat.id, REGISTRATION_WELCOME)

def handle_registration_message(message: Message) -> None:
    """Обрабатывает текстовые сообщения во время регистрации"""
    telegram_id = str(message.from_user.id)
    
    if telegram_id not in registration_states:
        return
    
    state = registration_states[telegram_id]
    
    if state['step'] == 'waiting_full_name':
        # Сохраняем ФИО и переходим к следующему шагу
        full_name = message.text.strip()
        if len(full_name) < 2:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректное имя (минимум 2 символа):")
            return
        
        try:
            user = User.objects.get(telegram_id=telegram_id)
            user.full_name = full_name
            user.save()
            
            # Переходим к выбору класса
            state['step'] = 'waiting_class'
            bot.send_message(message.chat.id, REGISTRATION_CLASS, reply_markup=school_classes_markup)
        except Exception as e:
            bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")
            return

def handle_class_choice(call: CallbackQuery) -> None:
    """Обрабатывает выбор класса"""
    telegram_id = str(call.from_user.id)
    
    if telegram_id not in registration_states:
        return
    
    state = registration_states[telegram_id]
    
    if state['step'] != 'waiting_class':
        return
    
    # Маппинг классов к тарифным планам и уровням
    raw_value = call.data.replace('class_', '')
    education_level = None
    
    if raw_value == '10_base':
        class_number = '10'
        education_level = 'base'
    elif raw_value == '10_profile':
        class_number = '10_profile'
        education_level = 'profile'
    elif raw_value == '11_base':
        class_number = '11'
        education_level = 'base'
    elif raw_value == '11_profile':
        class_number = '11_profile'
        education_level = 'profile'
    else:
        class_number = raw_value
    
    try:
        user = User.objects.get(telegram_id=telegram_id)
        user.class_number = class_number
        user.is_registered = True
        user.save()
        
        # Создаем первый профиль ученика
        with transaction.atomic():
            # Деактивируем все существующие профили
            user.student_profiles.update(is_active=False)
            
            # Создаем новый активный профиль
            profile = StudentProfile.objects.create(
                user=user,
                profile_name=user.full_name or f"Профиль {user.telegram_id}",
                full_name=user.full_name,
                class_number=class_number,
                education_level=education_level,
                is_active=True,
                is_registered=True
            )
        
        # Завершаем регистрацию и показываем главное меню
        from bot.handlers.common import MAIN_TEXT, main_markup
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=MAIN_TEXT,
            reply_markup=main_markup
        )
        
        # Удаляем состояние регистрации
        del registration_states[telegram_id]
        
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")

def start_registration_call(call: CallbackQuery) -> None:
    """Обработчик для кнопки проверки подписки"""
    start_registration(call.message)

# Функция для проверки, находится ли пользователь в процессе регистрации
def is_user_registering(telegram_id: str) -> bool:
    return str(telegram_id) in registration_states