import logging
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.models import User, BriefQuestion, UserBriefComplete
from bot import bot
from django.db import transaction


def start_brief(message: Message | CallbackQuery):
    """Начинает процесс заполнения бриф"""
    try:
        if isinstance(message, Message):
            user_id = str(message.from_user.id)
            msg = message
        else:
            user_id = str(message.from_user.id)
            msg = message.message
        
        user = User.objects.get(telegram_id=user_id)
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            if isinstance(message, Message):
                bot.reply_to(
                    message,
                    "⚠️ <b>Для заполнения брифа необходимо завершить регистрацию</b>\n\n"
                    "Пожалуйста, заполните следующие данные:\n"
                    f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                    f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                    f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                    "Нажмите кнопку ниже для завершения регистрации:",
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            else:
                bot.edit_message_text(
                    "⚠️ <b>Для заполнения брифа необходимо завершить регистрацию</b>\n\n"
                    "Пожалуйста, заполните следующие данные:\n"
                    f"✅ ФИО: {'Заполнено' if user.full_name else '❌ Не заполнено'}\n"
                    f"✅ Школа/ВУЗ: {'Заполнено' if user.school else '❌ Не заполнено'}\n"
                    f"✅ Класс/Курс: {'Заполнено' if user.grade else '❌ Не заполнено'}\n\n"
                    "Нажмите кнопку ниже для завершения регистрации:",
                    message.message.chat.id,
                    message.message.message_id,
                    reply_markup=markup,
                    parse_mode='HTML'
                )
            return
        
        # Проверяем, не заполнен ли уже бриф
        if user.brief_completed:
            bot.reply_to(message, "✅ Вы уже заполнили бриф!")
            return
        
        # Получаем первый активный вопрос
        first_question = BriefQuestion.objects.filter(is_active=True).order_by('order').first()
        
        if not first_question:
            bot.reply_to(message, "❌ В данный момент нет доступных вопросов для бриф")
            return
        
        # Создаем или получаем объект полного брифа
        brief, _ = UserBriefComplete.objects.get_or_create(
            user=user,
            defaults={'brief_data': []}
        )
        
        # Сохраняем состояние пользователя (какой вопрос он заполняет)
        user.current_brief_question = first_question.order
        user.save()
        
        # Отправляем первый вопрос
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Отменить", callback_data="cancel_brief"))
        
        if isinstance(message, Message):
            bot.reply_to(
                message,
                f"📝 <b>Бриф - Вопрос {first_question.order}</b>\n\n{first_question.question_text}",
                reply_markup=markup,
                parse_mode='HTML'
            )
            # Регистрируем следующий шаг для получения ответа
            bot.register_next_step_handler(message, handle_brief_answer, first_question.order)
        else:
            bot.edit_message_text(
                f"📝 <b>Бриф - Вопрос {first_question.order}</b>\n\n{first_question.question_text}",
                message.message.chat.id,
                message.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            # Для callback query нужно отправить новое сообщение
            bot.send_message(
                message.message.chat.id,
                "Теперь отправьте ваш ответ на вопрос:",
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отменить", callback_data="cancel_brief"))
            )
            # Регистрируем следующий шаг для получения ответа
            bot.register_next_step_handler(message.message, handle_brief_answer, first_question.order)
        
    except User.DoesNotExist:
        if isinstance(message, Message):
            bot.reply_to(message, "❌ Пользователь не найден. Сначала зарегистрируйтесь.")
        else:
            bot.answer_callback_query(message.id, "❌ Пользователь не найден. Сначала зарегистрируйтесь.")
    except Exception as e:
        logging.error(f"Ошибка в start_brief: {e}")
        if isinstance(message, Message):
            bot.reply_to(message, "❌ Произошла ошибка при запуске бриф")
        else:
            bot.answer_callback_query(message.id, "❌ Произошла ошибка при запуске бриф")


def handle_brief_answer(message: Message, current_question_order: int):
    """Обрабатывает ответ пользователя на вопрос бриф"""
    try:
        user_id = str(message.from_user.id)
        user = User.objects.get(telegram_id=user_id)
        
        # Получаем текущий вопрос
        current_question = BriefQuestion.objects.get(order=current_question_order, is_active=True)
        
        # Получаем или создаем объект полного брифа
        brief, _ = UserBriefComplete.objects.get_or_create(
            user=user,
            defaults={'brief_data': []}
        )
        
        # Обновляем или добавляем ответ в brief_data
        brief_data = brief.brief_data
        answer_exists = False
        for item in brief_data:
            if item['order'] == current_question_order:
                item['question'] = current_question.question_text
                item['answer'] = message.text
                answer_exists = True
                break
        
        if not answer_exists:
            brief_data.append({
                'order': current_question_order,
                'question': current_question.question_text,
                'answer': message.text
            })
        
        # Сохраняем обновленные данные
        brief.brief_data = sorted(brief_data, key=lambda x: x['order'])
        brief.save()
        
        # Получаем следующий вопрос
        next_question = BriefQuestion.objects.filter(
            is_active=True,
            order__gt=current_question_order
        ).order_by('order').first()
        
        if next_question:
            # Есть следующий вопрос
            user.current_brief_question = next_question.order
            user.save()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Отменить", callback_data="cancel_brief"))
            
            bot.reply_to(
                message,
                f"📝 <b>Бриф - Вопрос {next_question.order}</b>\n\n{next_question.question_text}",
                reply_markup=markup,
                parse_mode='HTML'
            )
            
            # Регистрируем следующий шаг
            bot.register_next_step_handler(message, handle_brief_answer, next_question.order)
            
        else:
            # Бриф завершен
            with transaction.atomic():
                user.brief_completed = True
                user.current_brief_question = None
                user.save()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
            
            # Формируем итоговый текст брифа
            summary_text = "🎉 <b>Поздравляем! Вы успешно заполнили бриф!</b>\n\n"
            summary_text += "Ваши ответы:\n\n"
            for item in brief.brief_data:
                summary_text += f"<b>Вопрос {item['order']}:</b> {item['question']}\n"
                summary_text += f"<b>Ответ:</b> {item['answer']}\n\n"
            
            bot.reply_to(
                message,
                summary_text,
                reply_markup=markup,
                parse_mode='HTML'
            )
            
    except User.DoesNotExist:
        bot.reply_to(message, "❌ Пользователь не найден.")
    except BriefQuestion.DoesNotExist:
        bot.reply_to(message, "❌ Вопрос не найден.")
    except Exception as e:
        logging.error(f"Ошибка в handle_brief_answer: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке ответа")


def cancel_brief(call: CallbackQuery):
    """Отменяет заполнение бриф"""
    try:
        user_id = str(call.from_user.id)
        user = User.objects.get(telegram_id=user_id)
        
        # Сбрасываем состояние бриф
        user.current_brief_question = None
        user.save()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
        
        bot.edit_message_text(
            "❌ Заполнение бриф отменено.\n\n"
            "Вы можете заполнить его позже в разделе профиля.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
        
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в cancel_brief: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


def show_brief_progress(call: CallbackQuery):
    """Показывает прогресс заполнения бриф"""
    try:
        user_id = str(call.from_user.id)
        user = User.objects.get(telegram_id=user_id)
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.edit_message_text(
                "⚠️ <b>Для доступа к брифу необходимо завершить регистрацию</b>\n\n"
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
        
        if user.brief_completed:
            # Получаем заполненный бриф
            brief = UserBriefComplete.objects.get(user=user)
            text = "✅ <b>Бриф полностью заполнен!</b>\n\n"
            text += "Ваши ответы:\n\n"
            for item in brief.brief_data:
                text += f"<b>Вопрос {item['order']}:</b> {item['question']}\n"
                text += f"<b>Ответ:</b> {item['answer']}\n\n"
        else:
            # Подсчитываем прогресс
            total_questions = BriefQuestion.objects.filter(is_active=True).count()
            brief = UserBriefComplete.objects.filter(user=user).first()
            answered_questions = len(brief.brief_data) if brief else 0
            
            if total_questions == 0:
                text = "❌ <b>В данный момент нет доступных вопросов для бриф</b>"
            else:
                progress_percent = (answered_questions / total_questions) * 100
                text = f"📊 <b>Прогресс заполнения бриф</b>\n\n"
                text += f"Заполнено: {answered_questions} из {total_questions} вопросов\n"
                text += f"Прогресс: {progress_percent:.1f}%"
                
                if answered_questions > 0:
                    text += "\n\nВаши ответы:\n\n"
                    for item in brief.brief_data:
                        text += f"<b>Вопрос {item['order']}:</b> {item['question']}\n"
                        text += f"<b>Ответ:</b> {item['answer']}\n\n"
                    text += f"\nПродолжить заполнение?"
        
        markup = InlineKeyboardMarkup()
        
        if not user.brief_completed and total_questions > 0:
            if answered_questions == 0:
                markup.add(InlineKeyboardButton("📝 Начать бриф", callback_data="start_brief"))
            else:
                markup.add(InlineKeyboardButton("📝 Продолжить бриф", callback_data="continue_brief"))
        
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="profile"))
        
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        bot.answer_callback_query(call.id)
        
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в show_brief_progress: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")


def continue_brief(call: CallbackQuery):
    """Продолжает заполнение бриф с того места, где остановился пользователь"""
    try:
        user_id = str(call.from_user.id)
        user = User.objects.get(telegram_id=user_id)
        
        # Проверяем, завершена ли регистрация
        if not user.full_name or not user.school or not user.grade:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📝 Завершить регистрацию", callback_data="start_registration"))
            
            bot.edit_message_text(
                "⚠️ <b>Для доступа к брифу необходимо завершить регистрацию</b>\n\n"
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
        
        if user.brief_completed:
            bot.answer_callback_query(call.id, "✅ Бриф уже заполнен!")
            return
        
        # Получаем или создаем объект полного брифа
        brief, _ = UserBriefComplete.objects.get_or_create(
            user=user,
            defaults={'brief_data': []}
        )
        
        # Находим следующий неотвеченный вопрос
        answered_orders = [item['order'] for item in brief.brief_data]
        next_question = BriefQuestion.objects.filter(
            is_active=True
        ).exclude(
            order__in=answered_orders
        ).order_by('order').first()
        
        if not next_question:
            # Все вопросы отвечены, но флаг не установлен
            with transaction.atomic():
                user.brief_completed = True
                user.save()
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu"))
            
            # Формируем итоговый текст брифа
            text = "🎉 <b>Поздравляем! Вы успешно заполнили бриф!</b>\n\n"
            text += "Ваши ответы:\n\n"
            for item in brief.brief_data:
                text += f"<b>Вопрос {item['order']}:</b> {item['question']}\n"
                text += f"<b>Ответ:</b> {item['answer']}\n\n"
            
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            return
        
        # Отправляем следующий вопрос
        user.current_brief_question = next_question.order
        user.save()
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Отменить", callback_data="cancel_brief"))
        
        bot.edit_message_text(
            f"📝 <b>Бриф - Вопрос {next_question.order}</b>\n\n{next_question.question_text}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode='HTML'
        )
        
        # Регистрируем следующий шаг
        bot.register_next_step_handler(call.message, handle_brief_answer, next_question.order)
        bot.answer_callback_query(call.id)
        
    except User.DoesNotExist:
        bot.answer_callback_query(call.id, "❌ Пользователь не найден")
    except Exception as e:
        logging.error(f"Ошибка в continue_brief: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка") 