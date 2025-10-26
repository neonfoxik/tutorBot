from telebot.types import CallbackQuery
from django.db import transaction
from bot import bot
import logging

logger = logging.getLogger('bot')
from bot.models import User, Payment, PaymentHistory
from bot.keyboards import (
    generate_payment_method_keyboard,
    generate_payment_months_keyboard,
    generate_balance_payment_months_keyboard,
    generate_check_payment_keyboard,
    generate_payment_menu_keyboard
)
from bot.pricing import get_price_by_class
from bot.yookassa_client import create_payment as create_yookassa_payment


def payment_method(call: CallbackQuery) -> None:
    """Показывает меню выбора способа оплаты"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
            
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        lesson_price = price_info['price']
        class_name = price_info['name']
        description = price_info['description']
        
        markup = generate_payment_method_keyboard()
        
        text = f"💳 Оплата занятий\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.class_number}\n"
        text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"💵 Стоимость: {lesson_price} ₽\n"
        text += f"💳 Баланс: {active_profile.balance} ₽\n\n"
        text += f"Выберите способ оплаты:"
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=markup,
                message_id=call.message.message_id
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            bot.answer_callback_query(call.id, "❌ Произошла ошибка")
            
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")


def payment_menu(call: CallbackQuery) -> None:
    """Показывает меню оплаты"""
    from bot.handlers.registration import start_registration
    
    telegram_id = str(call.from_user.id)
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = User.objects.get(telegram_id=telegram_id)
        
        # Проверяем, есть ли у пользователя хотя бы один профиль
        if not user.student_profiles.exists():
            # Если нет профилей, отправляем на регистрацию
            bot.answer_callback_query(call.id, "⚠️ Для оплаты необходимо пройти регистрацию")
            start_registration(call.message)
            return
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
            
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        lesson_price = price_info['price']
        class_name = price_info['name']
        description = price_info['description']
        
        markup = generate_payment_menu_keyboard()
        
        text = f"💳 Меню оплаты\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.class_number}\n"
        text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"💵 Стоимость: {lesson_price} ₽\n"
        text += f"💳 Баланс: {active_profile.balance} ₽\n\n"
        text += f"Выберите действие:"
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=markup,
                message_id=call.message.message_id
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            bot.answer_callback_query(call.id, "❌ Произошла ошибка")
            
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "⚠️ Для оплаты необходимо пройти регистрацию")
        start_registration(call.message)


def start_payment(call: CallbackQuery) -> None:
    """Начинает процесс оплаты - показывает выбор способа оплаты"""
    from bot.handlers.registration import start_registration
    
    telegram_id = str(call.from_user.id)
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = User.objects.get(telegram_id=telegram_id)
        
        # Проверяем, есть ли у пользователя хотя бы один профиль
        if not user.student_profiles.exists():
            # Если нет профилей, отправляем на регистрацию
            bot.answer_callback_query(call.id, "⚠️ Для оплаты необходимо пройти регистрацию")
            start_registration(call.message)
            return
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
            
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        lesson_price = price_info['price']
        class_name = price_info['name']
        description = price_info['description']
        
        markup = generate_payment_method_keyboard()
        
        text = f"💳 Оплата занятий\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.class_number}\n"
        text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"💵 Стоимость: {lesson_price} ₽\n"
        text += f"💳 Баланс: {active_profile.balance} ₽\n\n"
        text += f"Выберите способ оплаты:"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "⚠️ Для оплаты необходимо пройти регистрацию")
        start_registration(call.message)


def select_payment_method(call: CallbackQuery) -> None:
    """Обрабатывает выбор способа оплаты"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
            
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        lesson_price = price_info['price']
        class_name = price_info['name']
        description = price_info['description']
        
        if call.data == "pay_with_yookassa":
            markup = generate_payment_months_keyboard()
            text = f"📅 Выберите месяц для оплаты\n\n"
            text += f"👤 Профиль: {active_profile.profile_name}\n"
            text += f"📚 Класс: {active_profile.class_number}\n"
            text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
            text += f"💰 Тариф: {class_name}\n"
            text += f"ℹ️ {description}\n"
            text += f"💵 Стоимость: {lesson_price} ₽"
        else:  # pay_with_balance
            if active_profile.balance <= 0:
                bot.answer_callback_query(call.id, "❌ На балансе недостаточно средств")
                return
            
            markup = generate_balance_payment_months_keyboard()
            text = f"📅 Выберите месяц для оплаты с баланса\n\n"
            text += f"👤 Профиль: {active_profile.profile_name}\n"
            text += f"📚 Класс: {active_profile.class_number}\n"
            text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
            text += f"💰 Тариф: {class_name}\n"
            text += f"ℹ️ {description}\n"
            text += f"💵 Стоимость: {lesson_price} ₽\n"
            text += f"💳 Баланс: {active_profile.balance} ₽"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")


