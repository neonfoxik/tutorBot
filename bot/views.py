from datetime import datetime
import json
from traceback import format_exc

from asgiref.sync import sync_to_async
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from bot.handlers import *
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
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

from .models import PaymentHistory, User, StudentProfile, ComplexTask, Task, TaskFile, TaskImage, ComplexHomework, Homework, Lesson, Group, LessonAttendance
from .forms import TaskForm, ComposeTaskForm, StudentAnswerForm


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
            for profile in all_profiles:
                # учитываем дату регистрации профиля
                if profile.register_date.month <= month['id']:
                    ph_qs = PaymentHistory.objects.filter(
                        month=month["id"],
                        year=year,
                        user=profile.user,
                        student_profile=profile,
                    )
                    if ph_qs.exists():
                        month['payers_count'] += 1
                        month['is_paid'] = True
                        payment_record = ph_qs.first()
                        month['paid_users'].append(payment_record)
                        total_income += payment_record.amount_paid
                    else:
                        month['unpaid_users'].append(profile)

                month['all_users'] += 1
            month['all_students'] = month['paid_users'] + month['unpaid_users']
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


@staff_member_required
def groups_list(request):
    groups = Group.objects.prefetch_related('students', 'teacher').all()
    # Ученики, у которых нет группы (свободные, для добавления)
    free_students = StudentProfile.objects.filter(group__isnull=True)
    context = {
        'groups': groups,
        'free_students': free_students,
    }
    return render(request, 'crm/groups.html', context)


@staff_member_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    students = group.students.all()
    lessons = group.lessons.order_by('date')  # Все занятия этой группы
    # Получаем посещения одним запросом
    att_qs = LessonAttendance.objects.filter(lesson__in=lessons, student__in=students)
    attendances = {}
    for att in att_qs:
        attendances.setdefault(att.student_id, {})[att.lesson_id] = att
    # Получаем домашки одним запросом
    hw_qs = ComplexHomework.objects.filter(lesson__in=lessons, student__in=students)
    homeworks = {}
    for hw in hw_qs:
        homeworks.setdefault(hw.student_id, {})[hw.lesson_id] = hw

    context = {
        'group': group,
        'students': students,
        'lessons': lessons,
        'attendances': attendances,
        'homeworks': homeworks,
    }
    return render(request, 'crm/group_detail.html', context)


