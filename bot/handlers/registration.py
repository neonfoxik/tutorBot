from bot.models import User
from bot import bot
from django.conf import settings
from bot.keyboards import (
    education_choice_markup, 
    university_courses_markup, 
    school_classes_markup
)
from bot.texts import (
    REGISTRATION_WELCOME, 
    REGISTRATION_EDUCATION, 
    REGISTRATION_UNIVERSITY_COURSE, 
    REGISTRATION_SCHOOL_CLASS, 
    REGISTRATION_COMPLETE
)
from telebot.types import CallbackQuery, Message
from django.db import transaction

# Словарь для хранения состояния регистрации пользователей
registration_states = {}

def start_registration(message: Message) -> None:
    """Начинает процесс регистрации пользователя"""
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
            
            # Переходим к выбору места учебы
            state['step'] = 'waiting_education_choice'
            bot.send_message(message.chat.id, REGISTRATION_EDUCATION, reply_markup=education_choice_markup)
        except Exception as e:
            bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте еще раз.")
            return

def handle_education_choice(call: CallbackQuery) -> None:
    """Обрабатывает выбор места учебы"""
    telegram_id = str(call.from_user.id)
    
    if telegram_id not in registration_states:
        return
    
    state = registration_states[telegram_id]
    
    if state['step'] != 'waiting_education_choice':
        return
    
    education_type = call.data.replace('education_', '')
    
    try:
        user = User.objects.get(telegram_id=telegram_id)
        user.education_type = education_type
        user.save()
        
        # Переходим к выбору курса или класса
        state['step'] = 'waiting_course_or_class'
        
        if education_type == 'university':
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=REGISTRATION_UNIVERSITY_COURSE,
                reply_markup=university_courses_markup
            )
        else:  # school
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=REGISTRATION_SCHOOL_CLASS,
                reply_markup=school_classes_markup
            )
    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")

def handle_course_or_class_choice(call: CallbackQuery) -> None:
    """Обрабатывает выбор курса или класса"""
    telegram_id = str(call.from_user.id)
    
    if telegram_id not in registration_states:
        return
    
    state = registration_states[telegram_id]
    
    if state['step'] != 'waiting_course_or_class':
        return
    
    course_or_class = call.data.replace('course_', '').replace('class_', '')
    
    try:
        user = User.objects.get(telegram_id=telegram_id)
        user.course_or_class = course_or_class
        user.is_registered = True
        user.save()
        
        # Завершаем регистрацию
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=REGISTRATION_COMPLETE
        )
        
        # Показываем главное меню
        from bot.handlers.common import show_main_menu
        show_main_menu(call.message)
        
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