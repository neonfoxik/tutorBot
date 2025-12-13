from django.core.management.base import BaseCommand
from django.db import transaction
from bot.models import Payment, PaymentHistory
from bot.handlers.payments import notify_payment_success
from bot.yookassa_client import YooKassaClient
import logging

logger = logging.getLogger('bot')


class Command(BaseCommand):
    help = 'Проверяет статус всех незавершенных платежей у ЮKassa и обновляет базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без выполнения изменений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА - изменения не будут сохранены')
            )

        # Находим все незавершенные платежи
        pending_payments = Payment.objects.filter(
            status__in=['pending', 'waiting_for_capture']
        ).select_related('user', 'student_profile')

        if not pending_payments.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Нет незавершенных платежей для проверки')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'📋 Найдено {pending_payments.count()} незавершенных платежей')
        )

        # Инициализируем клиент ЮKassa
        try:
            client = YooKassaClient()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка инициализации клиента ЮKassa: {e}')
            )
            return

        updated_count = 0
        succeeded_count = 0
        canceled_count = 0
        error_count = 0

        for payment in pending_payments:
            try:
                self.stdout.write(f'\n🔍 Проверяем платеж {payment.yookassa_payment_id}...')

                # Получаем актуальный статус от ЮKassa
                payment_info = client.get_payment(payment.yookassa_payment_id)

                if not payment_info:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Не удалось получить информацию о платеже {payment.yookassa_payment_id}')
                    )
                    error_count += 1
                    continue

                current_status = payment_info.get('status')
                self.stdout.write(f'  📊 Текущий статус в ЮKassa: {current_status}')

                if current_status == 'succeeded' and payment.status != 'succeeded':
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Платеж {payment.yookassa_payment_id} успешно оплачен!')
                    )

                    if not dry_run:
                        with transaction.atomic():
                            # Обновляем статус платежа
                            payment.status = 'succeeded'
                            payment.payment_method = payment_info.get('payment_method', {})
                            payment.save()

                            # Создаем запись в истории платежей, если её нет
                            if not PaymentHistory.objects.filter(
                                user=payment.user,
                                payment=payment,
                                month=payment.payment_month,
                                year=payment.payment_year
                            ).exists():
                                PaymentHistory.objects.create(
                                    user=payment.user,
                                    student_profile=payment.student_profile,
                                    payment=payment,
                                    month=payment.payment_month,
                                    year=payment.payment_year,
                                    amount_paid=payment.amount,
                                    pricing_plan=payment.pricing_plan,
                                    payment_type='card',
                                    status='completed'
                                )

                                # Отправляем уведомления
                                try:
                                    notify_payment_success(payment.yookassa_payment_id)
                                    self.stdout.write('     📨 Уведомления отправлены')
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.WARNING(f'     ⚠️ Ошибка отправки уведомлений: {e}')
                                    )
                            else:
                                self.stdout.write('     ℹ️ Запись в истории платежей уже существует')

                    updated_count += 1
                    succeeded_count += 1

                elif current_status == 'canceled' and payment.status != 'canceled':
                    self.stdout.write(
                        self.style.WARNING(f'  ❌ Платеж {payment.yookassa_payment_id} был отменен')
                    )

                    if not dry_run:
                        payment.status = 'canceled'
                        payment.save()

                    updated_count += 1
                    canceled_count += 1

                elif current_status in ['pending', 'waiting_for_capture']:
                    self.stdout.write(f'  ⏳ Платеж {payment.yookassa_payment_id} еще в обработке')

                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ❓ Неизвестный статус платежа: {current_status}')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Ошибка при проверке платежа {payment.yookassa_payment_id}: {e}')
                )
                error_count += 1

        # Выводим итоговую статистику
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:'))
        self.stdout.write(f'  🔄 Обновлено платежей: {updated_count}')
        self.stdout.write(f'  ✅ Успешно оплаченных: {succeeded_count}')
        self.stdout.write(f'  ❌ Отмененных: {canceled_count}')
        self.stdout.write(f'  ⚠️ Ошибок: {error_count}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n🔍 Это был предварительный просмотр. Запустите без --dry-run для применения изменений.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Проверка завершена успешно!')
            )
