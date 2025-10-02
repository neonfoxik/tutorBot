from decimal import Decimal
from django.conf import settings
from telebot.types import CallbackQuery, Message
from bot import bot
from bot.models import User, StudentProfile, Payment, PaymentHistory
from bot.keyboards import (
    generate_payment_menu_keyboard,
    generate_payment_method_keyboard,
    generate_payment_months_keyboard,
    generate_balance_payment_months_keyboard,
    generate_payment_confirmation_keyboard,
    generate_check_payment_keyboard,
    UNIVERSAL_BUTTONS,
    MONTH_NAMES
)
from bot.pricing import get_price_by_class
from bot.yookassa_client import YooKassaClient
from django.utils import timezone


def get_active_profile(user: User) -> StudentProfile:
    """Получает активный профиль пользователя"""
    try:
        return user.student_profiles.get(is_active=True)
    except StudentProfile.DoesNotExist:
        return None


def payment_menu(call: CallbackQuery) -> None:
    """Обработчик меню оплаты"""
    markup = generate_payment_menu_keyboard()
    text = "💰 Оплата занятий\n\n"
    text += "Выберите действие:"
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        text=text,
        reply_markup=markup,
        message_id=call.message.message_id
    )


def start_payment(call: CallbackQuery) -> None:
    """Начинает процесс оплаты - показывает выбор способа оплаты"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        if not user.is_registered:
            bot.answer_callback_query(call.id, "Сначала завершите регистрацию!")
            return
        
        # Получаем активный профиль
        active_profile = get_active_profile(user)
        if not active_profile:
            text = "❌ У вас нет активного профиля.\n"
            text += "Создайте профиль в разделе 'Мои профили'."
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=UNIVERSAL_BUTTONS,
                message_id=call.message.message_id
            )
            return
        
        # Получаем цену для класса профиля
        price_info = get_price_by_class(active_profile.course_or_class)
        
        if not price_info:
            text = "❌ Не удалось определить стоимость для вашего класса.\n"
            text += "Обратитесь к администратору."
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=UNIVERSAL_BUTTONS,
                message_id=call.message.message_id
            )
            return
        
        markup = generate_payment_method_keyboard()
        text = f"💳 Оплата занятий\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.course_or_class}\n"
        text += f"💯 Тариф: {price_info['name']}\n"
        text += f"💰 Стоимость: {price_info['price']} руб.\n"
        text += f"💳 Баланс профиля: {active_profile.balance} ₽\n"
        text += f"📝 {price_info['description']}\n\n"
        text += "Выберите способ оплаты:"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")


def select_payment_method(call: CallbackQuery) -> None:
    """Обработчик выбора способа оплаты"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = get_active_profile(user)
        if not active_profile:
            bot.answer_callback_query(call.id, "У вас нет активного профиля")
            return
        
        # Получаем цену для класса профиля
        price_info = get_price_by_class(active_profile.course_or_class)
        
        if not price_info:
            bot.answer_callback_query(call.id, "Ошибка определения цены")
            return
        
        if call.data == "pay_with_yookassa":
            # Оплата через ЮKassa - показываем месяцы
            markup = generate_payment_months_keyboard()
            text = f"💳 Оплата через ЮKassa\n\n"
            text += f"👤 Профиль: {active_profile.profile_name}\n"
            text += f"📚 Класс: {active_profile.course_or_class}\n"
            text += f"💰 Стоимость: {price_info['price']} руб.\n\n"
            text += "Выберите месяц для оплаты:"
            
        elif call.data == "pay_with_balance":
            # Оплата с баланса - показываем месяцы
            markup = generate_balance_payment_months_keyboard()
            text = f"💰 Оплата с баланса\n\n"
            text += f"👤 Профиль: {active_profile.profile_name}\n"
            text += f"📚 Класс: {active_profile.course_or_class}\n"
            text += f"💰 Стоимость: {price_info['price']} руб.\n"
            text += f"💳 Баланс профиля: {active_profile.balance} ₽\n\n"
            text += "Выберите месяц для оплаты:"
            
        else:
            return
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")


