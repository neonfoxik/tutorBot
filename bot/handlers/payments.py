from decimal import Decimal
from django.conf import settings
from telebot.types import CallbackQuery, Message
from bot import bot
from bot.models import User, Payment, PaymentHistory
from bot.keyboards import (
    generate_payment_menu_keyboard,
    generate_payment_months_keyboard,
    generate_payment_confirmation_keyboard,
    UNIVERSAL_BUTTONS,
    MONTH_NAMES
)
from bot.pricing import get_price_by_class, TEST_PRICE
from bot.yookassa_client import YooKassaClient


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
    """Начинает процесс оплаты - показывает выбор месяца"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        if not user.is_registered:
            bot.answer_callback_query(call.id, "Сначала завершите регистрацию!")
            return
        
        # Получаем цену для класса пользователя
        price_info = get_price_by_class(user.course_or_class)
        
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
        
        markup = generate_payment_months_keyboard()
        text = f"💳 Оплата занятий\n\n"
        text += f"📚 Ваш класс: {user.course_or_class}\n"
        text += f"💯 Тариф: {price_info['name']}\n"
        text += f"💰 Стоимость: {TEST_PRICE} руб. (тестовый режим)\n"
        text += f"📝 {price_info['description']}\n\n"
        text += "Выберите месяц для оплаты:"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "Пользователь не найден")


def select_payment_month(call: CallbackQuery) -> None:
    """Обработчик выбора месяца для оплаты"""
    try:
        # Парсим callback_data: pay_month_{month}_{year}
        parts = call.data.split('_')
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "Ошибка в данных")
            return
        
        month = int(parts[2])
        year = int(parts[3])
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Проверяем, не оплачен ли уже этот месяц
        if PaymentHistory.is_month_paid(user, month, year):
            bot.answer_callback_query(call.id, f"Месяц {MONTH_NAMES[month]} {year} уже оплачен!")
            return
        
        # Получаем информацию о цене
        price_info = get_price_by_class(user.course_or_class)
        
        if not price_info:
            bot.answer_callback_query(call.id, "Ошибка определения цены")
            return
        
        markup = generate_payment_confirmation_keyboard(month, year)
        text = f"💳 Подтверждение оплаты\n\n"
        text += f"👤 Ученик: {user.full_name}\n"
        text += f"📚 Класс: {user.course_or_class}\n"
        text += f"💯 Тариф: {price_info['name']}\n"
        text += f"📅 Месяц: {MONTH_NAMES[month]} {year}\n"
        text += f"💰 К оплате: {TEST_PRICE} руб. (тестовый режим)\n\n"
        text += "Подтвердите оплату:"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    
    except (ValueError, User.DoesNotExist) as e:
        bot.answer_callback_query(call.id, "Ошибка обработки")


def confirm_payment(call: CallbackQuery) -> None:
    """Подтверждение и создание платежа"""
    try:
        # Парсим callback_data: confirm_payment_{month}_{year}
        parts = call.data.split('_')
        if len(parts) != 4:
            bot.answer_callback_query(call.id, "Ошибка в данных")
            return
        
        month = int(parts[2])
        year = int(parts[3])
        
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Проверяем повторно, не оплачен ли месяц
        if PaymentHistory.is_month_paid(user, month, year):
            bot.answer_callback_query(call.id, "Этот месяц уже оплачен!")
            return
        
        # Получаем информацию о цене
        price_info = get_price_by_class(user.course_or_class)
        
        if not price_info:
            bot.answer_callback_query(call.id, "Ошибка определения цены")
            return
        
        # Создаем платеж через ЮKassa
        yookassa_client = YooKassaClient()
        
        amount = Decimal(str(TEST_PRICE))  # Используем тестовую цену
        description = f"Оплата занятий за {MONTH_NAMES[month]} {year} - {price_info['name']}"
        
        metadata = {
            "user_id": user.telegram_id,
            "month": month,
            "year": year,
            "pricing_plan": price_info['key']
        }
        
        print(f"Создаем платеж для пользователя {user.telegram_id}")
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
            yookassa_payment_id=yookassa_response['id'],
            amount=amount,
            status=yookassa_response['status'],
            description=description,
            payment_month=month,
            payment_year=year,
            pricing_plan=price_info['key']
        )
        
        # Получаем ссылку для оплаты
        payment_url = yookassa_response['confirmation']['confirmation_url']
        
        # Создаем клавиатуру с ссылкой на оплату
        from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
        markup = InlineKeyboardMarkup()
        pay_btn = InlineKeyboardButton("💳 Перейти к оплате", url=payment_url)
        back_btn = InlineKeyboardButton("⬅️ Назад", callback_data="payment_menu")
        markup.add(pay_btn).add(back_btn)
        
        text = f"✅ Платеж создан!\n\n"
        text += f"💰 Сумма: {amount} руб.\n"
        text += f"📅 За месяц: {MONTH_NAMES[month]} {year}\n"
        text += f"💯 Тариф: {price_info['name']}\n\n"
        text += "Нажмите кнопку ниже для перехода к оплате.\n"
        text += "После успешной оплаты вам придет уведомление."
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            text=text,
            reply_markup=markup,
            message_id=call.message.message_id
        )
    
    except (ValueError, User.DoesNotExist) as e:
        bot.answer_callback_query(call.id, "Ошибка обработки")


def payment_history(call: CallbackQuery) -> None:
    """Показывает историю платежей пользователя"""
    try:
        user = User.objects.get(telegram_id=str(call.from_user.id))
        
        # Получаем историю оплаченных месяцев
        history = PaymentHistory.objects.filter(user=user).order_by('-year', '-month')
        
        text = "📊 История оплат\n\n"
        
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


def notify_payment_success(user_telegram_id: str, month: int, year: int, amount: Decimal):
    """Уведомляет пользователя об успешной оплате"""
    try:
        text = f"🎉 Оплата прошла успешно!\n\n"
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