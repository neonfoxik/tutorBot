import logging
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.models import User, Payment
from bot.keyboards import build_main_markup, build_payment_confirmation_markup, UNIVERSAL_BUTTONS, UNIVERSAL_VIDEO_MARKUP
from bot.texts import MAIN_TEXT
from bot.handlers.admin.admin import admin_permission
from bot import bot, logger


def start(message: Message):
    """Обработчик команды /start"""
    try:
        user, created = User.objects.get_or_create(
            telegram_id=str(message.from_user.id),
            defaults={
                'user_tg_name': message.from_user.username or 'none',
                'user_name': message.from_user.first_name or 'Без имени'
            }
        )
        if created:
            logger.info(f"Создан новый пользователь: {user.telegram_id}")
        
        # Проверяем, заполнены ли обязательные поля
        if not user.full_name or not user.school or not user.grade:
            # Показываем сообщение о необходимости завершить регистрацию
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.reply_to(
                message,
                "⚠️ <b>Для доступа к меню необходимо завершить регистрацию</b>\n\n"
                "Пожалуйста, заполните следующие данные:\n"
                f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                "Нажмите кнопку ниже для завершения регистрации:",
                reply_markup=markup,
                parse_mode='HTML'
            )
            return
        
        # Все поля заполнены - показываем главное меню
        bot.reply_to(message, MAIN_TEXT, reply_markup=build_main_markup())
    except Exception as e:
        logger.error(f"Ошибка в start: {e}")
        bot.reply_to(message, "Произошла ошибка. Попробуйте позже.")