def select_payment_month(call: CallbackQuery) -> None:
    """Обрабатывает выбор месяца для оплаты через ЮKassa"""
    logger.info(f"Начало обработки выбора месяца. User ID: {call.from_user.id}")
    logger.info(f"Callback data: {call.data}")
    logger.info("Проверка настроек YooKassa:")
    from django.conf import settings
    logger.info(f"YOOKASSA_TEST_MODE: {settings.YOOKASSA_TEST_MODE}")
    logger.info(f"YOOKASSA_SHOP_ID exists: {'YOOKASSA_SHOP_ID' in dir(settings)}")
    logger.info(f"YOOKASSA_SECRET_KEY exists: {'YOOKASSA_SECRET_KEY' in dir(settings)}")
    try:
        # Получаем месяц и год из callback_data
        parts = call.data.split('_')
        if len(parts) < 4:
            bot.answer_callback_query(call.id, "❌ Неверный формат данных")
            return
            
        try:
            month = int(parts[2])
            year = int(parts[3])
        except (IndexError, ValueError):
            bot.answer_callback_query(call.id, "❌ Неверный формат даты")
            return
            
        if not (1 <= month <= 12):
            bot.answer_callback_query(call.id, "❌ Неверный номер месяца")
            return
            
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
        
        # Проверяем, не оплачен ли уже этот месяц
        if PaymentHistory.is_month_paid(user, month, year, active_profile):
            bot.answer_callback_query(call.id, "❌ Этот месяц уже оплачен")
            return
        
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        lesson_price = price_info['price']
        class_name = price_info['name']
        description = price_info['description']
        
        # Создаем платеж в ЮKassa
        logger.info(f"Начинаем создание платежа в YooKassa для пользователя {user.telegram_id}")
        try:
            # Добавляем метаданные для платежа
            metadata = {
                'user_id': user.telegram_id,
                'profile_id': active_profile.id,
                'month': month,
                'year': year
            }
            
            # Создаем платеж
            payment_data = create_yookassa_payment(
                amount=lesson_price,
                description=f"Оплата занятий за {month:02d}.{year}",
                metadata=metadata
            )
            
            print(f"Payment data from YooKassa: {payment_data}")
            
            if not payment_data:
                bot.answer_callback_query(call.id, "❌ Ошибка создания платежа: нет ответа от ЮKassa")
                return
                
            if 'id' not in payment_data:
                bot.answer_callback_query(call.id, "❌ Ошибка создания платежа: нет ID платежа")
                return
                
            if 'confirmation' not in payment_data:
                bot.answer_callback_query(call.id, "❌ Ошибка создания платежа: нет данных для подтверждения")
                return
                
            if 'confirmation_url' not in payment_data['confirmation']:
                bot.answer_callback_query(call.id, "❌ Ошибка создания платежа: нет URL для оплаты")
                return
        except Exception as e:
            print(f"Error creating YooKassa payment: {e}")
            bot.answer_callback_query(call.id, "❌ Ошибка при создании платежа")
            return
        
        # Создаем запись о платеже
        payment = Payment.objects.create(
            user=user,
            student_profile=active_profile,
            yookassa_payment_id=payment_data['id'],
            amount=lesson_price,
            status='pending',
            description=f"Оплата занятий за {month:02d}.{year}",
            payment_month=month,
            payment_year=year,
            pricing_plan=class_name
        )
        
        # Получаем URL для оплаты
        confirmation_url = payment_data['confirmation']['confirmation_url']
        
        # Показываем кнопку для перехода к оплате
        markup = generate_check_payment_keyboard(confirmation_url, payment_data['id'], month, year)
        
        text = f"💳 Оплата занятий\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.class_number}\n"
        text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"📅 Период: {month:02d}.{year}\n"
        text += f"💵 Сумма: {lesson_price} ₽\n\n"
        text += f"Для оплаты нажмите кнопку 'Перейти к оплате'"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
        return
    except ValueError as e:
        print(f"ValueError in select_payment_month: {str(e)}")
        bot.answer_callback_query(call.id, "❌ Ошибка в формате данных")
        return
    except Exception as e:
        import traceback
        error_info = traceback.format_exc()
        logger.error(f"Подробная информация об ошибке в select_payment_month:\n{error_info}")
        logger.error(f"Данные callback: {call.data}")
        logger.error(f"ID пользователя: {call.from_user.id}")
        logger.error(f"Ошибка: {str(e)}")
        bot.answer_callback_query(call.id, "❌ Ошибка при обработке платежа. Попробуйте позже.")
        return


