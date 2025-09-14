from datetime import datetime
import json
from traceback import format_exc

from asgiref.sync import sync_to_async
from django.shortcuts import render
from bot.handlers import *
from django.conf import settings
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from telebot.apihelper import ApiTelegramException
from telebot.types import Update
import telebot

from bot import bot, logger
from bot.handlers.admin.admin import (
    admin_menu,
    admin_menu_callback,
    handle_view_students,
    handle_students_page,
    handle_select_student,
    handle_view_payment_history,
    handle_mark_payment_for_student,
    handle_admin_payment_method_selection,
    handle_admin_text_input,
    handle_mark_student_payment,
    handle_admin_mark_payment
)

from .models import PaymentHistory, User

# Регистрируем обработчики команд
# Обработчик команды /start (должен быть первым!)
@bot.message_handler(commands=['start'])
def handle_start_command(message):
    """Обработчик команды /start"""
    logger.info(f"Start command received from user {message.from_user.id}")
    from bot.handlers.common import start
    start(message)

bot.register_message_handler(admin_menu, commands=['admin'])

# Регистрируем callback обработчики для просмотра учеников
bot.register_callback_query_handler(
    handle_view_students,
    func=lambda call: call.data == "view_students"
)

bot.register_callback_query_handler(
    handle_students_page,
    func=lambda call: call.data.startswith("students_page_")
)

bot.register_callback_query_handler(
    handle_select_student,
    func=lambda call: call.data.startswith("select_student_")
)

bot.register_callback_query_handler(
    handle_view_payment_history,
    func=lambda call: call.data.startswith("view_payment_history_")
)

bot.register_callback_query_handler(
    handle_mark_payment_for_student,
    func=lambda call: call.data.startswith("mark_payment_for_student_")
)

# Регистрируем callback обработчики для отметки оплаты
bot.register_callback_query_handler(
    handle_mark_student_payment,
    func=lambda call: call.data == "mark_student_payment"
)

bot.register_callback_query_handler(
    handle_admin_mark_payment,
    func=lambda call: call.data.startswith("admin_mark_payment_")
)

# Регистрируем обработчики для выбора способа оплаты админом
bot.register_callback_query_handler(
    handle_admin_payment_method_selection,
    func=lambda call: call.data.startswith("admin_month_payment_") or call.data.startswith("admin_balance_payment_")
)

# Регистрируем обработчик текстовых сообщений от админов (кроме команд)
bot.register_message_handler(
    handle_admin_text_input,
    func=lambda msg: not msg.text.startswith('/') and User.objects.filter(telegram_id=str(msg.from_user.id), is_admin=True).exists()
)


def payment_info(request):
    all_users = User.objects.all()

    if request.method == 'POST':
        course = request.POST.get('course', '*')
        if course != "*":
            all_users = all_users.filter(course_or_class=course)

    years = set(PaymentHistory.objects.values_list('year', flat=True))
    if len(years) == 0:
        years = [datetime.now().year]
    all_info = []
    total_income = 0
    for year in years:
        year_info = {
            'date': year,
            'months': [
            {'title': 'Декабрь', 'id': 12, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False},
            {'title': 'Ноябрь', 'id': 11, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Октябрь', 'id': 10, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Сентябрь', 'id': 9, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Август', 'id': 8, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Июль', 'id': 7, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Июнь', 'id': 6, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Май', 'id': 5, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False},
            {'title': 'Апрель', 'id': 4, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Март', 'id': 3, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Февраль', 'id': 2, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
            {'title': 'Январь', 'id': 1, 'paid_users': [], 'unpaid_users': [], 'payers_count': 0, 'all_users': 0, 'is_paid': False}, 
        ]}

        for month in year_info['months']:
            for user in all_users:
                if user.register_date.month <= month['id']:
                    if PaymentHistory.objects.filter(month=month["id"], year=year, user__telegram_id=user.telegram_id).count() > 0:
                        month['payers_count'] += 1
                        month['is_paid'] = True
                        user.payment = PaymentHistory.objects.get(month=month["id"], year=year, user=user)
                        month['paid_users'].append(PaymentHistory.objects.get(month=month["id"], year=year, user=user))
                        total_income += PaymentHistory.objects.get(month=month["id"], year=year, user=user).amount_paid
                    else:
                        month['unpaid_users'].append(user)

                month['all_users'] += 1
            month['all_students'] = month['paid_users'] + month['unpaid_users']
        all_info.append(year_info)
    return render(request, 'templates_info.html', context={
        'all_info': all_info,
        'now_year': datetime.now().year,
        'now_month': datetime.now().month,
        'total_students': all_users.count(),
        'total_income': total_income
    })


@csrf_exempt
def index(request):
    if request.method == "POST":
        json_str = request.body.decode('UTF-8')
        logger.info(f"Received webhook data: {json_str}")
        
        update = telebot.types.Update.de_json(json_str)
        logger.info(f"Parsed update: {update}")
        
        try:
            bot.process_new_updates([update])
            logger.info("Successfully processed update")
        except Exception as e:
            logger.error(f"Error processing update: {e}")
            logger.error(f"Traceback: {format_exc()}")
        
        return HttpResponse("")
    return HttpResponse("Bot is running")


@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    """Setting webhook."""
    try:
        # Удаляем старый webhook перед установкой нового
        bot.remove_webhook()
        
        # Устанавливаем новый webhook
        bot.set_webhook(url=f"{settings.HOOK}/bot/{settings.BOT_TOKEN}")
        bot.send_message(settings.OWNER_ID, "webhook set")
        return JsonResponse({"message": "Webhook set successfully"}, status=200)
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return JsonResponse({"message": f"Error setting webhook: {str(e)}"}, status=500)


@require_GET
def status(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"message": "OK"}, status=200)


