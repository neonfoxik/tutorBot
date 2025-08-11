import logging
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.models import User
from bot import bot
from bot.handlers.brief import start_brief


def start_registration(message: Message | CallbackQuery):
    """Начинает процесс регистрации нового пользователя"""
    try:
        if isinstance(message, Message):
            user_id = str(message.from_user.id)
            msg = message
        else:
            user_id = str(message.from_user.id)
            msg = message.message
        
        user, created = User.objects.get_or_create(
            telegram_id=user_id,
            defaults={
                'user_tg_name': message.from_user.username or 'none',
                'user_name': message.from_user.first_name or 'Без имени',
            }
        )
        
        if created or not user.full_name or not user.school or not user.grade:
            # Новый пользователь или незавершенная регистрация - начинаем регистрацию
            start_registration_flow(msg, user)
        else:
            # Существующий пользователь с заполненными полями - показываем главное меню
            from bot.handlers.common import start as start_handler
            start_handler(msg)
            
    except Exception as e:
        logging.error(f"Ошибка в start_registration: {e}")
        if isinstance(message, Message):
            bot.reply_to(message, "❌ Произошла ошибка при регистрации. Попробуйте позже.")
        else:
            bot.answer_callback_query(message.id, "❌ Произошла ошибка при регистрации")


def start_registration_flow(message: Message, user: User):
    """Начинает пошаговый процесс регистрации"""
    try:
        # Определяем, с какого шага начинать регистрацию
        if not user.full_name:
            # Начинаем с ФИО
            welcome_text = (
                "🎉 <b>Добро пожаловать в TutorBot!</b>\n\n"
                "Для начала работы нам нужно узнать немного о вас.\n"
                "Давайте заполним ваш профиль пошагово.\n\n"
                "Пожалуйста, введите ваше полное ФИО:"
            )
            next_step = handle_full_name
        elif not user.school:
            # Продолжаем со школы/вуза
            welcome_text = (
                f"✅ ФИО: {user.full_name}\n\n"
                "Теперь укажите название вашей школы или вуза:"
            )
            next_step = handle_school
        elif not user.grade:
            # Продолжаем с класса/курса
            welcome_text = (
                f"✅ ФИО: {user.full_name}\n"
                f"✅ Школа/ВУЗ: {user.school}\n\n"
                "Укажите ваш класс или курс (например: '10 класс' или '2 курс'):"
            )
            next_step = handle_grade
        else:
            # Все заполнено - показываем главное меню
            from bot.handlers.common import start as start_handler
            start_handler(message)
            return
        
        # Если это callback query, сначала отвечаем на него
        if hasattr(message, 'id') and hasattr(message, 'answer_callback_query'):
            bot.answer_callback_query(message.id)
        
        msg = bot.reply_to(
            message,
            welcome_text,
            parse_mode='HTML'
        )
        
        # Регистрируем следующий шаг
        bot.register_next_step_handler(msg, next_step, user)
        
    except Exception as e:
        logging.error(f"Ошибка в start_registration_flow: {e}")
        bot.reply_to(message, "❌ Произошла ошибка. Попробуйте позже.")


def handle_full_name(message: Message, user: User):
    """Обрабатывает ввод ФИО и запрашивает школу/вуз"""
    try:
        # Проверяем минимальную длину ФИО
        if len(message.text.split()) < 2:
            msg = bot.reply_to(
                message,
                "⚠️ Пожалуйста, введите полное ФИО (минимум имя и фамилия):"
            )
            bot.register_next_step_handler(msg, handle_full_name, user)
            return

        user.full_name = message.text
        user.save()
        
      
        msg = bot.reply_to(
            message,
            "✅ ФИО сохранено!\n\n"
            "Теперь укажите название вашей школы или вуза:",
        )
        
        # Регистрируем следующий шаг для получения школы/вуза
        bot.register_next_step_handler(msg, handle_school, user)
        
    except Exception as e:
        logging.error(f"Ошибка в handle_full_name: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при сохранении ФИО")


def handle_school(message: Message, user: User):
    """Обрабатывает ввод школы/вуза и запрашивает класс/курс"""
    try:
        if len(message.text) < 3:
            msg = bot.reply_to(
                message,
                "⚠️ Пожалуйста, введите корректное название учебного заведения:"
            )
            bot.register_next_step_handler(msg, handle_school, user)
            return

        user.school = message.text
        user.save()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Отменить регистрацию", callback_data="cancel_registration"))
        
        msg = bot.reply_to(
            message,
            "✅ Учебное заведение сохранено!\n\n"
            "Укажите ваш класс или курс (например: '10 класс' или '2 курс'):",
            reply_markup=markup
        )
        
        # Регистрируем следующий шаг для получения класса/курса
        bot.register_next_step_handler(msg, handle_grade, user)
        
    except Exception as e:
        logging.error(f"Ошибка в handle_school: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при сохранении учебного заведения")


def handle_grade(message: Message, user: User):
    """Обрабатывает ввод класса/курса и завершает регистрацию"""
    try:
        if len(message.text) < 2:
            msg = bot.reply_to(
                message,
                "⚠️ Пожалуйста, укажите корректный класс или курс:"
            )
            bot.register_next_step_handler(msg, handle_grade, user)
            return

        user.grade = message.text
        user.save()
        
        # Регистрация завершена, предлагаем заполнить бриф
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📝 Заполнить бриф", callback_data="start_brief_after_reg"))
        
        bot.reply_to(
            message,
            f"🎉 <b>Регистрация успешно завершена!</b>\n\n"
            f"✅ ФИО: {user.full_name}\n"
            f"✅ Учебное заведение: {user.school}\n"
            f"✅ Класс/курс: {user.grade}\n\n"
            f"Теперь давайте заполним небольшой бриф, чтобы лучше понять ваши потребности "
            f"и подобрать оптимальную программу обучения.",
            reply_markup=markup,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Ошибка в handle_grade: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при сохранении класса/курса")


def cancel_registration(call: CallbackQuery):
    """Отменяет процесс регистрации"""
    try:
        user_id = str(call.from_user.id)
        user = User.objects.get(telegram_id=user_id)
        
        # Если пользователь только что создан и не заполнил данные - удаляем его
        if not user.full_name and not user.grade and not user.school:
            user.delete()
        
        bot.edit_message_text(
            "❌ Регистрация отменена. Вы можете начать её заново в любой момент.",
            call.message.chat.id,
            call.message.message_id
        )
        
        # Показываем кнопку для повторной регистрации
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📝 Начать регистрацию", callback_data="start_registration"))
        
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    except Exception as e:
        logging.error(f"Ошибка в cancel_registration: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


def start_brief_after_registration(call: CallbackQuery):
    """Запускает бриф после завершения регистрации"""
    try:
        user_id = str(call.from_user.id)
        user = User.objects.get(telegram_id=user_id)
        
        # Проверяем, что регистрация завершена
        if not user.full_name or not user.grade or not user.school:
            bot.answer_callback_query(call.id, "❌ Сначала завершите регистрацию")
            return
        
        # Запускаем бриф
        start_brief(call)
        
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в start_brief_after_registration: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
