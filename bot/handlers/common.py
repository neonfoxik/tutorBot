import logging
from traceback import format_exc
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
        logger.info(f"Начинаем обработку оплаты для пользователя {call.from_user.id}")
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        logger.info(f"Пользователь найден: {user.telegram_id}")
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            logger.info(f"Регистрация не завершена для пользователя {user.telegram_id}")
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
        
        logger.info(f"Регистрация завершена, показываем календарь для пользователя {user.telegram_id}")
        
        # Показываем календарь оплаты
        show_payment_calendar(call, user)
        
    except User.DoesNotExist:
        logger.error(f"Пользователь не найден: {call.from_user.id}")
        bot.answer_callback_query(call.id, "Пользователь не найден")
    except Exception as e:
        logger.error(f"Ошибка в pay: {e}")
        logger.error(f"Traceback: {format_exc()}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def show_payment_calendar(call: CallbackQuery, user: User):
    """Показывает календарь оплаты"""
    try:
        logger.info(f"Начинаем загрузку календаря для пользователя {user.telegram_id}")
        
        from bot.utils import get_payment_months, get_month_display_name, is_month_paid, get_current_academic_year
        
        # Получаем месяцы для оплаты (12 месяцев назад)
        months = get_payment_months(12)
        logger.info(f"Получены месяцы: {[m.strftime('%B %Y') for m in months]}")
        
        current_year = get_current_academic_year()
        logger.info(f"Текущий учебный год: {current_year}")
        
        # Формируем текст
        text = f"💳 <b>Оплата за обучение</b>\n\n"
        text += f"👤 Пользователь: {user.full_name}\n"
        text += f"🎓 {user.grade}\n"
        text += f"📚 {user.school}\n"
        text += f"📅 Учебный год: {current_year}\n"
        text += f"💰 Стоимость обучения: 1000 ₽/месяц\n\n"
        text += "Выберите месяц для оплаты:\n"
        text += "✅ - оплачено, 💰 - доступно для оплаты\n\n"
        
        # Создаем клавиатуру с месяцами в 2 столбца
        markup = InlineKeyboardMarkup(row_width=2)
        
        # Создаем список кнопок для месяцев
        month_buttons = []
        for i, month_date in enumerate(months):
            try:
                month_name = get_month_display_name(month_date)
                month_key = f"{month_date.year}_{month_date.month:02d}"
                
                logger.info(f"Обрабатываем месяц {month_name} {month_date.year}")
                
                if is_month_paid(user, month_date):
                    # Месяц уже оплачен
                    button_text = f"✅ {month_name}"
                    callback_data = f"month_paid_{month_key}"
                    logger.info(f"Месяц {month_name} уже оплачен")
                else:
                    # Месяц доступен для оплаты
                    button_text = f"💰 {month_name}"
                    callback_data = f"month_pay_{month_key}"
                    logger.info(f"Месяц {month_name} доступен для оплаты")
                
                month_buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))
                
            except Exception as month_error:
                logger.error(f"Ошибка при обработке месяца {month_date}: {month_error}")
                # Пропускаем проблемный месяц
                continue
        
        # Добавляем месяцы в клавиатуру по 2 в ряд
        for i in range(0, len(month_buttons), 2):
            if i + 1 < len(month_buttons):
                # Добавляем два месяца в один ряд
                markup.row(month_buttons[i], month_buttons[i + 1])
            else:
                # Последний месяц (если нечетное количество)
                markup.row(month_buttons[i])
        
        # Добавляем кнопку "Назад" снизу по центру
        markup.row(InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))
        
        logger.info("Клавиатура создана, отправляем сообщение")
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
        
        logger.info("Календарь успешно загружен")
        
    except Exception as e:
        logger.error(f"Ошибка в show_payment_calendar: {e}")
        logger.error(f"Traceback: {format_exc()}")
        bot.answer_callback_query(call.id, "Произошла ошибка при загрузке календаря")


