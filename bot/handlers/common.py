import os
import json
import random
from datetime import timedelta
from django.utils import timezone
from bot import bot
from django.conf import settings
from telebot.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from bot.models import User
from bot.texts import MAIN_TEXT
from bot.keyboards import main_markup, UNIVERSAL_BUTTONS
from .registration import start_registration


def start(message: Message) -> None:
    from bot import logger
    logger.info(f"Start command received from user {message.from_user.id}")
    start_registration(message)


def show_main_menu(message: Message) -> None:
    """Показывает главное меню пользователю"""
    from bot import logger
    logger.info(f"Showing main menu to user {message.from_user.id}")
    bot.send_message(message.chat.id, MAIN_TEXT, reply_markup=main_markup)


def menu_call(call: CallbackQuery) -> None:
    bot.edit_message_text(chat_id=call.message.chat.id, text=MAIN_TEXT, reply_markup=main_markup,
                          message_id=call.message.message_id)

def profile(call: CallbackQuery) -> None:
    """Обработчик профиля"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        profile_text = f"👤 Профиль\n\n"
        profile_text += f"ID: {user.telegram_id}\n"
        profile_text += f"ФИО: {user.full_name or 'Не указано'}\n"
        profile_text += f"Образование: {user.get_education_type_display() or 'Не указано'}\n"
        profile_text += f"Курс/Класс: {user.course_or_class or 'Не указано'}\n"
        profile_text += f"Статус: {'Зарегистрирован' if user.is_registered else 'Не зарегистрирован'}"
        
        bot.edit_message_text(chat_id=call.message.chat.id, text=profile_text, reply_markup=UNIVERSAL_BUTTONS,
                              message_id=call.message.message_id)
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")
