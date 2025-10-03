from telebot.types import Message, CallbackQuery
from bot import bot
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.models import User, StudentProfile
from bot.handlers.registration import start_registration


def start(message: Message) -> None:
    """Обработчик команды /start"""
    telegram_id = str(message.from_user.id)
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = User.objects.get(telegram_id=telegram_id)
        
        # Проверяем, есть ли у пользователя хотя бы один профиль
        if not user.student_profiles.exists():
            # Если нет профилей, отправляем на регистрацию
            start_registration(message)
            return
        
        # Если есть профили, показываем главное меню
        bot.send_message(message.chat.id, MAIN_TEXT, reply_markup=main_markup)
        
    except User.DoesNotExist:
        # Если пользователя нет в базе, отправляем на регистрацию
        start_registration(message)


def show_main_menu(message: Message) -> None:
    """Показывает главное меню"""
    telegram_id = str(message.from_user.id)
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = User.objects.get(telegram_id=telegram_id)
        
        # Проверяем, есть ли у пользователя хотя бы один профиль
        if not user.student_profiles.exists():
            # Если нет профилей, отправляем на регистрацию
            start_registration(message)
            return
        
        # Если есть профили, показываем главное меню
        bot.send_message(message.chat.id, MAIN_TEXT, reply_markup=main_markup)
        
    except User.DoesNotExist:
        # Если пользователя нет в базе, отправляем на регистрацию
        start_registration(message)


def menu_call(call: CallbackQuery) -> None:
    """Обработчик для возврата в главное меню"""
    telegram_id = str(call.from_user.id)
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = User.objects.get(telegram_id=telegram_id)
        
        # Проверяем, есть ли у пользователя хотя бы один профиль
        if not user.student_profiles.exists():
            # Если нет профилей, отправляем на регистрацию
            start_registration(call.message)
            return
        
        # Если есть профили, показываем главное меню
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=MAIN_TEXT,
                reply_markup=main_markup
            )
        except Exception:
            # Если не удалось отредактировать сообщение, отправляем новое
            bot.send_message(
                chat_id=call.message.chat.id,
                text=MAIN_TEXT,
                reply_markup=main_markup
            )
        
    except User.DoesNotExist:
        # Если пользователя нет в базе, отправляем на регистрацию
        start_registration(call.message)