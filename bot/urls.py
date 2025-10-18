from django.conf import settings
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required

from bot import views


app_name = 'bot'


urlpatterns = [
    path(settings.BOT_TOKEN, views.index, name="index"),
    path('', views.set_webhook, name="set_webhook"),
    path("bot/status/", views.status, name="status"),
    path("crm/", staff_member_required(views.crm_dashboard), name="crm_dashboard"),
    path("payment-info/", staff_member_required(views.payment_info), name="payment_info"),
    # Tasks
    path("tasks/create/", staff_member_required(views.create_task), name="task_create"),
    path("tasks/compose/", staff_member_required(views.compose_task), name="task_compose"),
    path("tasks/<int:task_id>/", views.task_detail, name="task_detail"),
    path("tasks/<int:complexhomework_id>/answer/<int:student_profile_id>/", views.answer_task, name="task_answer"),
    path("tasks/results/student/<int:student_profile_id>/", staff_member_required(views.student_homework_results), name="student_homework_results"),
]
