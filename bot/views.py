import json
from traceback import format_exc

from asgiref.sync import sync_to_async
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
    handle_view_students,
    handle_students_page,
    handle_select_student,
    handle_view_payment_history,
    handle_mark_payment_for_student,
    handle_mark_student_payment,
    handle_admin_mark_payment
)

# Регистрируем обработчики команд
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

@csrf_exempt
def index(request):
    if request.method == "POST":
        json_str = request.body.decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return HttpResponse("")
    return HttpResponse("Bot is running")


@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    """Setting webhook."""
    try:
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

start = bot.message_handler(commands=["start"])(start)
menu_call = bot.callback_query_handler(lambda c: c.data == "main_menu")(menu_call)
profile = bot.callback_query_handler(lambda c: c.data == "profile")(profile)

# Обработчики для регистрации
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обрабатывает все текстовые сообщения для регистрации"""
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