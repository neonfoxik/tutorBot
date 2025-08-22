from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from bot.models import User, PaymentHistory
from bot.pricing import get_price_by_class
from bot import bot
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Отправляет напоминания об оплате за следующий месяц всем пользователям'

    def handle(self, *args, **options):
        current_date = timezone.now()
        current_month = current_date.month + 1
        current_year = current_date.year
        
        # Получаем всех зарегистрированных пользователей (не админов)
        users = User.objects.filter(is_admin=False, is_registered=True)
        
        reminder_count = 0
        success_count = 0
        
        for user in users:
            try:
                # Проверяем, оплачен ли текущий месяц
                is_paid = PaymentHistory.objects.filter(
                    user=user,
                    month=current_month,
                    year=current_year,
                    payment__status='succeeded'
                ).exists()


                if not is_paid:
                    # Получаем цену для конкретного ученика
                    price_info = get_price_by_class(user.course_or_class)
                    
                    if price_info:
                        price = price_info['price']
                        class_name = price_info['name']
                    else:
                        # Если не удалось определить цену, используем базовую
                        price = 5000
                        class_name = "стандартный тариф"
                    
                    # Отправляем напоминание
                    message_text = (
                        f"🔔 Напоминание об оплате\n\n"
                        f"Здравствуйте, {user.full_name or 'дорогой ученик'}!\n\n"
                        f"Напоминаем, что необходимо оплатить занятия за {str(current_month).rjust(2, '0')}.{current_year}.\n"
                        f"Своевременная оплата обеспечивает непрерывность обучения.\n\n"
                        f"📚 Тариф: {class_name}\n"
                        f"💰 Сумма к оплате: {price} ₽\n\n"
                        f"Для оплаты используйте кнопку '💰 Оплата 💰' в главном меню бота.\n\n"
                        f"Спасибо за понимание! 📚"
                    )
                    
                    bot.send_message(user.telegram_id, message_text)
                    reminder_count += 1
                    self.stdout.write(f"✅ Напоминание отправлено пользователю {user.telegram_id} (класс: {user.course_or_class}, цена: {price} ₽)")
                    
                else:
                    self.stdout.write(f"ℹ️ Пользователь {user.telegram_id} уже оплатил следующий месяц")
                    
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания пользователю {user.telegram_id}: {e}")
                self.stdout.write(f"❌ Ошибка для пользователя {user.telegram_id}: {e}")
                continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Напоминания об оплате отправлены! '
                f'Отправлено: {reminder_count}, '
                f'Успешно: {success_count}'
            )
        ) 