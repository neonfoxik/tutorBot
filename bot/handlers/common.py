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
from bot.models import User, StudentProfile
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
    """Обработчик профиля - перенаправляет в меню профилей"""
    from .profiles import profiles_menu
    profiles_menu(call)
