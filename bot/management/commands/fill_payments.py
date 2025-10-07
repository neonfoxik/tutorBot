from django.core.management.base import BaseCommand
from django.utils import timezone
from bot.models import User, StudentProfile, PaymentHistory
from bot.pricing import get_price_by_class
from datetime import datetime

class Command(BaseCommand):
    help = 'Заполняет оплаты всех пользователей за октябрь 2025 года'

    def handle(self, *args, **options):
        # Месяц и год для заполнения
        target_month = 10
        target_year = 2025

        # Получаем всех пользователей с профилями
        profiles = StudentProfile.objects.filter(is_registered=True)
        
        self.stdout.write(f"Найдено {profiles.count()} профилей для заполнения оплат")
        
        success_count = 0
        error_count = 0
        
        for profile in profiles:
            try:
                # Проверяем, не оплачен ли уже этот месяц
                if PaymentHistory.is_month_paid(profile.user, target_month, target_year, profile):
                    self.stdout.write(f"Профиль {profile.profile_name} уже имеет оплату за {target_month:02d}.{target_year}")
                    continue

                # Получаем цену для класса и уровня
                class_key = profile.class_number
                if profile.education_level and profile.class_number in ['10', '11']:
                    class_key = f"{profile.class_number}_{profile.education_level}"

                price_info = get_price_by_class(class_key)
                
                if not price_info:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Не удалось определить тариф для профиля {profile.profile_name} "
                            f"(класс: {profile.class_number}, уровень: {profile.education_level})"
                        )
                    )
                    error_count += 1
                    continue

                # Создаем запись в истории платежей
                PaymentHistory.objects.create(
                    user=profile.user,
                    student_profile=profile,
                    month=target_month,
                    year=target_year,
                    amount_paid=price_info['price'],
                    pricing_plan=price_info['name'],
                    payment_type='card',
                    status='completed',
                    paid_at=timezone.now()
                )

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Создана оплата для профиля {profile.profile_name} "
                        f"на сумму {price_info['price']} руб. "
                        f"(тариф: {price_info['name']})"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Ошибка при создании оплаты для профиля {profile.profile_name}: {str(e)}"
                    )
                )
                error_count += 1

        self.stdout.write("\nИтоги заполнения:")
        self.stdout.write(f"Успешно создано оплат: {success_count}")
        self.stdout.write(f"Ошибок: {error_count}")
        self.stdout.write(f"Всего обработано профилей: {profiles.count()}")
