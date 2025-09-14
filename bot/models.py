from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta


class User(models.Model):
    EDUCATION_CHOICES = [
        ('school', 'Школа'),
        ('university', 'ВУЗ'),
    ]
    
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
    education_type = models.CharField(
        max_length=20,
        choices=EDUCATION_CHOICES,
        verbose_name="Тип образования",
        null=True,
        blank=True
    )
    course_or_class = models.CharField(
        max_length=10,
        verbose_name="Курс или класс",
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
    def is_month_paid(cls, user, month, year):
        """Проверить, оплачен ли указанный месяц"""
        return cls.objects.filter(
            user=user,
            month=month,
            year=year
        ).exists()
    
    @classmethod
    def get_paid_months(cls, user):
        """Получить все оплаченные месяцы для пользователя"""
        return cls.objects.filter(user=user).values_list('month', 'year')


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
   
