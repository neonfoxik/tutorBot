import hashlib
from bot import bot, logger
from django.conf import settings
from telebot.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)

from bot.models import User


def generate_ref_link(user_id: int) -> str:
    """Генерирует реферальную ссылку для пользователя."""
    # Создаем уникальный хеш на основе user_id
    hash_object = hashlib.md5(str(user_id).encode())
    ref_code = hash_object.hexdigest()[:8]
    return f"https://t.me/{settings.BOT_NAME}?start=ref_{ref_code}"

def handle_ref_link_in_ref_code(message: Message) -> None:
    new_user_id = message.from_user.id
    user_not_ref = User.objects.filter(telegram_id=new_user_id).first()  # Исправлено на .first() для получения объекта
    if user_not_ref and user_not_ref.ref_code:  # Проверяем, существует ли объект и не пустое ли поле ref_code
        ref_code = user_not_ref.ref_code
        for user in User.objects.all():
            hash_object = hashlib.md5(str(user.telegram_id).encode())
            if hash_object.hexdigest()[:8] == ref_code:
                if user.telegram_id != new_user_id:
                    user.coins += 5  # изменть это значение для корректировки стоимости реферальной ссылки
                    user.invited_referals += 1
                    user.save()
                    user_not_ref.ref_code = ''
                    user_not_ref.save()
                    bot.send_message(user.telegram_id,
                                     "Кто-то перешел по вашей реферальной ссылке! Вам начислено 5 монет! 😊")
                    break
                else:
                    bot.send_message(user.telegram_id,
                                     "Вы не можете переходить по своей же реферальной ссылке")
                    break

def handle_ref_link_in_ref_code_call(call: CallbackQuery) -> None:
    new_user_id = call.from_user.id
    user_not_ref = User.objects.filter(telegram_id=new_user_id).first()  # Исправлено на .first() для получения объекта
    if user_not_ref and user_not_ref.ref_code:  # Проверяем, существует ли объект и не пустое ли поле ref_code
        ref_code = user_not_ref.ref_code
        for user in User.objects.all():
            hash_object = hashlib.md5(str(user.telegram_id).encode())
            if hash_object.hexdigest()[:8] == ref_code:
                if user.telegram_id != new_user_id:
                    user.coins += 5  # изменть это значение для корректировки стоимости реферальной ссылки
                    user.invited_referals += 1
                    user.save()
                    user_not_ref.ref_code = ''
                    user_not_ref.save()
                    bot.send_message(user.telegram_id,
                                     "Кто-то перешел по вашей реферальной ссылке! Вам начислено 5 монет! 😊")
                    break
                else:
                    bot.send_message(user.telegram_id,
                                     "Вы не можете переходить по своей же реферальной ссылке")
                    break
def handle_ref_link(message: Message) -> None:
    """Обработчик реферальных ссылок."""
    try:
        # Проверяем, содержит ли сообщение реферальный код
        if 'ref_' not in message.text:
            return

        # Получаем реферальный код из сообщения
        ref_code = message.text.split('ref_')[1]
        new_user_id = message.from_user.id

        # Находим пользователя, который создал ссылку
        for user in User.objects.all():
            hash_object = hashlib.md5(str(user.telegram_id).encode())
            if hash_object.hexdigest()[:8] == ref_code:
                if user.telegram_id != new_user_id:
                    user.coins += 5  # изменть это значение для корректировки стоимости реферальной ссылки
                    user.invited_referals += 1
                    user.save()

                    bot.send_message(user.telegram_id,
                                     "Кто-то перешел по вашей реферальной ссылке! Вам начислено 5 монет! 😊")
                    break
                else:
                    bot.send_message(user.telegram_id,
                                     "Вы не можете переходить по своей же реферальной ссылке")
                    break
    except Exception as e:
        logger.error(f'Ошибка при обработке реферальной ссылки: {e}')

def get_ref_link(callback: CallbackQuery) -> None:
    """Отправляет пользователю его реферальную ссылку."""
    try:
        backMarkup = InlineKeyboardMarkup()
        backMarkup.add(InlineKeyboardButton(text="Назад в меню 🔙", callback_data="main_menu"))
        user_id = callback.from_user.id
        ref_link = generate_ref_link(user_id)

        bot.edit_message_text(chat_id=user_id,
                              message_id=callback.message.id,
                              text=f"Ваша реферальная ссылка:\n{ref_link}\n\nПоделитесь ею с друзьями и получите +5 монет за каждого нового пользователя!",
                              reply_markup=backMarkup
                              )
    except Exception as e:
        logger.error(f'Ошибка при генерации реферальной ссылки: {e}')