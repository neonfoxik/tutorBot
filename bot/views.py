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
        try:
            json_str = request.body.decode('UTF-8')
            update = telebot.types.Update.de_json(json_str)
            bot.process_new_updates([update])
            return HttpResponse("OK")
        except Exception as e:
            logger.error(f"Ошибка при обработке webhook: {e}")
            return HttpResponse("Error", status=500)
    return HttpResponse("Bot is running")

@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    """Setting webhook."""
    try:
        if not settings.HOOK or not settings.BOT_TOKEN:
            return JsonResponse({
                "error": "HOOK или BOT_TOKEN не настроены", 
                "hook": bool(settings.HOOK),
                "bot_token": bool(settings.BOT_TOKEN)
            }, status=400)
        
        webhook_url = f"{settings.HOOK}/bot/{settings.BOT_TOKEN}"
        
        # Проверяем, доступен ли домен
        import socket
        try:
            domain = settings.HOOK.replace('https://', '').replace('http://', '').split('/')[0]
            socket.gethostbyname(domain)
        except socket.gaierror:
            return JsonResponse({
                "error": f"Не удается разрешить домен: {domain}",
                "webhook_url": webhook_url
            }, status=400)
        
        # Устанавливаем webhook
        bot.set_webhook(url=webhook_url)
        
        # Отправляем уведомление владельцу (если возможно)
        if settings.OWNER_ID:
            try:
                bot.send_message(settings.OWNER_ID, f"Webhook установлен: {webhook_url}")
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение владельцу: {e}")
        
        return JsonResponse({
            "message": "Webhook успешно установлен", 
            "url": webhook_url,
            "hook": settings.HOOK,
            "bot_token": f"{settings.BOT_TOKEN[:10]}..." if settings.BOT_TOKEN else None
        }, status=200)
            
    except ApiTelegramException as e:
        error_msg = str(e)
        logger.error(f"Ошибка Telegram API при установке webhook: {e}")
        
        # Анализируем ошибку
        if "Failed to resolve host" in error_msg:
            return JsonResponse({
                "error": "Ошибка разрешения домена. Проверьте настройки DNS.",
                "webhook_url": webhook_url if 'webhook_url' in locals() else None,
                "details": error_msg
            }, status=400)
        elif "bad webhook" in error_msg:
            return JsonResponse({
                "error": "Некорректный webhook URL",
                "webhook_url": webhook_url if 'webhook_url' in locals() else None,
                "details": error_msg
            }, status=400)
        else:
            return JsonResponse({
                "error": f"Ошибка Telegram API: {error_msg}",
                "webhook_url": webhook_url if 'webhook_url' in locals() else None
            }, status=500)
            
    except Exception as e:
        logger.error(f"Неожиданная ошибка при установке webhook: {e}")
        return JsonResponse({
            "error": f"Внутренняя ошибка: {str(e)}",
            "webhook_url": webhook_url if 'webhook_url' in locals() else None
        }, status=500)

@require_GET
def webhook_info(request: HttpRequest) -> JsonResponse:
    """Информация о webhook без его установки."""
    try:
        if settings.HOOK and settings.BOT_TOKEN:
            webhook_url = f"{settings.HOOK}/bot/{settings.BOT_TOKEN}"
            return JsonResponse({
                "message": "Webhook информация",
                "hook": settings.HOOK,
                "bot_token": f"{settings.BOT_TOKEN[:10]}..." if settings.BOT_TOKEN else None,
                "webhook_url": webhook_url,
                "owner_id": settings.OWNER_ID
            }, status=200)
        else:
            return JsonResponse({"error": "HOOK или BOT_TOKEN не настроены"}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при получении информации о webhook: {e}")
        return JsonResponse({"error": f"Внутренняя ошибка: {e}"}, status=500)

@require_GET
def status(request: HttpRequest) -> JsonResponse:
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("check_payment_"))
def handle_payment_check(call):
    """Обрабатывает проверку оплаты"""
    from bot.handlers.payments import check_payment
    check_payment(call)