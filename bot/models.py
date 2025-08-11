from django.db import models


class User(models.Model):
    telegram_id = models.CharField(max_length=50, primary_key=True, verbose_name="Telegram ID")
    user_tg_name = models.CharField(max_length=35, blank=True, default='none', null=True, verbose_name="Имя пользователя в Telegram")
    user_name = models.CharField(max_length=35, verbose_name="Имя пользователя")
    full_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="ФИО")
    grade = models.CharField(max_length=20, blank=True, null=True, verbose_name="Класс/Курс")
    school = models.CharField(max_length=150, blank=True, null=True, verbose_name="Школа/Учебное заведение")
    brief_completed = models.BooleanField(default=False, verbose_name="Бриф заполнен")
    current_brief_question = models.PositiveIntegerField(blank=True, null=True, verbose_name="Текущий вопрос бриф")
    is_paid_current_month = models.BooleanField(default=False, verbose_name="Оплачен в текущем месяце")
    last_payment_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата последней оплаты")
    is_admin = models.BooleanField(default=False, verbose_name="Администратор")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=False, verbose_name="Персонал")
    is_superuser = models.BooleanField(default=False, verbose_name="Суперпользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_tg_name or 'Unknown'} ({self.full_name or 'Без имени'})"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class UserBriefComplete(models.Model):
    """Модель для хранения полного брифа пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complete_briefs', verbose_name="Пользователь")
    brief_data = models.JSONField(verbose_name="Данные брифа", help_text="Содержит все вопросы и ответы пользователя")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Полный бриф пользователя"
        verbose_name_plural = "Полные брифы пользователей"
        ordering = ['-created_at']

    def __str__(self):
        return f"Бриф пользователя {self.user.user_tg_name or 'Unknown'} от {self.created_at.strftime('%d.%m.%Y')}"

    def get_formatted_brief(self):
        """Возвращает отформатированный текст брифа"""
        result = []
        for item in self.brief_data:
            result.append(f"Вопрос: {item['question']}")
            result.append(f"Ответ: {item['answer']}\n")
        return "\n".join(result)


class BriefQuestion(models.Model):
    """Модель для вопросов брифов"""
    question_text = models.TextField(verbose_name="Текст вопроса")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок вопроса")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Вопрос бриф"
        verbose_name_plural = "Вопросы бриф"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Вопрос {self.order}: {self.question_text[:50]}..."


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        SUCCEEDED = 'succeeded', 'Подтвержден'
        FAILED = 'failed', 'Отклонен'
        MANUAL = 'manual', 'Ручной зачет'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments', verbose_name="Пользователь")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name="Статус")
    description = models.CharField(max_length=255, blank=True, verbose_name="Описание")
    yookassa_payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID платежа ЮKassa")
    payment_month = models.DateField(verbose_name="Месяц оплаты", help_text="Первый день месяца, за который производится оплата", default='2024-08-01')
    academic_year = models.CharField(max_length=9, verbose_name="Учебный год", help_text="Например: 2024-2025", default='2024-2025')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    confirmed_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата подтверждения")
    admin_comment = models.CharField(max_length=255, blank=True, verbose_name="Комментарий администратора")

    class Meta:
        verbose_name = "Платеж"
        verbose_name_plural = "Платежи"
        ordering = ['-payment_month', '-created_at']
        unique_together = ['user', 'payment_month', 'academic_year']

    def __str__(self):
        return f"Платеж {self.id} - {self.user.user_tg_name} за {self.payment_month.strftime('%B %Y')}"

    @property
    def month_name(self):
        """Возвращает название месяца на русском"""
        month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        return month_names[self.payment_month.month]

    @property
    def is_current_month(self):
        """Проверяет, является ли месяц текущим"""
        from datetime import date
        today = date.today()
        return (self.payment_month.year == today.year and 
                self.payment_month.month == today.month)

    @property
    def is_future_month(self):
        """Проверяет, является ли месяц будущим"""
        from datetime import date
        today = date.today()
        return (self.payment_month.year > today.year or 
                (self.payment_month.year == today.year and self.payment_month.month > today.month))