@require_GET
def start_polling(request: HttpRequest) -> JsonResponse:
    """Start bot with long polling instead of webhook."""
    try:
        # Удаляем webhook если он был установлен
        bot.remove_webhook()
        
        # Запускаем long polling в фоне
        import threading
        def run_polling():
            try:
                bot.infinity_polling(timeout=10, long_polling_timeout=5)
            except Exception as e:
                logger.error(f"Polling error: {e}")
        
        polling_thread = threading.Thread(target=run_polling, daemon=True)
        polling_thread.start()
        
        return JsonResponse({"message": "Bot started with long polling"}, status=200)
    except Exception as e:
        logger.error(f"Error starting polling: {e}")
        return JsonResponse({"message": f"Error starting polling: {str(e)}"}, status=500)


"""Common"""

# Обработчик команды /start удален - используется тестовый обработчик выше

bot.register_callback_query_handler(menu_call, func=lambda c: c.data == "main_menu")
bot.register_callback_query_handler(profile, func=lambda c: c.data == "profile")

# Обработчики для регистрации
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_all_messages(message):
    """Обрабатывает все текстовые сообщения для регистрации (кроме команд)"""
    from bot.handlers.registration import handle_registration_message
    handle_registration_message(message)

# Обработчики для выбора места учебы
@bot.callback_query_handler(func=lambda call: call.data.startswith("education_"))
def handle_education_selection(call):
    """Обрабатывает выбор места учебы"""
    from bot.handlers.registration import handle_education_choice
    handle_education_choice(call)

# Обработчики для выбора курса
@bot.callback_query_handler(func=lambda call: call.data.startswith("course_"))
def handle_course_selection(call):
    """Обрабатывает выбор курса"""
    from bot.handlers.registration import handle_course_or_class_choice
    handle_course_or_class_choice(call)

# Обработчики для выбора класса
@bot.callback_query_handler(func=lambda call: call.data.startswith("class_"))
def handle_class_selection(call):
    """Обрабатывает выбор класса"""
    from bot.handlers.registration import handle_course_or_class_choice
    handle_course_or_class_choice(call)

# Обработчики платежей
payment_menu = bot.callback_query_handler(lambda c: c.data == "payment_menu")(payment_menu)
start_payment = bot.callback_query_handler(lambda c: c.data == "start_payment")(start_payment)
payment_history = bot.callback_query_handler(lambda c: c.data == "payment_history")(payment_history)

# Обработчик для возврата в админ меню
admin_menu_callback_handler = bot.callback_query_handler(lambda c: c.data == "admin_menu")(admin_menu_callback)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_month_"))
def handle_payment_month_selection(call):
    """Обрабатывает выбор месяца для оплаты"""
    from bot.handlers.payments import select_payment_month
    select_payment_month(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_payment_"))
def handle_payment_confirmation(call):
    """Обрабатывает подтверждение платежа"""
    from bot.handlers.payments import confirm_payment
    confirm_payment(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_payment_"))
def handle_payment_check(call):
    """Обрабатывает проверку оплаты"""
    from bot.handlers.payments import check_payment
    check_payment(call)

@bot.callback_query_handler(func=lambda call: call.data in ["pay_with_yookassa", "pay_with_balance"])
def handle_payment_method_selection(call):
    """Обрабатывает выбор способа оплаты"""
    from bot.handlers.payments import select_payment_method
    select_payment_method(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_balance_month_"))
def handle_balance_payment_month_selection(call):
    """Обрабатывает выбор месяца для оплаты с баланса"""
    from bot.handlers.payments import select_balance_payment_month
    select_balance_payment_month(call)