@staff_member_required
@require_POST
def group_add_student(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    student_id = request.POST.get('student_id')
    if student_id:
        student = get_object_or_404(StudentProfile, id=student_id)
        student.group = group
        student.save()
    return redirect('bot:group_detail', group_id=group.id)


@staff_member_required
@require_POST
def group_remove_student(request, group_id, student_id):
    group = get_object_or_404(Group, id=group_id)
    student = get_object_or_404(StudentProfile, id=student_id, group=group)
    student.group = None
    student.save()
    return redirect('bot:group_detail', group_id=group.id)


@staff_member_required
@require_http_methods(["GET", "POST"])
def lesson_attendance_mark(request, lesson_id: int):
    lesson = get_object_or_404(Lesson.objects.select_related("group"), id=lesson_id)
    students = lesson.group.students.filter(is_active=True).order_by("profile_name")
    attendance_choices = dict(LessonAttendance.STATUS_CHOICES)

    # Загружаем существующие отметки в словарь
    existing_attendance = {
        att.student_id: att
        for att in LessonAttendance.objects.filter(lesson=lesson, student__in=students)
    }

    if request.method == "POST":
        try:
            with transaction.atomic():
                for student in students:
                    status_key = f"status_{student.id}"
                    comment_key = f"comment_{student.id}"

                    status_value = request.POST.get(status_key, "absent")
                    comment_value = request.POST.get(comment_key, "").strip()

                    attendance = existing_attendance.get(student.id)

                    if attendance:
                        attendance.status = status_value
                        attendance.comment = comment_value
                        attendance.save(update_fields=["status", "comment", "marked_at"])
                    else:
                        LessonAttendance.objects.create(
                            lesson=lesson,
                            student=student,
                            status=status_value,
                            comment=comment_value,
                        )
            messages.success(request, "Посещаемость сохранена.")
            return redirect("bot:group_detail", group_id=lesson.group_id)
        except Exception as exc:
            logger.exception("Ошибка сохранения посещаемости: %s", exc)
            messages.error(
                request,
                "Не удалось сохранить посещаемость. Проверьте данные и попробуйте ещё раз.",
            )

    context = {
        "lesson": lesson,
        "students": students,
        "attendance_choices": attendance_choices,
        "existing_attendance": existing_attendance,
    }
    return render(request, "crm/lesson_attendance.html", context)


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

# Обработчики student_menu
bot.register_message_handler(education, commands=['education'])
bot.register_callback_query_handler(education_show_handler, func=lambda c: c.data.split("_")[0] == "lessons" or c.data.split("_")[0] == "homeworks")
bot.register_callback_query_handler(education_studentprofiles_handler, func=lambda c: c.data.split("_")[0] == "education")
bot.register_callback_query_handler(show_lessons, func=lambda c: c.data.startswith("lessons-"))



@receiver(post_save, sender=ComplexHomework)
def assign_student_to_complex_homework(sender, instance, created, **kwargs):
    """Функция, сохраняющая д\з для всей группы при создании ComplexHomework"""
    if created:  # Проверяем, создано ли новое объект
        if instance.group != None and instance.student is None:
            for student in StudentProfile.objects.filter(group=instance.group):
                ComplexHomework.objects.filter(group=instance.group, lesson=instance.lesson).update(student=student)


@receiver(post_save, sender=Lesson)
def assign_lessonattendance_to_student(sender, instance, created, **kwargs):
    """Функция, сохраняющая д\з для всей группы при создании ComplexHomework"""
    if created:  # Проверяем, создано ли новое объект
        if instance.group != None:
            for student in StudentProfile.objects.filter(group=instance.group):
                # Создаем экземляр модели посещения с базовым значением Не был
                LessonAttendance.objects.create(lesson=instance, student=student, status="absent")


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


"""Site"""

def _resolve_submission_lesson(student: StudentProfile, task: ComplexTask) -> Lesson:
    """Возвращает урок для привязки домашней работы. Гарантирует not null.

    Приоритет:
      1) lesson у задания
      2) последний урок группы ученика
      3) создаёт новый урок на сегодня в группе ученика
    """
    if task and task.lesson.id:
        return task.lesson
    # берём по группе
    group = None
    if task and task.group.id:
        group = task.group
    if group is None:
        group = student.group
    if group is not None:
        last = Lesson.objects.filter(group=group).order_by('-date', '-start_time').first()
        if last:
            return last
        # создаём новый урок на сегодня
        return Lesson.objects.create(group=group, date=timezone.now().date(), topic='Автосоздано для ответа')
    # в крайнем случае — создадим техническую группу и урок
    teacher = User.objects.filter(is_teacher=True).first()
    group = Group.objects.create(name=f"AutoGroup-{student.id}", teacher=teacher or User.objects.first())
    return Lesson.objects.create(group=group, date=timezone.now().date(), topic='Автосоздано для ответа')



# ======= Tasks UI =======
@staff_member_required
def create_task(request):
    """Страница создания задания учителем (MVP)."""
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task: Task = form.save(commit=False)
            # Пытаемся привязать автора по telegram_id из GET/POST при наличии
            creator_tid = request.GET.get('creator_tid') or request.POST.get('creator_tid')
            if creator_tid:
                task.created_by = User.objects.filter(telegram_id=str(creator_tid)).first()
            task.save()

            # Сохраняем множественные файлы/изображения
            for f in request.FILES.getlist('files'):
                TaskFile.objects.create(task=task, file=f)
            for img in request.FILES.getlist('images'):
                TaskImage.objects.create(task=task, image=img)
            return redirect('bot:task_detail', task_id=task.id)
    else:
        form = TaskForm()
    return render(request, 'tasks/create.html', {"form": form})


@staff_member_required
def compose_task(request):
    """Конструктор комплексного задания: создаём задачу и добавляем подзадачи."""
    if request.method == 'POST':
        form = ComposeTaskForm(request.POST)
        if form.is_valid():
            base_task: Task = form.save(commit=False)
            base_task.created_by = base_task.created_by or None
            base_task.save()
            selected = form.cleaned_data['tasks']
            if selected:
                base_task.complex_task.set(selected)
            return redirect('bot:task_detail', task_id=base_task.id)
    else:
        form = ComposeTaskForm()
    return render(request, 'tasks/compose.html', {"form": form})


def task_detail(request, task_id: int):
    """Простая страница просмотра задания."""
    task = get_object_or_404(ComplexTask.objects.prefetch_related('files', 'images', 'complex_task'), id=task_id)
    return render(request, 'tasks/detail.html', {"task": task})


def answer_task(request, complexhomework_id: int, student_profile_id: int):
    """Страница ответа ученика на задание. Для комплексного задания выводим все подзадания."""
    #task = get_object_or_404(ComplexTask, id=task_id)
    complex_hw = get_object_or_404(ComplexHomework, id=complexhomework_id)
    student = get_object_or_404(StudentProfile, id=student_profile_id)
    task = complex_hw.complex_task

    # Если это комплексное задание — собираем подзадания
    sub_tasks = list(Task.objects.filter(complex_task=task))
    is_complex = True #len(sub_tasks) > 0

    # Если задание уже отправлено, пользователю показывается страница с соотв. надписью. Не даем ему изменить ответ
    if complex_hw.status == "done":
        return render(request, 'tasks/answer_has_sent.html')

    if is_complex:
        if request.method == 'POST':
            # Пройдёмся по каждому подзаданию, сохраним отдельный Homework и объединим в комплексный Homework
            lesson_obj = complex_hw.lesson #_resolve_submission_lesson(student, task)
            #complex_hw = ComplexHomework.objects.filter(student=student, complex_task=task).first()
            if complex_hw is None:
                complex_hw = ComplexHomework.objects.create(
                                student=student,
                                lesson=lesson_obj,
                                complex_task=task,
                                status='done',
                            )
            # Перебираем задания в наборе и выводим их
            for st in sub_tasks:
                field_name = f"answer_text_{st.id}"
                answer_text = request.POST.get(field_name, '').strip()
                if not answer_text:
                    continue
                hw = Homework.objects.filter(complex_homework=complex_hw, task=st).first()  # Экземпляр для записи ответа на задание
                lesson_obj = complex_hw.lesson #_resolve_submission_lesson(student, task)
                
                # Проверяем, является ли ответ правильным, неправильным или текстовым
                if st.answer:
                    if str(answer_text) == st.answer:
                        answer_result = "correct"
                    elif str(answer_text) != st.answer:
                        answer_result = "incorrect"
                else:
                    answer_result = "text"

                if hw is None:
                    Homework.objects.create(
                        complex_homework=complex_hw,
                        task=st,
                        assigned_text=st.description,
                        status='done',
                        result=answer_result,
                        answer_text=answer_text,
                        submitted_at=timezone.now(),
                    )
                else:
                    ...
                    """hw.answer_text = answer_text
                    hw.status = 'done'
                    hw.submitted_at = timezone.now()
                    hw.save(update_fields=['answer_text', 'status', 'submitted_at'])"""

            # В конце ставим статус на д\з "выполнен"
            complex_hw.status = 'done'
            complex_hw.save()
            return render(request, 'tasks/answer_success.html', {"task": task, "student": student})

        # GET: подготовим начальные ответы, если существуют
        sub_items = []
        for st in sub_tasks:
            hw = Homework.objects.filter(complex_homework=complex_hw, task=st).first()
            sub_items.append({
                'task': st,
                'initial': hw.answer_text if hw else ''
            })
        return render(
            request,
            'tasks/answer.html',
            {"task": task, "student": student, "is_complex": True, "sub_items": sub_items}
        )

    else:
        form = StudentAnswerForm(initial={"answer_text": homework.answer_text if homework else ""})

    
    return render(request, 'tasks/answer.html', {"form": form, "task": task, "student": student, "is_complex": False})


@staff_member_required
def student_homework_results(request, student_profile_id: int):
    """Просмотр результатов ДЗ по ученику для преподавателя.

    Показывает список всех `Homework` ученика, сгруппированных по урокам и заданиям.
    """
    student = get_object_or_404(StudentProfile, id=student_profile_id)
    homework = ComplexHomework.objects.filter(student=student)
    list_hw = list()
    for hw in homework:
        list_hw.append(hw)
        for answer in Homework.objects.filter(complex_homework=hw):
            list_hw.append(answer)
    #homeworks = Homework.objects.filter(complex_homework=homework)
    return render(request, 'tasks/results_student.html', {"student": student, "homeworks": list_hw})