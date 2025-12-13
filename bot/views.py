from datetime import datetime
import json
from traceback import format_exc

from asgiref.sync import sync_to_async
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
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

from bot.handlers.payments import (
    start_payment,
    payment_menu,
    payment_method,
    select_payment_method,
    select_payment_month,
    select_balance_payment_month,
    check_payment,
    payment_history,
    notify_payment_success,
    notify_admins_about_payment
)

from .models import Payment, PaymentHistory, User, StudentProfile


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
    # Переходим на уровень профилей учеников (а не пользователей)
    all_profiles = StudentProfile.objects.select_related('user').all()

    if request.method == 'POST':
        course = request.POST.get('course', '*')
        if course != "*":
            all_profiles = all_profiles.filter(class_number=course)

    # Получаем все года из PaymentHistory И из Payment (на случай если webhook не обработался)
    years_from_history = set(PaymentHistory.objects.values_list('year', flat=True))
    years_from_payments = set(Payment.objects.filter(status='succeeded').values_list('payment_year', flat=True))
    years = years_from_history | years_from_payments
    if len(years) == 0:
        years = [datetime.now().year]

    all_info = []
    total_income = 0

    for year in sorted(years, reverse=True):  # Сортируем года по убыванию
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
            ]
        }

        for month in year_info['months']:
            month['all_users'] = 0
            month['paid_users'] = []
            month['unpaid_users'] = []

            for profile in all_profiles:
                # учитываем дату регистрации профиля - показываем только тех, кто был зарегистрирован к этому месяцу
                if profile.register_date.year < year or (profile.register_date.year == year and profile.register_date.month <= month['id']):
                    month['all_users'] += 1

                    # Проверяем оплату в PaymentHistory
                    ph_qs = PaymentHistory.objects.filter(
                        month=month["id"],
                        year=year,
                        user=profile.user,
                        student_profile=profile,
                        status='completed'
                    )

                    # Также проверяем успешные платежи в Payment (на случай если webhook не обработался)
                    payment_qs = Payment.objects.filter(
                        payment_month=month["id"],
                        payment_year=year,
                        user=profile.user,
                        student_profile=profile,
                        status='succeeded'
                    )

                    if ph_qs.exists() or payment_qs.exists():
                        month['payers_count'] += 1
                        month['is_paid'] = True

                        # Предпочитаем PaymentHistory, но если его нет, используем Payment
                        if ph_qs.exists():
                            payment_record = ph_qs.first()
                        else:
                            payment_obj = payment_qs.first()
                            # Создаем временный объект, похожий на PaymentHistory для шаблона
                            class TempPaymentRecord:
                                def __init__(self, payment_obj, profile):
                                    self.student_profile = profile
                                    self.amount_paid = payment_obj.amount
                                    self.pricing_plan = payment_obj.pricing_plan
                            payment_record = TempPaymentRecord(payment_obj, profile)

                        month['paid_users'].append(payment_record)
                        total_income += payment_record.amount_paid
                    else:
                        month['unpaid_users'].append(profile)

        all_info.append(year_info)

    return render(request, 'templates_info.html', context={
        'all_info': all_info,
        'now_year': datetime.now().year,
        'now_month': datetime.now().month,
        'total_students': all_profiles.count(),
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


@csrf_exempt
@require_POST
def yookassa_webhook(request):
    """
    Обработчик webhook уведомлений от ЮKassa
    """
    try:
        # Получаем данные из POST запроса
        webhook_data = json.loads(request.body.decode('utf-8'))

        logger.info(f"Получен webhook от ЮKassa: {webhook_data}")

        # Обрабатываем webhook через функцию из yookassa_client
        from bot.yookassa_client import process_webhook
        success = process_webhook(webhook_data)

        if success:
            # Если платеж успешно обработан, отправляем уведомления
            event_type = webhook_data.get('event')
            if event_type == 'payment.succeeded':
                payment_id = webhook_data.get('object', {}).get('id')
                if payment_id:
                    # Вызываем функцию отправки уведомлений
                    from bot.handlers.payments import notify_payment_success
                    notify_payment_success(payment_id)

            return JsonResponse({"status": "ok"}, status=200)
        else:
            logger.error("Ошибка обработки webhook от ЮKassa")
            return JsonResponse({"status": "error", "message": "Failed to process webhook"}, status=400)

    except json.JSONDecodeError:
        logger.error("Неверный JSON в webhook от ЮKassa")
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@staff_member_required
def crm_dashboard(request):
    """CRM панель для администраторов"""
    # Получаем статистику
    total_students = StudentProfile.objects.filter(is_registered=True).count()
    active_students = StudentProfile.objects.filter(is_registered=True, is_active=True).count()
    
    # Статистика платежей
    payment_stats = PaymentHistory.objects.filter(
        status='completed'
    ).aggregate(
        total_payments=Count('id'),
        total_income=Sum('amount_paid')
    )
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'total_payments': payment_stats['total_payments'] or 0,
        'total_income': payment_stats['total_income'] or 0
    }
    
    return render(request, 'crm/dashboard.html', context)


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

# Обработчики для профилей
bot.register_callback_query_handler(profiles_menu, func=lambda c: c.data == "profiles_menu")
bot.register_callback_query_handler(view_profiles, func=lambda c: c.data == "view_profiles")
bot.register_callback_query_handler(create_profile, func=lambda c: c.data == "create_profile")
bot.register_callback_query_handler(confirm_profile_creation, func=lambda c: c.data == "confirm_profile_creation")

# Обработчики для выбора профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_profile_"))
def handle_profile_selection(call):
    """Обрабатывает выбор профиля"""
    from bot.handlers.profiles import select_profile
    select_profile(call)

# Обработчики для переключения профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("switch_to_profile_"))
def handle_profile_switch(call):
    """Обрабатывает переключение на профиль"""
    from bot.handlers.profiles import switch_to_profile
    switch_to_profile(call)

# Обработчики для управления данными профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_profile_data_"))
def handle_profile_data_management(call):
    """Обрабатывает управление данными профиля"""
    from bot.handlers.profiles import edit_profile_data
    edit_profile_data(call)

# Обработчики для удаления профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_profile_"))
def handle_profile_deletion(call):
    """Обрабатывает удаление профиля"""
    from bot.handlers.profiles import delete_profile
    delete_profile(call)

# Обработчики для подтверждения удаления профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_profile_"))
def handle_profile_deletion_confirmation(call):
    """Обрабатывает первое подтверждение удаления профиля"""
    from bot.handlers.profiles import confirm_delete_profile
    confirm_delete_profile(call)

# Обработчики для финального удаления профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("final_delete_profile_"))
def handle_profile_final_deletion(call):
    """Обрабатывает финальное удаление профиля"""
    from bot.handlers.profiles import final_delete_profile
    final_delete_profile(call)

# Обработчики для создания профиля
@bot.callback_query_handler(func=lambda call: call.data.startswith("profile_class_"))
def handle_profile_class_selection(call):
    """Обрабатывает выбор класса для профиля"""
    from bot.handlers.profiles import handle_profile_class_choice
    handle_profile_class_choice(call)

# Обработчики для регистрации и создания профилей
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_all_messages(message):
    """Обрабатывает все текстовые сообщения для регистрации и создания профилей (кроме команд)"""
    from bot.handlers.registration import handle_registration_message, is_user_registering
    from bot.handlers.profiles import handle_profile_creation_message, is_user_creating_profile
    
    # Проверяем, находится ли пользователь в процессе создания профиля
    if is_user_creating_profile(str(message.from_user.id)):
        handle_profile_creation_message(message)
    # Проверяем, находится ли пользователь в процессе регистрации
    elif is_user_registering(str(message.from_user.id)):
        handle_registration_message(message)

# Обработчики для выбора класса
@bot.callback_query_handler(func=lambda call: call.data.startswith("class_"))
def handle_class_selection(call):
    """Обрабатывает выбор класса"""
    from bot.handlers.registration import handle_class_choice
    handle_class_choice(call)

# Обработчики платежей
bot.register_callback_query_handler(start_payment, func=lambda c: c.data == "start_payment")
bot.register_callback_query_handler(payment_history, func=lambda c: c.data == "payment_history")
bot.register_callback_query_handler(payment_method, func=lambda c: c.data == "payment_method")
bot.register_callback_query_handler(payment_menu, func=lambda c: c.data == "payment_menu")

# Обработчик для возврата в админ меню
admin_menu_callback_handler = bot.callback_query_handler(lambda c: c.data == "admin_menu")(admin_menu_callback)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_month_"))
def handle_payment_month_selection(call):
    """Обрабатывает выбор месяца для оплаты"""
    from bot.handlers.payments import select_payment_month
    select_payment_month(call)

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