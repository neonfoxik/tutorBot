import logging
from datetime import datetime
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.models import User, Payment
from bot.keyboards import build_admin_markup, UNIVERSAL_BUTTONS
from bot import bot
from django.utils import timezone


def admin_permission(func):
    """Декоратор для проверки прав администратора"""
    def wrapper(msg: Message | CallbackQuery, *args, **kwargs):
        try:
            if isinstance(msg, Message):
                user_id = str(msg.from_user.id)
            else:
                user_id = str(msg.from_user.id)
            
            user = User.objects.get(telegram_id=user_id, is_admin=True)
            return func(msg, *args, **kwargs)
        except User.DoesNotExist:
            if isinstance(msg, Message):
                bot.reply_to(msg, "У вас нет прав администратора.")
            else:
                bot.answer_callback_query(msg.id, "У вас нет прав администратора.")
        except Exception as e:
            logging.error(f"Ошибка в admin_permission: {e}")
            if isinstance(msg, Message):
                bot.reply_to(msg, "Произошла ошибка.")
            else:
                bot.answer_callback_query(msg.id, "Произошла ошибка.")
    return wrapper


@admin_permission
def admin_menu(msg: Message | CallbackQuery):
    """Главное меню админ-панели"""
    try:
        if isinstance(msg, Message):
            bot.reply_to(msg, "🔧 Админ-панель", reply_markup=build_admin_markup())
        else:
            bot.edit_message_text(
                "🔧 Админ-панель",
                msg.message.chat.id,
                msg.message.message_id,
                reply_markup=build_admin_markup()
            )
            bot.answer_callback_query(msg.id)
    except Exception as e:
        logging.error(f"Ошибка в admin_menu: {e}")


@admin_permission
def admin_list_all(call: CallbackQuery):
    """Список всех клиентов"""
    try:
        users = User.objects.all().order_by('-created_at')
        
        if not users:
            text = "📝 Список клиентов пуст"
        else:
            text = "👥 <b>Все клиенты:</b>\n\n"
            for user in users[:20]:  # Ограничиваем 20 пользователями
                status = "✅ Оплачено" if user.is_paid_current_month else "❌ Не оплачено"
                text += f"• {user.full_name or user.user_name or 'Без имени'} ({user.user_tg_name})\n"
                text += f"  🎓 {user.grade or 'Не указан'}, 🏫 {user.school or 'Не указано'}\n"
                text += f"  💳 {status}\n\n"
            
            if len(users) > 20:
                text += f"... и еще {len(users) - 20} клиентов"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Ошибка в admin_list_all: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


@admin_permission
def admin_list_paid(call: CallbackQuery):
    """Список оплативших клиентов"""
    try:
        users = User.objects.filter(is_paid_current_month=True).order_by('-last_payment_at')
        
        if not users:
            text = "✅ Нет оплативших клиентов"
        else:
            text = "✅ <b>Оплатившие клиенты:</b>\n\n"
            for user in users[:20]:
                text += f"• {user.full_name or user.user_name or 'Без имени'} ({user.user_tg_name})\n"
                text += f"  💰 Последняя оплата: {user.last_payment_at.strftime('%d.%m.%Y') if user.last_payment_at else 'Не указана'}\n\n"
            
            if len(users) > 20:
                text += f"... и еще {len(users) - 20} клиентов"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Ошибка в admin_list_paid: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


@admin_permission
def admin_list_unpaid(call: CallbackQuery):
    """Список неоплативших клиентов"""
    try:
        users = User.objects.filter(is_paid_current_month=False).order_by('-created_at')
        
        if not users:
            text = "❌ Нет неоплативших клиентов"
        else:
            text = "❌ <b>Неоплатившие клиенты:</b>\n\n"
            for user in users[:20]:
                text += f"• {user.full_name or user.user_name or 'Без имени'} ({user.user_tg_name})\n"
                text += f"  🎓 {user.grade or 'Не указан'}, 🏫 {user.school or 'Не указано'}\n\n"
            
            if len(users) > 20:
                text += f"... и еще {len(users) - 20} клиентов"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Ошибка в admin_list_unpaid: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


@admin_permission
def admin_pending_payments(call: CallbackQuery):
    """Список неподтвержденных платежей"""
    try:
        payments = Payment.objects.filter(status=Payment.Status.PENDING).order_by('-created_at')
        
        if not payments:
            text = "💼 Нет неподтвержденных платежей"
        else:
            text = "💼 <b>Неподтвержденные платежи:</b>\n\n"
            for payment in payments[:10]:
                text += f"• ID: {payment.id}\n"
                text += f"  👤 {payment.user.full_name or payment.user.user_name or 'Без имени'}\n"
                text += f"  💰 {payment.amount} ₽\n"
                text += f"  📅 {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                text += f"  📝 {payment.description}\n\n"
            
            text += "Для подтверждения используйте команды:\n"
            text += "/accept_<ID> - принять платеж\n"
            text += "/decline_<ID> - отклонить платеж"
            
            if len(payments) > 10:
                text += f"\n\n... и еще {len(payments) - 10} платежей"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Ошибка в admin_pending_payments: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