def select_balance_payment_month(call: CallbackQuery) -> None:
    """Обрабатывает выбор месяца для оплаты с баланса"""
    try:
        # Получаем месяц и год из callback_data
        month = int(call.data.split('_')[3])
        year = int(call.data.split('_')[4])
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
        
        # Проверяем, не оплачен ли уже этот месяц
        if PaymentHistory.is_month_paid(user, month, year, active_profile):
            bot.answer_callback_query(call.id, "❌ Этот месяц уже оплачен")
            return
        
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        lesson_price = price_info['price']
        class_name = price_info['name']
        description = price_info['description']
        
        # Проверяем достаточно ли средств на балансе
        if active_profile.balance < lesson_price:
            bot.answer_callback_query(call.id, "❌ На балансе недостаточно средств")
            return
        
        with transaction.atomic():
            # Списываем средства с баланса
            active_profile.balance -= lesson_price
            active_profile.save()
            
            # Создаем запись в истории платежей
            PaymentHistory.objects.create(
                user=user,
                student_profile=active_profile,
                month=month,
                year=year,
                amount_paid=lesson_price,
                pricing_plan=class_name,
                payment_type='balance',
                status='completed'
            )
        
        text = f"✅ Оплата успешно выполнена!\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.class_number}\n"
        text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"📅 Период: {month:02d}.{year}\n"
        text += f"💵 Списано: {lesson_price} ₽\n"
        text += f"💳 Остаток на балансе: {active_profile.balance} ₽"
        
        markup = generate_payment_menu_keyboard()
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
        
        # Уведомляем админов об оплате
        notify_admins_about_payment(user, active_profile, month, year, lesson_price, 'balance')
        
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


def check_payment(call: CallbackQuery) -> None:
    """Проверяет статус платежа"""
    try:
        # Получаем данные из callback_data
        payment_id = call.data.split('_')[2]
        month = int(call.data.split('_')[3])
        year = int(call.data.split('_')[4])
        
        payment = Payment.objects.get(yookassa_payment_id=payment_id)
        
        if payment.status == 'succeeded':
            # Платеж уже проведен
            text = f"✅ Оплата успешно выполнена!\n\n"
            text += f"👤 Профиль: {payment.student_profile.profile_name}\n"
            text += f"📚 Класс: {payment.student_profile.class_number}\n"
            text += f"📊 Уровень: {payment.student_profile.get_education_level_display() or 'Не указан'}\n"
            text += f"📅 Период: {month:02d}.{year}\n"
            text += f"💵 Сумма: {payment.amount} ₽"
            
            markup = generate_payment_menu_keyboard()
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=markup,
                message_id=call.message.message_id
            )
        else:
            bot.answer_callback_query(call.id, "❌ Платеж еще не проведен")
    except Payment.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Платеж не найден")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


