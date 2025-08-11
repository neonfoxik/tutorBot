from datetime import date, datetime
from dateutil.relativedelta import relativedelta


def get_current_academic_year():
    """Возвращает текущий учебный год в формате '2024-2025'"""
    today = date.today()
    
    # Если сейчас август-декабрь, то это начало нового учебного года
    if today.month >= 8:
        return f"{today.year}-{today.year + 1}"
    else:
        # Если январь-июль, то это продолжение предыдущего учебного года
        return f"{today.year - 1}-{today.year}"


def get_payment_months(months_back=12):
    """Возвращает список месяцев для оплаты (с прошлого месяца назад)"""
    today = date.today()
    months = []
    
    # Начинаем с прошлого месяца
    start_month = today - relativedelta(months=1)
    
    for i in range(months_back):
        month_date = start_month - relativedelta(months=i)
        months.append(month_date)
    
    return months


def get_month_display_name(month_date):
    """Возвращает название месяца на русском языке"""
    month_names = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    return month_names[month_date.month]


def get_academic_year_for_month(month_date):
    """Определяет учебный год для указанного месяца"""
    # Если месяц август-декабрь, то это начало нового учебного года
    if month_date.month >= 8:
        return f"{month_date.year}-{month_date.year + 1}"
    else:
        # Если январь-июль, то это продолжение предыдущего учебного года
        return f"{month_date.year - 1}-{month_date.year}"


def format_month_key(month_date):
    """Форматирует месяц для использования в callback_data"""
    return f"{month_date.year}_{month_date.month:02d}"


def parse_month_key(month_key):
    """Парсит month_key обратно в дату"""
    year, month = month_key.split('_')
    return date(int(year), int(month), 1)


def is_month_paid(user, month_date):
    """Проверяет, оплачен ли указанный месяц пользователем"""
    try:
        from bot.models import Payment
        
        academic_year = get_academic_year_for_month(month_date)
        
        try:
            payment = Payment.objects.get(
                user=user,
                payment_month=month_date,
                academic_year=academic_year,
                status__in=[Payment.Status.SUCCEEDED, Payment.Status.MANUAL]
            )
            return True
        except Payment.DoesNotExist:
            return False
        except Exception as e:
            print(f"Ошибка при проверке платежа: {e}")
            return False
            
    except Exception as e:
        print(f"Ошибка в is_month_paid: {e}")
        return False


def get_month_status(user, month_date):
    """Возвращает статус месяца для пользователя"""
    try:
        from bot.models import Payment
        
        academic_year = get_academic_year_for_month(month_date)
        
        try:
            payment = Payment.objects.get(
                user=user,
                payment_month=month_date,
                academic_year=academic_year
            )
            return payment.status
        except Payment.DoesNotExist:
            return None
        except Exception as e:
            print(f"Ошибка при получении статуса платежа: {e}")
            return None
            
    except Exception as e:
        print(f"Ошибка в get_month_status: {e}")
        return None


def get_payment_amount_for_month(month_date):
    """Возвращает сумму оплаты для указанного месяца"""
    # Здесь можно добавить логику расчета стоимости в зависимости от месяца
    # Пока возвращаем фиксированную сумму
    return 1000.00 