def menu_call(call: CallbackQuery):
    """Обработчик кнопки 'Главное меню'"""
    try:
        bot.edit_message_text(
            MAIN_TEXT,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=build_main_markup()
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Ошибка в menu_call: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def menu_video(call: CallbackQuery):
    """Обработчик кнопки 'Главное меню' из видео"""
    try:
        bot.edit_message_text(
            MAIN_TEXT,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=build_main_markup()
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Ошибка в menu_video: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def FAQ(call: CallbackQuery):
    """Обработчик кнопки 'Туториал'"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.edit_message_text(
                "⚠️ <b>Для доступа к туториалу необходимо завершить регистрацию</b>\n\n"
                "Пожалуйста, заполните следующие данные:\n"
                f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                "Нажмите кнопку ниже для завершения регистрации:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            return
        
        bot.edit_message_text(
            "📚 Туториал по использованию бота\n\n"
            "Здесь будет инструкция по использованию бота...",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=UNIVERSAL_VIDEO_MARKUP
        )
        bot.answer_callback_query(call.id)
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")
    except Exception as e:
        logger.error(f"Ошибка в FAQ: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def profile(call: CallbackQuery):
    """Обработчик кнопки 'Профиль'"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.edit_message_text(
                "⚠️ <b>Для доступа к профилю необходимо завершить регистрацию</b>\n\n"
                "Пожалуйста, заполните следующие данные:\n"
                f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                "Нажмите кнопку ниже для завершения регистрации:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            return
        
        profile_text = f"👤 <b>Профиль</b>\n\n"
        profile_text += f"📱 Имя: {user.user_name or 'Не указано'}\n"
        profile_text += f"📝 ФИО: {user.full_name or 'Не указано'}\n"
        profile_text += f"🎓 Класс: {user.grade or 'Не указано'}\n"
        profile_text += f"🏫 Школа: {user.school or 'Не указано'}\n"
        profile_text += f"💳 Статус оплаты: {'✅ Оплачено' if user.is_paid_current_month else '❌ Не оплачено'}\n"
        profile_text += f"📝 Бриф: {'✅ Заполнен' if user.brief_completed else '❌ Не заполнен'}\n"
        
        if user.last_payment_at:
            profile_text += f"📅 Последняя оплата: {user.last_payment_at.strftime('%d.%m.%Y')}\n"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✏️ Изменить ФИО", callback_data="profile_set_full_name"))
        markup.add(InlineKeyboardButton("✏️ Изменить класс", callback_data="profile_set_grade"))
        markup.add(InlineKeyboardButton("✏️ Изменить школу", callback_data="profile_set_school"))
        
        if not user.brief_completed:
            markup.add(InlineKeyboardButton("📝 Заполнить бриф", callback_data="brief_progress"))
        else:
            markup.add(InlineKeyboardButton("📊 Прогресс бриф", callback_data="brief_progress"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        bot.edit_message_text(
            profile_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в profile: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def _ask_text(call: CallbackQuery, field: str, title: str):
    """Общая функция для запроса текста"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.edit_message_text(
                "⚠️ <b>Для изменения профиля необходимо завершить регистрацию</b>\n\n"
                "Пожалуйста, заполните следующие данные:\n"
                f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                "Нажмите кнопку ниже для завершения регистрации:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            return
        
        bot.edit_message_text(
            f"Введите {title}:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=UNIVERSAL_BUTTONS
        )
        bot.answer_callback_query(call.id)
        
        # Регистрируем следующий шаг для получения текста
        bot.register_next_step_handler(call.message, _save_profile_field, field, title)
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в _ask_text: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def _save_profile_field(message: Message, field: str, title: str):
    """Общая функция для сохранения поля профиля"""
    try:
        user = User.objects.get(telegram_id=str(message.from_user.id))
        setattr(user, field, message.text)
        user.save()
        
        bot.reply_to(
            message,
            f"✅ {title} успешно обновлен!",
            reply_markup=build_main_markup()
        )
    except User.DoesNotExist:
        bot.reply_to(message, "Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка при сохранении {field}: {e}")
        bot.reply_to(message, "Произошла ошибка при сохранении")


def profile_set_full_name(call: CallbackQuery):
    """Обработчик установки ФИО"""
    _ask_text(call, 'full_name', 'ФИО')


def profile_set_grade(call: CallbackQuery):
    """Обработчик установки класса"""
    _ask_text(call, 'grade', 'класс')


def profile_set_school(call: CallbackQuery):
    """Обработчик установки школы"""
    _ask_text(call, 'school', 'школу')


def pay(call: CallbackQuery):
    """Обработчик кнопки 'Оплата'"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.edit_message_text(
                "⚠️ <b>Для доступа к оплате необходимо завершить регистрацию</b>\n\n"
                "Пожалуйста, заполните следующие данные:\n"
                f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                "Нажмите кнопку ниже для завершения регистрации:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            return
        
        # Создаем запись о платеже
        payment = Payment.objects.create(
            user=user,
            amount=1000.00,  # Фиксированная сумма для заглушки
            description="Оплата за обучение",
            status=Payment.Status.PENDING
        )
        
        # Заглушка для ЮKassa - в реальности здесь будет генерация ссылки
        payment_link = f"https://yoomoney.ru/quickpay/button-widget?targets=Оплата%20за%20обучение&default-sum={payment.amount}&button-text=11&any-card-payment-type=on&button-size=m&button-color=orange&successURL=&quickpay=small&account=410012345678901&"
        
        payment_text = (
            f"💳 <b>Оплата за обучение</b>\n\n"
            f"💰 Сумма: {payment.amount} ₽\n"
            f"📝 Описание: {payment.description}\n\n"
            f"🔗 <a href='{payment_link}'>Перейти к оплате</a>\n\n"
            f"После оплаты нажмите кнопку 'Я оплатил'"
        )
        
        bot.edit_message_text(
            payment_text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=build_payment_confirmation_markup(payment.id),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        bot.answer_callback_query(call.id)
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в pay: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def payment_i_paid(call: CallbackQuery):
    """Обработчик кнопки 'Я оплатил'"""
    try:
        payment_id = int(call.data.split('_')[-1])
        payment = Payment.objects.get(id=payment_id)
        
        # Устанавливаем статус PENDING для ручной проверки админом
        payment.status = Payment.Status.PENDING
        payment.save()
        
        bot.edit_message_text(
            "⏳ <b>Ожидание подтверждения</b>\n\n"
            "Ваш платеж отправлен на проверку администратору.\n"
            "Вы получите уведомление после подтверждения.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id, "Платеж отправлен на проверку")
        
        # Уведомляем админа о новом платеже (если есть админ)
        try:
            admin_users = User.objects.filter(is_admin=True)
            for admin in admin_users:
                bot.send_message(
                    admin.telegram_id,
                    f"🔔 Новый платеж на проверку!\n"
                    f"Пользователь: {payment.user.user_tg_name}\n"
                    f"Сумма: {payment.amount} ₽\n"
                    f"ID платежа: {payment.id}"
                )
        except Exception as e:
            logging.error(f"Ошибка при уведомлении админа: {e}")
            
    except (ValueError, Payment.DoesNotExist):
        bot.answer_callback_query(call.id, "Платеж не найден")
    except Exception as e:
        logging.error(f"Ошибка в payment_i_paid: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")

    