def select_payment_month(call: CallbackQuery) -> None:
    """Обработчик выбора месяца для оплаты - сразу создает платеж и показывает ссылку"""
    try:
        # Парсим callback_data: pay_month_{month}_{year}
        parts = call.data.split('_')
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "Ошибка в данных")
            return
        
        month = int(parts[2])
        year = int(parts[3])
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = get_active_profile(user)
        if not active_profile:
            bot.answer_callback_query(call.id, "У вас нет активного профиля")
            return
        
        # Проверяем, не оплачен ли уже этот месяц для профиля
        if PaymentHistory.is_month_paid(user, month, year, active_profile):
            bot.answer_callback_query(call.id, f"Месяц {MONTH_NAMES[month]} {year} уже оплачен!")
            return
        
        # Получаем информацию о цене
        price_info = get_price_by_class(active_profile.course_or_class)
        
        if not price_info:
            bot.answer_callback_query(call.id, "Ошибка определения цены")
            return
        
        # Создаем платеж через ЮKassa
        yookassa_client = YooKassaClient()
        
        amount = Decimal(str(price_info['price']))
        description = f"Оплата занятий за {MONTH_NAMES[month]} {year} - {price_info['name']} - {active_profile.profile_name}"
        
        metadata = {
            "user_id": user.telegram_id,
            "profile_id": active_profile.id,
            "month": month,
            "year": year,
            "pricing_plan": price_info['key']
        }
        
        print(f"Создаем платеж для пользователя {user.telegram_id}, профиль {active_profile.id}")
        print(f"Сумма: {amount}, Описание: {description}")
        print(f"Метаданные: {metadata}")
        
        yookassa_response = yookassa_client.create_payment(
            amount=amount,
            description=description,
            metadata=metadata
        )
        
        print(f"Ответ от ЮKassa: {yookassa_response}")
        
        if not yookassa_response:
            text = "❌ Ошибка при создании платежа.\n\n"
            text += "Возможные причины:\n"
            text += "• Неправильные настройки ЮKassa\n"
            text += "• Проблемы с интернет-соединением\n"
            text += "• Ошибка на стороне ЮKassa\n\n"
            text += "Попробуйте позже или обратитесь к администратору."
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=UNIVERSAL_BUTTONS,
                message_id=call.message.message_id
            )
            return
        
        # Сохраняем платеж в базу данных
        payment = Payment.objects.create(
            user=user,
            student_profile=active_profile,
            yookassa_payment_id=yookassa_response['id'],
            amount=amount,
            status=yookassa_response['status'],
            description=description,
            payment_month=month,
            payment_year=year,
            pricing_plan=price_info['key']
        )
        
        # Получаем ссылку для оплаты (confirmation_url)
        payment_url = yookassa_response.get('confirmation', {}).get('confirmation_url')
        
        # Создаем клавиатуру с реальной ссылкой на оплату и кнопкой проверки
        markup = generate_check_payment_keyboard(payment_url, payment.yookassa_payment_id, month, year)
        
        text = f"✅ Платеж создан!\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.course_or_class}\n"
        text += f"💯 Тариф: {price_info['name']}\n"
        text += f"📅 Месяц: {MONTH_NAMES[month]} {year}\n"
        text += f"💰 Сумма: {amount} руб.\n\n"
        text += "1️⃣ Перейдите по ссылке и оплатите\n"
        text += "2️⃣ После оплаты нажмите 'Проверить оплату'\n"
        text += "3️⃣ Получите подтверждение"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    
    except (ValueError, User.DoesNotExist) as e:
        bot.answer_callback_query(call.id, "Ошибка обработки")


