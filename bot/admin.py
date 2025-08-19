from django.contrib import admin
from .models import User, Payment, PaymentHistory

class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'full_name', 'education_type', 'course_or_class', 'is_registered', 'is_admin')
    search_fields = ('full_name', 'telegram_id')
    list_filter = ('education_type', 'is_registered', 'is_admin')
    ordering = ('-is_registered',)
    list_editable = ('is_admin',)

    def get_queryset(self, request):
        """Переопределяем метод для обработки ошибок при получении пользователей."""
        try:
            return super().get_queryset(request)
        except Exception as e:
            return User.objects.none()

admin.site.register(User, UserAdmin)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('yookassa_payment_id', 'user', 'amount', 'status', 'payment_month', 'payment_year', 'created_at')
    list_filter = ('status', 'payment_month', 'payment_year', 'created_at', 'pricing_plan')
    search_fields = ('yookassa_payment_id', 'user__full_name', 'user__telegram_id')
    readonly_fields = ('yookassa_payment_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'year', 'amount_paid', 'pricing_plan', 'paid_at')
    list_filter = ('month', 'year', 'pricing_plan', 'paid_at')
    search_fields = ('user__full_name', 'user__telegram_id')
    readonly_fields = ('paid_at',)
    ordering = ('-year', '-month')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'payment')
