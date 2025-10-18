from django.contrib import admin
from .models import User, StudentProfile, Payment, PaymentHistory, Group, Lesson, LessonAttendance, ComplexHomework, Homework, ComplexTask, Task, TaskFile, TaskImage

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


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'teacher__full_name', 'teacher__telegram_id')
    list_editable = ('is_active',)
    ordering = ('-is_active', 'name')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('profile_name', 'user', 'group', 'full_name', 'class_number', 'education_level', 'is_active', 'balance', 'created_at')
    list_filter = ('education_level', 'is_active', 'is_registered', 'created_at', 'group')
    search_fields = ('profile_name', 'full_name', 'user__telegram_id', 'group__name')
    list_editable = ('is_active',)
    ordering = ('-is_active', '-created_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'group')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('group', 'date', 'start_time', 'end_time', 'topic')
    list_filter = ('group', 'date')
    search_fields = ('group__name', 'topic')
    ordering = ('-date', '-start_time')


@admin.register(LessonAttendance)
class LessonAttendanceAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'student', 'status', 'marked_at')
    list_filter = ('status', 'lesson__group', 'lesson__date')
    search_fields = ('student__profile_name', 'lesson__group__name')
    ordering = ('-marked_at',)


@admin.register(ComplexHomework)
class ComplexHomeworkAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'complex_task', 'group', 'status')
    list_filter = ('status', 'lesson__group', 'complex_task')
    search_fields = ('student__profile_name', 'lesson__group__name', 'complex_task__title')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('task', 'status', 'result', 'submitted_at', 'checked_at')
    list_filter = ('status', 'result', 'complex_homework__complex_task')
    search_fields = ('student__profile_name', 'complex_homework__lesson__group__name', 'task__title')
    ordering = ('-submitted_at',)


@admin.register(ComplexTask)
class ComplexTaskAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title', 'description')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    search_fields = ('title', 'description', 'created_by__full_name')
    ordering = ('-created_at',)


@admin.register(TaskFile)
class TaskFileAdmin(admin.ModelAdmin):
    list_display = ('task', 'file', 'uploaded_at')
    list_filter = ('task',)
    search_fields = ('task__title',)


@admin.register(TaskImage)
class TaskImageAdmin(admin.ModelAdmin):
    list_display = ('task', 'image', 'uploaded_at')
    list_filter = ('task',)
    search_fields = ('task__title',)


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