def select_balance_payment_month(call: CallbackQuery) -> None:
    """Обработчик выбора месяца для оплаты с баланса"""
    try:
        # Парсим callback_data: pay_balance_month_{month}_{year}
        parts = call.data.split('_')
        if len(parts) != 5:
            bot.answer_callback_query(call.id, "Ошибка в данных")
            return
        
        month = int(parts[3])
        year = int(parts[4])
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = get_active_profile(user)
        if not active_profile:
            bot.answer_callback_query(call.id, "У вас нет активного профиля")
            return
        
        # Проверяем, не оплачен ли уже этот месяц для профиля
        if PaymentHistory.is_month_paid(user, month, year, active_profile):
            bot.answer_callback_query(call.id, f"Месяц {MONTH_NAMES[month]} {year} уже оплачен!")
            return
        
        # Получаем информацию о цене
        price_info = get_price_by_class(active_profile.course_or_class)
        
        if not price_info:
            bot.answer_callback_query(call.id, "Ошибка определения цены")
            return
        
        amount = Decimal(str(price_info['price']))
        
        # Проверяем, достаточно ли средств на балансе профиля
        if active_profile.balance < amount:
            bot.answer_callback_query(call.id, f"Недостаточно средств на балансе!\nТребуется: {amount} ₽\nДоступно: {active_profile.balance} ₽")
            return
        
        # Списываем деньги с баланса профиля
        active_profile.balance -= amount
        active_profile.save()
        
        # Создаем запись в истории оплат
        PaymentHistory.objects.create(
            user=user,
            student_profile=active_profile,
            payment=None,  # Нет платежа через ЮKassa
            month=month,
            year=year,
            amount_paid=amount,
            pricing_plan=price_info['key'],
            payment_type='balance',
            status='completed'
        )
        
        # Уведомляем пользователя об успешной оплате
        notify_payment_success(user.telegram_id, month, year, amount, active_profile)
        
        # Уведомляем всех администраторов
        notify_admins_about_payment(user, month, year, amount, active_profile)
        
        # Обновляем сообщение
        text = f"🎉 Оплата с баланса прошла успешно!\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n"
        text += f"📚 Класс: {active_profile.course_or_class}\n"
        text += f"💯 Тариф: {price_info['name']}\n"
        text += f"📅 Месяц: {MONTH_NAMES[month]} {year}\n"
        text += f"💰 Сумма: {amount} ₽\n"
        text += f"💳 Остаток на балансе: {active_profile.balance} ₽\n\n"
        text += f"✅ Теперь вы можете посещать занятия в этом месяце!"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=generate_payment_menu_keyboard(),
            message_id=call.message.message_id
        )
    
    except (ValueError, User.DoesNotExist) as e:
        bot.answer_callback_query(call.id, "Ошибка обработки")


def check_payment(call: CallbackQuery) -> None:
    """Проверяет статус оплаты и обрабатывает успешные платежи"""
    try:
        # Парсим callback_data: check_payment_{payment_id}_{month}_{year}
        parts = call.data.split('_')
        if len(parts) != 5:
            bot.answer_callback_query(call.id, "Ошибка в данных")
            return
        
        payment_id = parts[2]
        month = int(parts[3])
        year = int(parts[4])
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = get_active_profile(user)
        if not active_profile:
            bot.answer_callback_query(call.id, "У вас нет активного профиля")
            return
        
        # Проверяем, не оплачен ли уже этот месяц для профиля
        if PaymentHistory.is_month_paid(user, month, year, active_profile):
            bot.answer_callback_query(call.id, f"Месяц {MONTH_NAMES[month]} {year} уже оплачен!")
            return
        
        # Получаем информацию о платеже из ЮKassa
        yookassa_client = YooKassaClient()
        payment_info = yookassa_client.get_payment(payment_id)
        
        if not payment_info:
            bot.answer_callback_query(call.id, "Ошибка получения информации о платеже")
            return
        
        payment_status = payment_info.get('status')
        
        if payment_status == 'succeeded':
            # Платеж успешен - обновляем базу данных
            try:
                payment = Payment.objects.get(yookassa_payment_id=payment_id)
                payment.status = 'succeeded'
                payment.payment_method = payment_info.get('payment_method', {})
                payment.save()
                
                # Создаем запись в истории оплат
                PaymentHistory.objects.create(
                    user=user,
                    student_profile=active_profile,
                    payment=payment,
                    month=month,
                    year=year,
                    amount_paid=payment.amount,
                    pricing_plan=payment.pricing_plan
                )
                
                # Уведомляем пользователя об успешной оплате
                notify_payment_success(user.telegram_id, month, year, payment.amount, active_profile)
                
                # Уведомляем всех администраторов
                notify_admins_about_payment(user, month, year, payment.amount, active_profile)
                
                # Обновляем сообщение
                text = f"🎉 Оплата подтверждена!\n\n"
                text += f"👤 Профиль: {active_profile.profile_name}\n"
                text += f"💰 Сумма: {payment.amount} руб.\n"
                text += f"📅 Месяц: {MONTH_NAMES[month]} {year}\n"
                text += f"✅ Теперь вы можете посещать занятия в этом месяце!"
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    text=text,
                    reply_markup=generate_payment_menu_keyboard(),
                    message_id=call.message.message_id
                )
                
            except Payment.DoesNotExist:
                bot.answer_callback_query(call.id, "Платеж не найден в базе данных")
                return
                
        elif payment_status == 'pending':
            bot.answer_callback_query(call.id, "Платеж еще не завершен. Попробуйте позже.")
        elif payment_status == 'canceled':
            bot.answer_callback_query(call.id, "Платеж отменен.")
        else:
            bot.answer_callback_query(call.id, f"Статус платежа: {payment_status}")
    
    except (ValueError, User.DoesNotExist) as e:
        bot.answer_callback_query(call.id, "Ошибка обработки")


