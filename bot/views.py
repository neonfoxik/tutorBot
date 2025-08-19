import json
from traceback import format_exc

from asgiref.sync import sync_to_async
from bot.handlers import *
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from telebot.apihelper import ApiTelegramException
from telebot.types import Update

from bot import bot, logger


@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    """Setting webhook."""
    bot.set_webhook(url=f"{settings.HOOK}/bot/{settings.BOT_TOKEN}")
    bot.send_message(settings.OWNER_ID, "webhook set")
    return JsonResponse({"message": "OK"}, status=200)


@require_GET
def status(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"message": "OK"}, status=200)


@csrf_exempt
@require_POST
@sync_to_async
def index(request: HttpRequest) -> JsonResponse:
    if request.META.get("CONTENT_TYPE") != "application/json":
        return JsonResponse({"message": "Bad Request"}, status=403)

    json_string = request.body.decode("utf-8")
    update = Update.de_json(json_string)
    try:
        bot.process_new_updates([update])
    except ApiTelegramException as e:
        logger.error(f"Telegram exception. {e} {format_exc()}")
    except ConnectionError as e:
        logger.error(f"Connection error. {e} {format_exc()}")
    except Exception as e:
        bot.send_message(settings.OWNER_ID, f'Error from index: {e}')
        logger.error(f"Unhandled exception. {e} {format_exc()}")
    return JsonResponse({"message": "OK"}, status=200)


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


@csrf_exempt
@require_POST
def yookassa_webhook(request: HttpRequest) -> JsonResponse:
    """Обработка уведомлений от ЮKassa"""
    try:
        webhook_data = json.loads(request.body.decode('utf-8'))
        
        from bot.yookassa_client import process_webhook
        from bot.handlers.payments import notify_payment_success
        from bot.models import PaymentHistory
        from bot.keyboards import MONTH_NAMES
        
        success = process_webhook(webhook_data)
        
        if success:
            # Если это успешный платеж, отправляем уведомление пользователю
            event_type = webhook_data.get('event')
            if event_type == 'payment.succeeded':
                payment_data = webhook_data.get('object')
                metadata = payment_data.get('metadata', {})
                
                user_telegram_id = metadata.get('user_id')
                month = int(metadata.get('month', 0))
                year = int(metadata.get('year', 0))
                amount = float(payment_data.get('amount', {}).get('value', 0))
                
                if user_telegram_id and month and year:
                    notify_payment_success(user_telegram_id, month, year, amount)
        
        return JsonResponse({"message": "OK"}, status=200)
    
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook ЮKassa: {e}")
        return JsonResponse({"message": "Error"}, status=500)