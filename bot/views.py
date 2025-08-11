from traceback import format_exc

from bot import bot, logger
from bot.handlers import common, admin, registration, brief
from bot.handlers.admin.admin import accept_payment, decline_payment
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from telebot.apihelper import ApiTelegramException
from telebot.types import Update


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
        try:
            bot.send_message(settings.OWNER_ID, f'Error from index: {e}')
        except:
            pass
        logger.error(f"Unhandled exception. {e} {format_exc()}")
    return JsonResponse({"message": "OK"}, status=200)


"""Common"""

# Регистрация хендлеров для общих функций
start = bot.message_handler(commands=["start"])(common.start)
menu_call = bot.callback_query_handler(func=lambda call: call.data == "main_menu")(common.menu_call)
menu_video = bot.callback_query_handler(func=lambda call: call.data == "main_video_menu")(common.menu_video)
FAQ = bot.callback_query_handler(func=lambda call: call.data == "FAQ")(common.FAQ)

# Регистрация хендлеров для профиля
profile = bot.callback_query_handler(func=lambda call: call.data == "profile")(common.profile)
profile_set_full_name = bot.callback_query_handler(func=lambda call: call.data == "profile_set_full_name")(common.profile_set_full_name)
profile_set_grade = bot.callback_query_handler(func=lambda call: call.data == "profile_set_grade")(common.profile_set_grade)
profile_set_school = bot.callback_query_handler(func=lambda call: call.data == "profile_set_school")(common.profile_set_school)

# Регистрация хендлеров для оплаты
pay = bot.callback_query_handler(func=lambda call: call.data == "pay")(common.pay)
payment_i_paid = bot.callback_query_handler(func=lambda call: call.data.startswith("payment_i_paid_"))(common.payment_i_paid)
month_pay = bot.callback_query_handler(func=lambda call: call.data.startswith("month_pay_"))(common.handle_month_payment)
month_paid = bot.callback_query_handler(func=lambda call: call.data.startswith("month_paid_"))(common.handle_month_paid_info)
pay_now = bot.callback_query_handler(func=lambda call: call.data.startswith("pay_now_"))(common.pay_now)
payment_calendar = bot.callback_query_handler(func=lambda call: call.data == "payment_calendar")(common.payment_calendar_back)

# Регистрация хендлеров для регистрации
start_registration = bot.message_handler(commands=["start_registration"])(registration.start_registration)
start_registration_call = bot.callback_query_handler(func=lambda call: call.data == "start_registration")(registration.start_registration)
education_type_cb = bot.callback_query_handler(func=lambda call: call.data.startswith("education_type_"))(registration.handle_education_type)
grade_selection_cb = bot.callback_query_handler(func=lambda call: call.data.startswith("grade_"))(registration.handle_grade_selection)
start_brief_after_reg_cb = bot.callback_query_handler(func=lambda call: call.data == "start_brief_after_reg")(registration.start_brief_after_registration)
cancel_registration_cb = bot.callback_query_handler(func=lambda call: call.data == "cancel_registration")(registration.cancel_registration)

# Регистрация хендлеров для админ-панели
admin_menu_cb = bot.callback_query_handler(func=lambda call: call.data == "admin_menu")(admin.admin_menu)
admin_list_all = bot.callback_query_handler(func=lambda call: call.data == "admin_list_all")(admin.admin_list_all)
admin_list_paid = bot.callback_query_handler(func=lambda call: call.data == "admin_list_paid")(admin.admin_list_paid)
admin_list_unpaid = bot.callback_query_handler(func=lambda call: call.data == "admin_list_unpaid")(admin.admin_list_unpaid)
admin_pending_payments = bot.callback_query_handler(func=lambda call: call.data == "admin_pending_payments")(admin.admin_pending_payments)
admin_send_reminders = bot.callback_query_handler(func=lambda call: call.data == "admin_send_reminders")(admin.admin_send_reminders)
newsletter_cb = bot.callback_query_handler(func=lambda call: call.data == "newsletter")(admin.newsletter)

# Регистрация команд для админов
accept_payment = bot.message_handler(commands=["accept"])(accept_payment)
decline_payment = bot.message_handler(commands=["decline"])(decline_payment)

# Регистрация хендлеров для бриф
start_brief_cmd = bot.message_handler(commands=["brief"])(brief.start_brief)
start_brief_cb = bot.callback_query_handler(func=lambda call: call.data == "start_brief")(brief.start_brief)
continue_brief_cb = bot.callback_query_handler(func=lambda call: call.data == "continue_brief")(brief.continue_brief)
cancel_brief_cb = bot.callback_query_handler(func=lambda call: call.data == "cancel_brief")(brief.cancel_brief)
brief_progress_cb = bot.callback_query_handler(func=lambda call: call.data == "brief_progress")(brief.show_brief_progress)
