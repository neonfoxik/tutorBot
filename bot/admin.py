from django.contrib import admin
from .models import User, StudentProfile, Payment, PaymentHistory

class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'full_name', 'class_number', 'is_registered', 'is_admin')
    search_fields = ('full_name', 'telegram_id')
    list_filter = ('is_registered', 'is_admin')
    ordering = ('-is_registered',)
    list_editable = ('is_admin',)

    def get_queryset(self, request):
        """Переопределяем метод для обработки ошибок при получении пользователей."""
        try:
            return super().get_queryset(request)
        except Exception as e:
            return User.objects.none()

admin.site.register(User, UserAdmin)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('profile_name', 'user', 'full_name', 'class_number', 'education_level', 'is_active', 'balance', 'created_at')
    list_filter = ('education_level', 'is_active', 'is_registered', 'created_at')
    search_fields = ('profile_name', 'full_name', 'user__telegram_id')
    list_editable = ('is_active',)
    ordering = ('-is_active', '-created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('yookassa_payment_id', 'user', 'student_profile', 'amount', 'status', 'payment_month', 'payment_year', 'created_at')
    list_filter = ('status', 'payment_month', 'payment_year', 'created_at', 'pricing_plan')
    search_fields = ('yookassa_payment_id', 'user__full_name', 'user__telegram_id', 'student_profile__profile_name')
    readonly_fields = ('yookassa_payment_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'student_profile')


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_profile', 'month', 'year', 'amount_paid', 'pricing_plan', 'paid_at')
    list_filter = ('month', 'year', 'pricing_plan', 'paid_at')
    search_fields = ('user__full_name', 'user__telegram_id', 'student_profile__profile_name')
    readonly_fields = ('paid_at',)
    ordering = ('-year', '-month')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'student_profile', 'payment')