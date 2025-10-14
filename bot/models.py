from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class User(models.Model):
    telegram_id = models.CharField(
        primary_key=True,
        max_length=50
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name="ФИО",
        null=True,
        blank=True
    )
    class_number = models.CharField(
        max_length=10,
        verbose_name="Класс",
        null=True,
        blank=True
    )
    is_registered = models.BooleanField(
        default=False,
        verbose_name="Завершена регистрация"
    )
    register_date = models.DateField(
        default='2025-08-25',
        verbose_name='Дата регистрации'
    )
    is_admin = models.BooleanField(
        default=False,
        verbose_name="Администратор"
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Баланс"
    )
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
    
    def __str__(self):
        return f"{self.full_name} ({self.telegram_id})"


class Payment(models.Model):
    """Модель для хранения информации о платежах"""
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('waiting_for_capture', 'Ожидает подтверждения'),
        ('succeeded', 'Успешно'),
        ('canceled', 'Отменен'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Пользователь'
    )
    student_profile = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Профиль ученика',
        null=True,
        blank=True
    )
    yookassa_payment_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='ID платежа в ЮKassa'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма платежа'
    )
    currency = models.CharField(
        max_length=3,
        default='RUB',
        verbose_name='Валюта'
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name='Статус платежа'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание платежа'
    )
    payment_method = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Метод оплаты'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    # Поля для привязки к оплачиваемому периоду
    payment_month = models.IntegerField(
        verbose_name='Месяц оплаты'
    )
    payment_year = models.IntegerField(
        verbose_name='Год оплаты'
    )
    pricing_plan = models.CharField(
        max_length=50,
        verbose_name='Тарифный план'
    )
    
    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Платеж {self.yookassa_payment_id} - {self.user.full_name} - {self.amount} руб."