def handle_month_payment(call: CallbackQuery):
    """Обрабатывает выбор месяца для оплаты"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Извлекаем месяц из callback_data
        month_key = call.data.split('_', 2)[2]  # month_pay_2024_08 -> 2024_08
        from bot.utils import parse_month_key, get_month_display_name, get_academic_year_for_month, get_payment_amount_for_month
        
        month_date = parse_month_key(month_key)
        month_name = get_month_display_name(month_date)
        academic_year = get_academic_year_for_month(month_date)
        amount = get_payment_amount_for_month(month_date)
        
        # Создаем или получаем запись о платеже
        from bot.models import Payment
        payment, created = Payment.objects.get_or_create(
            user=user,
            payment_month=month_date,
            academic_year=academic_year,
            defaults={
                'amount': amount,
                'description': f"Оплата за {month_name} {month_date.year}",
                'status': Payment.Status.PENDING
            }
        )
        
        if not created and payment.status in [Payment.Status.SUCCEEDED, Payment.Status.MANUAL]:
            # Месяц уже оплачен
            bot.answer_callback_query(call.id, f"✅ {month_name} уже оплачен!")
            return
        
        # Показываем информацию об оплате
        text = f"💳 <b>Оплата за {month_name} {month_date.year}</b>\n\n"
        text += f"👤 Пользователь: {user.full_name}\n"
        text += f"🎓 {user.grade}\n"
        text += f"📚 {user.school}\n"
        text += f"📅 Учебный год: {academic_year}\n"
        text += f"💰 Сумма: {amount} ₽\n\n"
        text += "Нажмите кнопку ниже для перехода к оплате:"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Перейти к оплате", callback_data=f"pay_now_{payment.id}"))
        markup.add(InlineKeyboardButton("🔙 Назад к календарю", callback_data="payment_calendar"))
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logging.error(f"Ошибка в handle_month_payment: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def handle_month_paid_info(call: CallbackQuery):
    """Показывает информацию об уже оплаченном месяце"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Извлекаем месяц из callback_data
        month_key = call.data.split('_', 2)[2]  # month_paid_2024_08 -> 2024_08
        from bot.utils import parse_month_key, get_month_display_name, get_academic_year_for_month
        
        month_date = parse_month_key(month_key)
        month_name = get_month_display_name(month_date)
        academic_year = get_academic_year_for_month(month_date)
        
        # Получаем информацию о платеже
        from bot.models import Payment
        payment = Payment.objects.get(
            user=user,
            payment_month=month_date,
            academic_year=academic_year
        )
        
        text = f"✅ <b>{month_name} {month_date.year} - Оплачено</b>\n\n"
        text += f"👤 Пользователь: {user.full_name}\n"
        text += f"🎓 {user.grade}\n"
        text += f"📚 {user.school}\n"
        text += f"📅 Учебный год: {academic_year}\n"
        text += f"💰 Сумма: {payment.amount} ₽\n"
        text += f"📅 Дата оплаты: {payment.confirmed_at.strftime('%d.%m.%Y') if payment.confirmed_at else 'Не указана'}\n"
        text += f"📝 Статус: {payment.get_status_display()}\n\n"
        text += "Этот месяц уже оплачен и доступен для обучения."
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад к календарю", callback_data="payment_calendar"))
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logging.error(f"Ошибка в handle_month_paid_info: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def pay_now(call: CallbackQuery):
    """Переход к оплате выбранного месяца"""
    try:
        payment_id = int(call.data.split('_')[-1])
        from bot.models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        user = payment.user
        
        # Заглушка для ЮKassa - в реальности здесь будет генерация ссылки
        payment_link = f"https://yoomoney.ru/quickpay/button-widget?targets=Оплата%20за%20{payment.payment_month.strftime('%B %Y')}&default-sum={payment.amount}&button-text=11&any-card-payment-type=on&button-size=m&button-color=orange&successURL=&quickpay=small&account=410012345678901&"
        
        text = f"💳 <b>Оплата за {payment.payment_month.strftime('%B %Y')}</b>\n\n"
        text += f"👤 Пользователь: {user.full_name}\n"
        text += f"🎓 {user.grade}\n"
        text += f"📚 {user.school}\n"
        text += f"💰 Сумма: {payment.amount} ₽\n\n"
        text += f"🔗 <a href='{payment_link}'>Перейти к оплате</a>\n\n"
        text += "После оплаты нажмите кнопку 'Я оплатил'"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Я оплатил", callback_data=f"payment_i_paid_{payment.id}"))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data=f"month_pay_{payment.payment_month.year}_{payment.payment_month.month:02d}"))
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logging.error(f"Ошибка в pay_now: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def payment_calendar_back(call: CallbackQuery):
    """Возврат к календарю оплаты"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        show_payment_calendar(call, user)
    except Exception as e:
        logging.error(f"Ошибка в payment_calendar_back: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


def payment_i_paid(call: CallbackQuery):
    """Обработчик кнопки 'Я оплатил'"""
    try:
        payment_id = int(call.data.split('_')[-1])
        payment = Payment.objects.get(id=payment_id)
        
        # Устанавливаем статус PENDING для ручной проверки админом
        payment.status = Payment.Status.PENDING
        payment.save()
        
        # Показываем информацию о платеже и предлагаем вернуться к календарю
        text = "⏳ <b>Ожидание подтверждения</b>\n\n"
        text += f"Ваш платеж за {payment.payment_month.strftime('%B %Y')} отправлен на проверку администратору.\n"
        text += "Вы получите уведомление после подтверждения.\n\n"
        text += f"💰 Сумма: {payment.amount} ₽\n"
        text += f"📅 Месяц: {payment.payment_month.strftime('%B %Y')}\n"
        text += f"📚 Учебный год: {payment.academic_year}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📅 Вернуться к календарю", callback_data="payment_calendar"))
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
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
                    f"ID платежа: {payment.id}\n"
                    f"Месяц: {payment.payment_month.strftime('%B %Y')}\n"
                    f"Учебный год: {payment.academic_year}"
                )
        except Exception as e:
            logging.error(f"Ошибка при уведомлении админа: {e}")
            
    except (ValueError, Payment.DoesNotExist):
        bot.answer_callback_query(call.id, "Платеж не найден")
    except Exception as e:
        logging.error(f"Ошибка в payment_i_paid: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")

    

