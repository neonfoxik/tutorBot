from functools import wraps
from datetime import datetime

from django.conf import settings
from telebot.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from bot.keyboards import (
    ADMIN_MARKUP,
    generate_students_pagination_keyboard,
    generate_admin_payment_months_keyboard,
    generate_student_info_keyboard,
    generate_payment_history_keyboard
)
from bot import bot, logger
from bot.models import User, Payment, PaymentHistory
from bot.pricing import get_price_by_class


def admin_permission(func):
    """
    Checking user for admin permission to access the function.
    """

    @wraps(func)
    def wrapped(message: Message) -> None:
        user_id = message.from_user.id
        user = User.objects.get(telegram_id=user_id)
        if not user.is_admin:
            bot.send_message(user_id, '⛔ У вас нет администраторского доступа')
            logger.warning(f'Попытка доступа к админ панели от {user_id}')
            return
        return func(message)

    return wrapped


def admin_permission_callback(func):
    """
    Checking user for admin permission to access the callback function.
    """

    @wraps(func)
    def wrapped(call: CallbackQuery) -> None:
        user_id = call.from_user.id
        try:
            user = User.objects.get(telegram_id=user_id)
            if not user.is_admin:
                bot.answer_callback_query(call.id, '⛔ У вас нет администраторского доступа')
                logger.warning(f'Попытка доступа к админ панели от {user_id}')
                return
            return func(call)
        except User.DoesNotExist:
            bot.answer_callback_query(call.id, '⛔ Пользователь не найден')
            return
    return wrapped


@admin_permission
def admin_menu(msg: Message):
    bot.send_message(msg.from_user.id, 'Админ панель', reply_markup=ADMIN_MARKUP)


@admin_permission_callback
def admin_menu_callback(call: CallbackQuery):
    """Обработчик для возврата в админ меню из callback"""
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text='Админ панель',
        reply_markup=ADMIN_MARKUP
    )


@admin_permission_callback
def handle_view_students(call: CallbackQuery):
    """Показывает список учеников с пагинацией для просмотра"""
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите ученика для просмотра информации:",
        reply_markup=generate_students_pagination_keyboard()
    )


@admin_permission_callback
def handle_students_page(call: CallbackQuery):
    """Обработчик пагинации списка учеников"""
    # Получаем номер страницы из callback_data
    page = int(call.data.split('_')[2])
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите ученика для просмотра информации:",
        reply_markup=generate_students_pagination_keyboard(page=page)
    )


@admin_permission_callback
def handle_select_student(call: CallbackQuery):
    """Обработчик выбора ученика для просмотра информации"""
    try:
        # Получаем ID ученика из callback_data
        logger.info(f"Callback data: {call.data}")
        student_id = call.data.split('_')[2].strip()
        logger.info(f"Student ID: '{student_id}'")
        
        # Проверяем, что ID не пустой и не является служебным словом
        if not student_id or student_id in ['student', 'admin', 'user']:
            bot.answer_callback_query(call.id, "❌ Неверный ID ученика")
            logger.error(f"Неверный ID ученика: '{student_id}'")
            return
        
        student = User.objects.get(telegram_id=student_id)
        
        # Получаем информацию об оплатах ученика
        payments = PaymentHistory.objects.filter(user=student, status='completed').order_by('year', 'month')
        
        # Определяем текущий месяц и год
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Проверяем, оплачен ли текущий месяц
        current_month_paid = payments.filter(month=current_month, year=current_year).exists()
        
        # Находим последний оплаченный месяц
        last_paid_month = None
        if payments.exists():
            last_payment = payments.last()
            last_paid_month = f"{last_payment.month}/{last_payment.year}"
        
        # Формируем текст сообщения
        message_text = f"👤 Информация об ученике:\n\n"
        message_text += f"ФИО: {student.full_name or 'Не указано'}\n"
        message_text += f"Telegram ID: {student.telegram_id}\n"
        message_text += f"Дата регистрации: {student.register_date.strftime('%d.%m.%Y')}\n\n"
        
        message_text += f"💰 Статус оплаты:\n"
        message_text += f"Текущий месяц ({current_month}/{current_year}): "
        message_text += "✅ Оплачен" if current_month_paid else "❌ Не оплачен"
        message_text += f"\nПоследний оплаченный месяц: {last_paid_month or 'Нет оплат'}\n\n"
        
        message_text += f"📊 Всего оплат: {payments.count()}"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=generate_student_info_keyboard(student_id)
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Ученик не найден")
        logger.error(f"Ученик с ID {student_id} не найден при выборе")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        logger.error(f"Ошибка в handle_select_student: {e}")


