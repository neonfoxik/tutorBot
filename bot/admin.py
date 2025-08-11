from django.contrib import admin
from .models import User, Payment, BriefQuestion, UserBriefComplete


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'telegram_id', 'user_tg_name', 'user_name', 'full_name', 'grade', 'school',
        'is_paid_current_month', 'last_payment_at', 'is_admin'
    )
    search_fields = ('user_name', 'user_tg_name', 'full_name', 'telegram_id')
    list_filter = ('is_admin', 'is_paid_current_month', 'brief_completed')
    ordering = ('-last_payment_at',)

    def get_queryset(self, request):
        try:
            return super().get_queryset(request)
        except Exception:
            return User.objects.none()


class BriefQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('question_text',)
    list_filter = ('is_active',)
    ordering = ('order',)


class UserBriefCompleteAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'get_answers_count')
    search_fields = ('user__user_name', 'user__full_name')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def get_answers_count(self, obj):
        return len(obj.brief_data)
    get_answers_count.short_description = 'Количество ответов'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at', 'confirmed_at', 'yookassa_payment_id')
    list_filter = ('status',)
    search_fields = ('user__user_name', 'user__full_name', 'yookassa_payment_id')


admin.site.register(User, UserAdmin)
admin.site.register(BriefQuestion, BriefQuestionAdmin)
admin.site.register(UserBriefComplete, UserBriefCompleteAdmin)