@admin_permission
def admin_send_reminders(call: CallbackQuery):
    """Отправка напоминаний об оплате"""
    try:
        unpaid_users = User.objects.filter(is_paid_current_month=False)
        sent_count = 0
        
        for user in unpaid_users:
            try:
                bot.send_message(
                    user.telegram_id,
                    "🔔 Напоминание об оплате!\n\n"
                    "Не забудьте оплатить обучение за текущий месяц.\n"
                    "Используйте кнопку 'Оплата' в главном меню."
                )
                sent_count += 1
            except Exception as e:
                logging.error(f"Ошибка при отправке напоминания пользователю {user.user_tg_name}: {e}")
        
        text = f"📤 Напоминания отправлены!\n\n✅ Отправлено: {sent_count}\n❌ Ошибок: {len(unpaid_users) - sent_count}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="admin_menu"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Ошибка в admin_send_reminders: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


@admin_permission
def newsletter(call: CallbackQuery):
    """Рассылка сообщений всем пользователям"""
    try:
        bot.edit_message_text(
            "📣 <b>Рассылка</b>\n\n"
            "Отправьте сообщение для рассылки всем пользователям:",
            call.message.chat.id,
            call.message.message_id,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
        
        # Регистрируем следующий шаг для получения текста рассылки
        bot.register_next_step_handler(call.message, handle_message)
    except Exception as e:
        logging.error(f"Ошибка в newsletter: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")


@admin_permission
def handle_message(msg: Message):
    """Обработчик текста для рассылки"""
    try:
        users = User.objects.all()
        sent_count = 0
        error_count = 0
        
        for user in users:
            try:
                bot.send_message(user.telegram_id, msg.text)
                sent_count += 1
            except Exception as e:
                logging.error(f"Ошибка при отправке рассылки пользователю {user.user_tg_name}: {e}")
                error_count += 1
        
        result_text = f"📤 Рассылка завершена!\n\n✅ Отправлено: {sent_count}\n❌ Ошибок: {error_count}"
        
        bot.reply_to(msg, result_text, reply_markup=build_admin_markup())
    except Exception as e:
        logging.error(f"Ошибка в handle_message: {e}")
        bot.reply_to(msg, "Произошла ошибка при рассылке")


def accept_payment(message: Message):
    """Команда для подтверждения платежа"""
    try:
        # Проверяем права администратора
        user = User.objects.get(
            telegram_id=str(message.from_user.id),
            is_admin=True
        )
        
        # Парсим ID платежа из команды /accept_<ID>
        parts = message.text.split('_')
        if len(parts) != 2:
            bot.reply_to(message, "Используйте формат: /accept_<ID_платежа>")
            return
        
        try:
            payment_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "Неверный ID платежа")
            return
        
        # Находим и подтверждаем платеж
        payment = Payment.objects.get(id=payment_id, status=Payment.Status.PENDING)
        payment.status = Payment.Status.MANUAL
        payment.confirmed_at = timezone.now()
        payment.admin_comment = f"Подтвержден админом {user.user_tg_name}"
        payment.save()
        
        # Обновляем статус пользователя
        payment.user.is_paid_current_month = True
        payment.user.last_payment_at = timezone.now()
        payment.user.save()
        
        # Уведомляем пользователя
        try:
            bot.send_message(
                payment.user.telegram_id,
                f"✅ Ваш платеж на сумму {payment.amount} ₽ подтвержден!\n"
                f"Спасибо за оплату обучения."
            )
        except Exception as e:
            logging.error(f"Ошибка при уведомлении пользователя: {e}")
        
        bot.reply_to(message, f"✅ Платеж {payment_id} подтвержден!")
        
    except User.DoesNotExist:
        bot.reply_to(message, "У вас нет прав администратора")
    except Payment.DoesNotExist:
        bot.reply_to(message, f"Платеж {payment_id} не найден или уже обработан")
    except Exception as e:
        logging.error(f"Ошибка в accept_payment_cmd: {e}")
        bot.reply_to(message, "Произошла ошибка при подтверждении платежа")


def decline_payment(message: Message):
    """Команда для отклонения платежа"""
    try:
        # Проверяем права администратора
        user = User.objects.get(
            telegram_id=str(message.from_user.id),
            is_admin=True
        )
        
        # Парсим ID платежа из команды /decline_<ID>
        parts = message.text.split('_')
        if len(parts) != 2:
            bot.reply_to(message, "Используйте формат: /decline_<ID_платежа>")
            return
        
        try:
            payment_id = int(parts[1])
        except ValueError:
            bot.reply_to(message, "Неверный ID платежа")
            return
        
        # Находим и отклоняем платеж
        payment = Payment.objects.get(id=payment_id, status=Payment.Status.PENDING)
        payment.status = Payment.Status.FAILED
        payment.admin_comment = f"Отклонен админом {user.user_tg_name}"
        payment.save()
        
        # Уведомляем пользователя
        try:
            bot.send_message(
                payment.user.telegram_id,
                f"❌ Ваш платеж на сумму {payment.amount} ₽ отклонен.\n"
                f"Пожалуйста, повторите оплату или свяжитесь с администратором."
            )
        except Exception as e:
            logging.error(f"Ошибка при уведомлении пользователя: {e}")
        
        bot.reply_to(message, f"❌ Платеж {payment_id} отклонен!")
        
    except User.DoesNotExist:
        bot.reply_to(message, "У вас нет прав администратора")
    except Payment.DoesNotExist:
        bot.reply_to(message, f"Платеж {payment_id} не найден или уже обработан")
    except Exception as e:
        logging.error(f"Ошибка в decline_payment_cmd: {e}")
        bot.reply_to(message, "Произошла ошибка при отклонении платежа")