@admin_permission_callback
def handle_view_payment_history(call: CallbackQuery):
    """Показывает историю оплат ученика"""
    try:
        # Получаем ID ученика из callback_data
        logger.info(f"Callback data: {call.data}")
        parts = call.data.split('_')
        logger.info(f"Split parts: {parts}")
        
        # ID находится на последней позиции
        student_id = parts[-1].strip()
        logger.info(f"Student ID: '{student_id}'")
        
        # Проверяем, что ID не пустой и не является служебным словом
        if not student_id or student_id in ['student', 'admin', 'user']:
            bot.answer_callback_query(call.id, "❌ Неверный ID ученика")
            logger.error(f"Неверный ID ученика: '{student_id}'")
            return
        
        student = User.objects.get(telegram_id=student_id)
        
        # Получаем все оплаты ученика
        payments = PaymentHistory.objects.filter(user=student, status='completed').order_by('year', 'month')
        
        if not payments.exists():
            message_text = f"📊 История оплат ученика {student.full_name or 'Не указано'}:\n\n"
            message_text += "У ученика пока нет оплат."
        else:
            message_text = f"📊 История оплат ученика {student.full_name or 'Не указано'}:\n\n"
            
            for payment in payments:
                month_name = {
                    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
                    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
                    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
                }[payment.month]
                
                message_text += f"📅 {month_name} {payment.year}\n"
                message_text += f"💰 Сумма: {payment.amount_paid} ₽\n"
                message_text += f"💳 Тип: {payment.payment_type}\n"
                message_text += f"📝 Дата: {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=generate_payment_history_keyboard(student_id)
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Ученик не найден")
        logger.error(f"Ученик с ID {student_id} не найден при просмотре истории оплат")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        logger.error(f"Ошибка в handle_view_payment_history: {e}")


@admin_permission_callback
def handle_mark_payment_for_student(call: CallbackQuery):
    """Показывает выбор месяца для отметки оплаты конкретного ученика"""
    try:
        # Получаем ID ученика из callback_data
        logger.info(f"Callback data: {call.data}")
        parts = call.data.split('_')
        logger.info(f"Split parts: {parts}")
        
        # ID находится на последней позиции
        student_id = parts[-1].strip()
        logger.info(f"Student ID: '{student_id}'")
        
        # Проверяем, что ID не пустой и не является служебным словом
        if not student_id or student_id in ['student', 'admin', 'user']:
            bot.answer_callback_query(call.id, "❌ Неверный ID ученика")
            logger.error(f"Неверный ID ученика: '{student_id}'")
            return
        
        student = User.objects.get(telegram_id=student_id)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Выберите месяц оплаты для ученика {student.full_name or 'Не указано'}:",
            reply_markup=generate_admin_payment_months_keyboard(student_id)
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Ученик не найден")
        logger.error(f"Ученик с ID '{student_id}' не найден при попытке отметить оплату")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        logger.error(f"Ошибка в handle_mark_payment_for_student: {e}")


@admin_permission_callback
def handle_mark_student_payment(call: CallbackQuery):
    """Показывает список учеников с пагинацией для отметки оплаты."""
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Выберите ученика для отметки оплаты:",
        reply_markup=generate_students_pagination_keyboard()
    )


@admin_permission_callback
def handle_admin_mark_payment(call: CallbackQuery):
    """Обработчик отметки оплаты администратором"""
    try:
        # Разбираем callback_data
        logger.info(f"Callback data: {call.data}")
        parts = call.data.split('_')
        logger.info(f"Split parts: {parts}")
        
        if len(parts) < 5:
            bot.answer_callback_query(call.id, "❌ Неверный формат данных")
            logger.error(f"Неверный формат callback_data: {call.data}")
            return
        
        student_id = parts[3].strip()
        month = parts[4].strip()
        year = parts[5].strip()
        
        logger.info(f"Student ID: '{student_id}', Month: '{month}', Year: '{year}'")
        
        # Проверяем, что ID не пустой и не является служебным словом
        if not student_id or student_id in ['student', 'admin', 'user']:
            bot.answer_callback_query(call.id, "❌ Неверный ID ученика")
            logger.error(f"Неверный ID ученика: '{student_id}'")
            return
        
        student = User.objects.get(telegram_id=student_id)
        
        # Получаем цену занятия для ученика
        price_info = get_price_by_class(student.course_or_class)
        
        if price_info:
            lesson_price = price_info['price']
            class_name = price_info['name']
        else:
            # Если не удалось определить цену, используем базовую
            lesson_price = 5000
            class_name = "стандартный тариф"
        
        # Создаем запись об оплате
        payment = PaymentHistory.objects.create(
            user=student,
            amount_paid=lesson_price,  # Используем индивидуальную цену занятия
            payment_type='cash',  # Тип оплаты - наличные
            status='completed',  # Статус - завершено
            month=int(month),
            year=int(year),
            pricing_plan=class_name
        )
        
        # Отправляем сообщение админу
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ Оплата успешно отмечена!\n\n"
                 f"Ученик: {student.full_name or 'Не указано'}\n"
                 f"Класс: {class_name}\n"
                 f"Месяц: {month}/{year}\n"
                 f"Сумма: {lesson_price} ₽",
            reply_markup=ADMIN_MARKUP
        )
        
        # Отправляем уведомление ученику
        bot.send_message(
            student.telegram_id,
            f"✅ Администратор отметил вашу оплату за {month}/{year}\n"
            f"Тариф: {class_name}\n"
            f"Сумма: {lesson_price} ₽"
        )
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Ученик не найден")
        logger.error(f"Ученик с ID {student_id} не найден при отметке оплаты")
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
        logger.error(f"Ошибка в handle_admin_mark_payment: {e}")