class PaymentHistory(models.Model):
    """Модель для отслеживания истории оплаченных месяцев"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('card', 'Банковская карта'),
        ('cash', 'Наличные'),
        ('transfer', 'Перевод'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_history',
        verbose_name='Пользователь'
    )
    student_profile = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='payment_history',
        verbose_name='Профиль ученика',
        null=True,
        blank=True
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='history_records',
        verbose_name='Платеж',
        null=True,
        blank=True
    )
    month = models.IntegerField(
        verbose_name='Месяц'
    )
    year = models.IntegerField(
        verbose_name='Год'
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Оплаченная сумма'
    )
    pricing_plan = models.CharField(
        max_length=50,
        verbose_name='Тарифный план'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='card',
        verbose_name='Тип оплаты'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name='Статус оплаты'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    paid_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оплаты'
    )
    
    class Meta:
        verbose_name = "История оплат"
        verbose_name_plural = "История оплат"
        unique_together = ['user', 'month', 'year']
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.month:02d}.{self.year} - {self.amount_paid} руб."
    
    @classmethod
    def is_month_paid(cls, user, month, year, student_profile=None):
        """Проверить, оплачен ли указанный месяц"""
        query = cls.objects.filter(
            user=user,
            month=month,
            year=year
        )
        if student_profile:
            query = query.filter(student_profile=student_profile)
        return query.exists()
    
    @classmethod
    def get_paid_months(cls, user, student_profile=None):
        """Получить все оплаченные месяцы для пользователя"""
        query = cls.objects.filter(user=user)
        if student_profile:
            query = query.filter(student_profile=student_profile)
        return query.values_list('month', 'year')


class AdminState(models.Model):
    """Модель для хранения состояний администраторов"""
    
    admin_id = models.CharField(
        max_length=50,
        verbose_name="ID администратора"
    )
    state = models.CharField(
        max_length=100,
        verbose_name="Состояние"
    )
    data = models.JSONField(
        default=dict,
        verbose_name="Данные состояния"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Состояние администратора"
        verbose_name_plural = "Состояния администраторов"
        unique_together = ['admin_id', 'state']
    
    def __str__(self):
        return f"Admin {self.admin_id} - {self.state}"


class Group(models.Model):
    """Модель для группы учеников"""
    name = models.CharField(
        max_length=150,
        verbose_name="Название группы"
    )
    teacher = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='teaching_groups',
        verbose_name='Преподаватель'
    )
    telegram_group_chat_id = models.CharField(
        max_length=64,
        verbose_name='ID Telegram-чата группы',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name}"


class StudentProfile(models.Model):
    """Модель для профилей учеников под одним Telegram аккаунтом"""
    
    EDUCATION_LEVEL_CHOICES = [
        ('base', 'База'),
        ('profile', 'Профиль'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_profiles',
        verbose_name='Пользователь Telegram'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='students',
        verbose_name='Группа',
        null=True,
        blank=True
    )
    profile_name = models.CharField(
        max_length=100,
        verbose_name="Имя профиля",
        help_text="Например: 'Иван Петров' или 'Мария Сидорова'"
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name="ФИО",
        null=True,
        blank=True
    )
    class_number = models.CharField(
        max_length=10,
        verbose_name="Класс",
        null=True,
        blank=True
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name="Уровень (база/профиль)",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активный профиль"
    )
    is_registered = models.BooleanField(
        default=False,
        verbose_name="Завершена регистрация"
    )
    register_date = models.DateField(
        default='2025-08-25',
        verbose_name='Дата регистрации'
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Баланс"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    
    class Meta:
        verbose_name = "Профиль ученика"
        verbose_name_plural = "Профили учеников"
        unique_together = ['user', 'profile_name']
    
    def __str__(self):
        return f"{self.profile_name} ({self.user.telegram_id})"
    
    def get_education_level_display(self):
        """Возвращает отображаемое название уровня образования"""
        for choice in self.EDUCATION_LEVEL_CHOICES:
            if choice[0] == self.education_level:
                return choice[1]
        return self.education_level


class Lesson(models.Model):
    """Модель урока, привязанного к группе"""

    ATTENDANCE_STATUS = [
        ('present', 'Был'),
        ('absent', 'Не был'),
        ('excused', 'Уважительная причина'),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Группа'
    )
    date = models.DateField(
        verbose_name='Дата урока'
    )
    start_time = models.TimeField(
        verbose_name='Начало',
        null=True,
        blank=True
    )
    end_time = models.TimeField(
        verbose_name='Окончание',
        null=True,
        blank=True
    )
    topic = models.CharField(
        max_length=200,
        verbose_name='Тема',
        null=True,
        blank=True
    )
    notes = models.TextField(
        verbose_name='Заметки',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['-date', '-start_time']
        unique_together = [('group', 'date', 'start_time')]

    def __str__(self):
        start = f" {self.start_time}" if self.start_time else ''
        return f"{self.group.name} — {self.date}{start}"


class LessonAttendance(models.Model):
    """Посещаемость: статус посещения ученика на конкретном уроке"""

    STATUS_CHOICES = [
        ('present', 'Был'),
        ('absent', 'Не был'),
        ('excused', 'Уважительная причина'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Урок'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Ученик'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name='Статус',
        default='present'
    )
    comment = models.CharField(
        max_length=255,
        verbose_name='Комментарий',
        null=True,
        blank=True
    )
    marked_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Отмечено'
    )

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = [('lesson', 'student')]

    def __str__(self):
        return f"{self.student.profile_name} — {self.lesson.date}: {self.get_status_display()}"


class Homework(models.Model):
    """Домашнее задание ученика к уроку"""

    STATUS_CHOICES = [
        ('done', 'Сделал'),
        ('not_done', 'Не сделал'),
    ]

    RESULT_CHOICES = [
        ('correct', 'Верно'),
        ('incorrect', 'Неверно'),
        ('text', 'Текстовый ответ'),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Ученик'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Урок'
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.SET_NULL,
        related_name='homeworks',
        verbose_name='Задание',
        null=True,
        blank=True
    )
    assigned_text = models.TextField(
        verbose_name='Текст задания',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default='not_done',
        verbose_name='Статус'
    )
    result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES,
        verbose_name='Результат проверки',
        null=True,
        blank=True
    )
    answer_text = models.TextField(
        verbose_name='Ответ ученика',
        null=True,
        blank=True
    )
    submitted_at = models.DateTimeField(
        verbose_name='Отправлено',
        null=True,
        blank=True
    )
    checked_at = models.DateTimeField(
        verbose_name='Проверено',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        unique_together = [('student', 'lesson')]
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.profile_name} — {self.lesson}"


class Task(models.Model):
    """Задача/задание с описанием и вложениями (файлы/изображения)."""

    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    description = models.TextField(
        verbose_name='Описание задания',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_tasks',
        verbose_name='Создатель',
        null=True,
        blank=True
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='tasks',
        verbose_name='Группа',
        null=True,
        blank=True
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        related_name='tasks',
        verbose_name='Урок',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


def task_file_upload_to(instance, filename):
    return f"tasks/{instance.task_id}/files/{filename}"


def task_image_upload_to(instance, filename):
    return f"tasks/{instance.task_id}/images/{filename}"


class TaskFile(models.Model):
    """Файловые вложения к заданию."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Задание'
    )
    file = models.FileField(
        upload_to=task_file_upload_to,
        verbose_name='Файл'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Загружено'
    )

    class Meta:
        verbose_name = 'Файл задания'
        verbose_name_plural = 'Файлы задания'

    def __str__(self):
        return f"Файл для {self.task_id}"


class TaskImage(models.Model):
    """Изображения к заданию."""

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Задание'
    )
    image = models.ImageField(
        upload_to=task_image_upload_to,
        verbose_name='Изображение'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Загружено'
    )

    class Meta:
        verbose_name = 'Изображение задания'
        verbose_name_plural = 'Изображения задания'

    def __str__(self):
        return f"Изображение для {self.task_id}"