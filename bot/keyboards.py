from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def build_main_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🕴 Профиль", callback_data="profile"))
    markup.add(InlineKeyboardButton("💳 Оплата", callback_data="pay"))
    return markup


def build_payment_confirmation_markup(payment_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data=f"payment_i_paid_{payment_id}"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
    return markup


def build_admin_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👥 Клиенты: все", callback_data="admin_list_all"))
    markup.add(InlineKeyboardButton("✅ Оплатившие", callback_data="admin_list_paid"))
    markup.add(InlineKeyboardButton("⏳ Неоплатившие", callback_data="admin_list_unpaid"))
    markup.add(InlineKeyboardButton("💼 Неподтв. платежи", callback_data="admin_pending_payments"))
    markup.add(InlineKeyboardButton("🔔 Отправить напоминания", callback_data="admin_send_reminders"))
    markup.add(InlineKeyboardButton("📣 Рассылка", callback_data="newsletter"))
    return markup


UNIVERSAL_BUTTONS = InlineKeyboardMarkup()
UNIVERSAL_BUTTONS.add(InlineKeyboardButton("Назад👈", callback_data="main_menu"))

UNIVERSAL_VIDEO_MARKUP = InlineKeyboardMarkup()
UNIVERSAL_VIDEO_MARKUP.add(InlineKeyboardButton("Назад👈", callback_data="main_video_menu"))