def payment_history(call: CallbackQuery) -> None:
    """Показывает историю платежей пользователя"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем активный профиль
        active_profile = get_active_profile(user)
        if not active_profile:
            text = "❌ У вас нет активного профиля.\n"
            text += "Создайте профиль в разделе 'Мои профили'."
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=UNIVERSAL_BUTTONS,
                message_id=call.message.message_id
            )
            return
        
        # Получаем историю оплаченных месяцев для профиля
        history = PaymentHistory.objects.filter(
            user=user, 
            student_profile=active_profile
        ).order_by('-year', '-month')
        
        text = f"📊 История оплат\n\n"
        text += f"👤 Профиль: {active_profile.profile_name}\n\n"
        
        if history.exists():
            for record in history:
                month_name = MONTH_NAMES[record.month]
                text += f"✅ {month_name} {record.year} - {record.amount_paid} руб.\n"
                text += f"   📅 Оплачено: {record.paid_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        else:
            text += "Платежей пока нет."
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=UNIVERSAL_BUTTONS,
            message_id=call.message.message_id
        )
    
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")


def notify_payment_success(user_telegram_id: str, month: int, year: int, amount: Decimal, profile: StudentProfile):
    """Уведомляет пользователя об успешной оплате"""
    try:
        text = f"🎉 Оплата прошла успешно!\n\n"
        text += f"👤 Профиль: {profile.profile_name}\n"
        text += f"💰 Сумма: {amount} руб.\n"
        text += f"📅 Оплачен месяц: {MONTH_NAMES[month]} {year}\n"
        text += f"✅ Теперь вы можете посещать занятия в этом месяце!"
        
        bot.send_message(
            chat_id=user_telegram_id,
            text=text,
            reply_markup=generate_payment_menu_keyboard()
        )
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")


def notify_admins_about_payment(user: User, month: int, year: int, amount: Decimal, profile: StudentProfile):
    """Уведомляет всех администраторов о новой оплате"""
    try:
        # Получаем всех администраторов
        admins = User.objects.filter(is_admin=True)
        
        if not admins.exists():
            return
        
        text = f"💰 Новая оплата!\n\n"
        text += f"👤 Ученик: {profile.profile_name}\n"
        text += f"🆔 Telegram ID: {user.telegram_id}\n"
        text += f"📚 Класс: {profile.course_or_class}\n"
        text += f"📅 Месяц: {MONTH_NAMES[month]} {year}\n"
        text += f"💰 Сумма: {amount} руб.\n"
        text += f"⏰ Время: {timezone.now().strftime('%d.%m.%Y %H:%M')}"
        
        # Отправляем уведомление каждому администратору
        for admin in admins:
            try:
                bot.send_message(
                    chat_id=admin.telegram_id,
                    text=text
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления администратору {admin.telegram_id}: {e}")
                
    except Exception as e:
        print(f"Ошибка при уведомлении администраторов: {e}")
