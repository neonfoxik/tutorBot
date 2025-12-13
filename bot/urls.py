from django.conf import settings
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required

from bot import views


app_name = 'bot'


urlpatterns = [
    path(settings.BOT_TOKEN, views.index, name="index"),
    path('', views.set_webhook, name="set_webhook"),
    path("bot/status/", views.status, name="status"),
    path("yookassa/webhook/", views.yookassa_webhook, name="yookassa_webhook"),
    path("crm/", staff_member_required(views.crm_dashboard), name="crm_dashboard"),
    path("payment-info/", staff_member_required(views.payment_info), name="payment_info"),
]