def payment_history(call: CallbackQuery) -> None:
    """Показывает историю платежей"""
    from bot.handlers.registration import start_registration
    
    telegram_id = str(call.from_user.id)
    
    try:
        # Проверяем, есть ли пользователь в базе
        user = User.objects.get(telegram_id=telegram_id)
        
        # Проверяем, есть ли у пользователя хотя бы один профиль
        if not user.student_profiles.exists():
            # Если нет профилей, отправляем на регистрацию
            bot.answer_callback_query(call.id, "⚠️ Для просмотра истории необходимо пройти регистрацию")
            start_registration(call.message)
            return
        
        # Получаем активный профиль
        active_profile = user.student_profiles.filter(is_active=True).first()
        if not active_profile:
            bot.answer_callback_query(call.id, "❌ У вас нет активного профиля")
            return
            
        # Получаем цену занятия для ученика с учетом уровня образования
        class_key = active_profile.class_number
        if active_profile.education_level:
            if active_profile.class_number in ['10', '11']:
                class_key = f"{active_profile.class_number}_{active_profile.education_level}"
        
        price_info = get_price_by_class(class_key)
        
        if not price_info:
            bot.answer_callback_query(call.id, "❌ Не удалось определить тариф для вашего класса")
            return
            
        class_name = price_info['name']
        description = price_info['description']
        
        # Получаем историю платежей
        payments = PaymentHistory.objects.filter(
            user=user,
            student_profile=active_profile,
            status='completed'
        ).order_by('-year', '-month')
        
        text = f"📊 История платежей\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.class_number}\n"
        text += f"📊 Уровень: {active_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"💳 Баланс: {active_profile.balance} ₽\n\n"
        
        if not payments.exists():
            text += f"У вас пока нет оплаченных месяцев."
        else:
            text += f"Оплаченные месяцы:\n"
            for payment in payments:
                text += f"• {payment.month:02d}.{payment.year} - {payment.amount_paid} ₽\n"
        
        markup = generate_payment_menu_keyboard()
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "⚠️ Для просмотра истории необходимо пройти регистрацию")
        start_registration(call.message)


def notify_payment_success(payment_id: str) -> None:
    """Уведомляет пользователя об успешной оплате"""
    try:
        payment = Payment.objects.get(yookassa_payment_id=payment_id)
        
        # Создаем запись в истории платежей
        PaymentHistory.objects.create(
            user=payment.user,
            student_profile=payment.student_profile,
            payment=payment,
            month=payment.payment_month,
            year=payment.payment_year,
            amount_paid=payment.amount,
            pricing_plan=payment.pricing_plan,
            payment_type='card',
            status='completed'
        )
        
        # Получаем цену занятия для ученика
        price_info = get_price_by_class(payment.student_profile.class_number)
        
        if price_info:
            class_name = price_info['name']
            description = price_info['description']
        else:
            class_name = payment.pricing_plan
            description = ""
        
        # Отправляем уведомление пользователю
        text = f"✅ Оплата успешно выполнена!\n\n"
        text += f"👤 Профиль: {payment.student_profile.profile_name}\n"
        text += f"📚 Класс: {payment.student_profile.class_number}\n"
        text += f"📊 Уровень: {payment.student_profile.get_education_level_display() or 'Не указан'}\n"
        text += f"💰 Тариф: {class_name}\n"
        text += f"ℹ️ {description}\n"
        text += f"📅 Период: {payment.payment_month:02d}.{payment.payment_year}\n"
        text += f"💵 Сумма: {payment.amount} ₽"
        
        bot.send_message(
            chat_id=payment.user.telegram_id,
            text=text
        )
        
        # Уведомляем админов
        notify_admins_about_payment(
            payment.user,
            payment.student_profile,
            payment.payment_month,
            payment.payment_year,
            payment.amount,
            'card'
        )
        
    except Payment.DoesNotExist:
        pass


def notify_admins_about_payment(user: User, profile: 'StudentProfile', month: int, year: int, amount: float, payment_type: str) -> None:
    """Уведомляет админов об оплате"""
    admins = User.objects.filter(is_admin=True)
    
    # Получаем цену занятия для ученика
    price_info = get_price_by_class(profile.class_number)
    
    if price_info:
        class_name = price_info['name']
        description = price_info['description']
    else:
        class_name = "Тариф не определен"
        description = ""
    
    text = f"💰 Новая оплата!\n\n"
    text += f"👤 Ученик: {profile.full_name}\n"
    text += f"📚 Класс: {profile.class_number}\n"
    text += f"📊 Уровень: {profile.get_education_level_display() or 'Не указан'}\n"
    text += f"💰 Тариф: {class_name}\n"
    text += f"ℹ️ {description}\n"
    text += f"📅 Период: {month:02d}.{year}\n"
    text += f"💳 Способ: {'Банковская карта' if payment_type == 'card' else 'С баланса'}\n"
    text += f"💵 Сумма: {amount} ₽"
    
    for admin in admins:
        try:
            bot.send_message(admin.telegram_id, text)
        except Exception:
            continue