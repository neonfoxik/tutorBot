from django.conf import settings
from django.urls import path

from bot import views


app_name = 'bot'


urlpatterns = [
    path(settings.BOT_TOKEN, views.index, name="index"),
    path('bot/', views.set_webhook, name="set_webhook"),
    path("bot/status/", views.status, name="status"),
    path("payment-info/", views.payment_info, name="payment_info"),
]
