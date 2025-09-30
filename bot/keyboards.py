from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from datetime import datetime, timedelta
from calendar import month_name
import locale

# Установим русскую локаль для названий месяцев
try:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')
    except:
        pass  # Если не удается установить русскую локаль


main_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("👥 Мои профили", callback_data="profiles_menu")
btn2 = InlineKeyboardButton("💳 Оплатить занятия", callback_data="start_payment")
btn3 = InlineKeyboardButton("📊 История платежей", callback_data="payment_history")
main_markup.add(btn1).add(btn2).add(btn3)


# Клавиатуры для регистрации
education_choice_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("🏫 Школа", callback_data="education_school")
btn2 = InlineKeyboardButton("🎓 ВУЗ", callback_data="education_university")
education_choice_markup.add(btn1, btn2)

university_courses_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("1 курс", callback_data="course_1")
btn2 = InlineKeyboardButton("2 курс", callback_data="course_2")
btn3 = InlineKeyboardButton("3 курс", callback_data="course_3")
btn4 = InlineKeyboardButton("4 курс", callback_data="course_4")
btn5 = InlineKeyboardButton("5 курс", callback_data="course_5")
btn6 = InlineKeyboardButton("6 курс", callback_data="course_6")
university_courses_markup.add(btn1, btn2, btn3).add(btn4, btn5, btn6)

school_classes_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("5 класс", callback_data="class_5")
btn2 = InlineKeyboardButton("6 класс", callback_data="class_6")
btn3 = InlineKeyboardButton("7 класс", callback_data="class_7")
btn4 = InlineKeyboardButton("8 класс", callback_data="class_8")
btn5 = InlineKeyboardButton("9 класс (ОГЭ)", callback_data="class_9")
btn6 = InlineKeyboardButton("10 класс", callback_data="class_10")
btn7 = InlineKeyboardButton("11 класс (ЕГЭ)", callback_data="class_11")
school_classes_markup.add(btn1, btn2, btn3).add(btn4, btn5).add(btn6, btn7)

UNIVERSAL_BUTTONS = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("⬅️ Назад ⬅️", callback_data="main_menu")
UNIVERSAL_BUTTONS.add(btn1)

ADMIN_MARKUP = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("👥 Просмотр оплаты учеников", url="https://fundamentally116.store/bot/payment-info/")
btn2 = InlineKeyboardButton("💵 Отметить оплату ученика", callback_data="mark_student_payment")
ADMIN_MARKUP.add(btn1).add(btn2)

# Названия месяцев на русском языке (первые 3 буквы)
MONTH_NAMES = {
    1: "Янв", 2: "Фев", 3: "Мар", 4: "Апр",
    5: "Май", 6: "Июн", 7: "Июл", 8: "Авг",
    9: "Сен", 10: "Окт", 11: "Ноя", 12: "Дек"
}

def generate_students_pagination_keyboard(page=1, students_per_page=8):
    """
    Генерирует клавиатуру с пагинацией учеников
    """
    markup = InlineKeyboardMarkup()
    from bot.models import User
    
    # Получаем всех учеников (не админов)
    students = User.objects.filter(is_admin=False)
    total_students = students.count()
    total_pages = (total_students + students_per_page - 1) // students_per_page
    
    # Получаем учеников для текущей страницы
    start_idx = (page - 1) * students_per_page
    end_idx = start_idx + students_per_page
    current_students = students[start_idx:end_idx]
    
    # Добавляем кнопки с учениками
    for student in current_students:
        button_text = student.full_name or f"ID: {student.telegram_id}"
        callback_data = f"select_student_{student.telegram_id}"
        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Добавляем кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"students_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"students_page_{page+1}"))
    if nav_buttons:
        markup.add(*nav_buttons)
    
    # Добавляем кнопку "Назад"
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu"))
    
    return markup

def generate_admin_payment_method_keyboard(student_id):
    """
    Генерирует клавиатуру выбора способа оплаты для админа
    """
    markup = InlineKeyboardMarkup()
    
    # Кнопка для оплаты за конкретный месяц
    month_payment_btn = InlineKeyboardButton("📅 Оплатить за месяц", callback_data=f"admin_month_payment_{student_id}")
    
    # Кнопка для зачисления на баланс
    balance_payment_btn = InlineKeyboardButton("💰 Зачислить на баланс", callback_data=f"admin_balance_payment_{student_id}")
    
    # Кнопка назад к списку учеников
    back_btn = InlineKeyboardButton("⬅️ Назад к списку", callback_data="mark_student_payment")
    
    markup.add(month_payment_btn).add(balance_payment_btn).add(back_btn)
    
    return markup

def generate_admin_payment_months_keyboard(student_id):
    """
    Генерирует клавиатуру с месяцами для админской отметки оплаты
    """
    markup = InlineKeyboardMarkup()
    
    # Проверяем, что student_id не пустой и не является служебным словом
    if not student_id or str(student_id).strip() in ['student', 'admin', 'user']:
        return markup
    
    # Очищаем student_id от пробелов
    student_id = str(student_id).strip()
    
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    buttons = []
    
    # Генерируем 12 месяцев начиная с текущего
    for i in range(12):
        month = ((current_month - 1 + i) % 12) + 1
        year = current_year + ((current_month + i - 1) // 12)
        
        month_name = MONTH_NAMES[month]
        button_text = f"{month_name} {year}"
        callback_data = f"admin_mark_payment_{student_id}_{month}_{year}"
        
        buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Размещаем кнопки по 3 в ряд
    for i in range(0, len(buttons), 3):
        row_buttons = buttons[i:i+3]
        markup.add(*row_buttons)
    
    # Кнопка назад к списку учеников
    back_btn = InlineKeyboardButton("⬅️ Назад к списку учеников", callback_data="mark_student_payment")
    markup.add(back_btn)
    
    return markup

def generate_payment_method_keyboard():
    """Генерирует клавиатуру выбора способа оплаты"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("💳 Оплатить через ЮKassa", callback_data="pay_with_yookassa")
    btn2 = InlineKeyboardButton("💰 Оплатить с баланса", callback_data="pay_with_balance")
    btn3 = InlineKeyboardButton("⬅️ Назад", callback_data="payment_menu")
    
    markup.add(btn1).add(btn2).add(btn3)
    
    return markup

def generate_payment_menu_keyboard():
    """Генерирует клавиатуру меню оплаты"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("💳 Оплатить занятия", callback_data="start_payment")
    btn2 = InlineKeyboardButton("📊 История платежей", callback_data="payment_history")
    btn3 = InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    
    markup.add(btn1).add(btn2).add(btn3)
    
    return markup

def generate_balance_payment_months_keyboard():
    """
    Генерирует клавиатуру с месяцами для оплаты с баланса
    Логика: показываем 12 месяцев начиная с текущего месяца.
    """
    markup = InlineKeyboardMarkup()
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    buttons = []
    
    # Генерируем 12 месяцев начиная с текущего
    for i in range(12):
        month = ((current_month - 1 + i) % 12) + 1
        year = current_year + ((current_month + i - 1) // 12)
        
        month_name = MONTH_NAMES[month]
        button_text = f"{month_name} {year}"
        callback_data = f"pay_balance_month_{month}_{year}"
        
        buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Размещаем кнопки по 3 в ряд
    for i in range(0, len(buttons), 3):
        row_buttons = buttons[i:i+3]
        markup.add(*row_buttons)
    
    # Кнопка назад
    back_btn = InlineKeyboardButton("⬅️ Назад", callback_data="start_payment")
    markup.add(back_btn)
    
    return markup

def generate_payment_months_keyboard():
    """
    Генерирует клавиатуру с 12 месяцами для выбора оплаты.
    Логика: показываем 12 месяцев начиная с текущего месяца.
    """
    markup = InlineKeyboardMarkup()
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    buttons = []
    
    # Генерируем 12 месяцев начиная с текущего
    for i in range(12):
        month = ((current_month - 1 + i) % 12) + 1
        year = current_year + ((current_month + i - 1) // 12)
        
        month_name = MONTH_NAMES[month]
        button_text = f"{month_name} {year}"
        callback_data = f"pay_month_{month}_{year}"
        
        buttons.append(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Размещаем кнопки по 3 в ряд
    for i in range(0, len(buttons), 3):
        row_buttons = buttons[i:i+3]
        markup.add(*row_buttons)
    
    # Кнопка назад
    back_btn = InlineKeyboardButton("⬅️ Назад", callback_data="payment_menu")
    markup.add(back_btn)
    
    return markup



def generate_payment_confirmation_keyboard(month, year):
    """Генерирует клавиатуру подтверждения оплаты"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_payment_{month}_{year}")
    btn2 = InlineKeyboardButton("❌ Отменить", callback_data="start_payment")
    
    markup.add(btn1).add(btn2)
    
    return markup

def generate_check_payment_keyboard(payment_id, month, year):
    """Генерирует клавиатуру для проверки оплаты"""
    markup = InlineKeyboardMarkup()
    
    # Кнопка для перехода к оплате
    pay_btn = InlineKeyboardButton("💳 Перейти к оплате", url=f"https://yoomoney.ru/checkout/payments/v2/contract?orderId={payment_id}")
    
    # Кнопка для проверки оплаты
    check_btn = InlineKeyboardButton("🔍 Проверить оплату", callback_data=f"check_payment_{payment_id}_{month}_{year}")
    
    # Кнопка назад
    back_btn = InlineKeyboardButton("⬅️ Назад", callback_data="payment_menu")
    
    markup.add(pay_btn).add(check_btn).add(back_btn)
    
    return markup

def generate_student_info_keyboard(student_id):
    """
    Генерирует клавиатуру с информацией об ученике и его оплатах
    """
    markup = InlineKeyboardMarkup()
    
    # Проверяем, что student_id не пустой и не является служебным словом
    if not student_id or str(student_id).strip() in ['student', 'admin', 'user']:
        return markup
    
    # Очищаем student_id от пробелов
    student_id = str(student_id).strip()
    
    # Кнопка для отметки оплаты
    mark_payment_btn = InlineKeyboardButton("💵 Отметить оплату", callback_data=f"mark_payment_for_student_{student_id}")
    
    # Кнопка для просмотра истории оплат
    history_btn = InlineKeyboardButton("📊 История оплат", callback_data=f"view_payment_history_{student_id}")
    
    # Кнопка назад к списку учеников
    back_btn = InlineKeyboardButton("⬅️ Назад к списку", callback_data="view_students")
    
    markup.add(mark_payment_btn).add(history_btn).add(back_btn)
    
    return markup

def generate_payment_history_keyboard(student_id):
    """
    Генерирует клавиатуру для просмотра истории оплат ученика
    """
    markup = InlineKeyboardMarkup()
    
    # Проверяем, что student_id не пустой и не является служебным словом
    if not student_id or str(student_id).strip() in ['student', 'admin', 'user']:
        return markup
    
    # Очищаем student_id от пробелов
    student_id = str(student_id).strip()
    
    # Кнопка назад к информации об ученике
    back_btn = InlineKeyboardButton("⬅️ Назад к ученику", callback_data=f"select_student_{student_id}")
    
    markup.add(back_btn)
    
    return markup


# Клавиатуры для управления профилями
def generate_profiles_menu_keyboard():
    """Генерирует клавиатуру меню профилей"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("👥 Мои профили", callback_data="view_profiles")
    btn2 = InlineKeyboardButton("➕ Создать профиль", callback_data="create_profile")
    btn3 = InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")
    
    markup.add(btn1).add(btn2).add(btn3)
    
    return markup


def generate_profiles_list_keyboard(profiles):
    """Генерирует клавиатуру со списком профилей"""
    markup = InlineKeyboardMarkup()
    
    for profile in profiles:
        # Показываем активный профиль с отметкой
        status_icon = "✅" if profile.is_active else "⏸️"
        button_text = f"{status_icon} {profile.profile_name}"
        callback_data = f"select_profile_{profile.id}"
        markup.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    
    # Кнопка для создания нового профиля
    markup.add(InlineKeyboardButton("➕ Создать новый профиль", callback_data="create_profile"))
    
    # Кнопка назад
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="main_menu"))
    
    return markup


def generate_profile_management_keyboard(profile_id):
    """Генерирует клавиатуру управления конкретным профилем"""
    markup = InlineKeyboardMarkup()
    
    # Кнопка для переключения на профиль (если не активен)
    switch_btn = InlineKeyboardButton("🔄 Переключиться", callback_data=f"switch_to_profile_{profile_id}")
    
    # Кнопка для изменения данных профиля
    edit_data_btn = InlineKeyboardButton("✏️ Изменить данные", callback_data=f"edit_profile_data_{profile_id}")
    
    # Кнопка назад к списку профилей
    back_btn = InlineKeyboardButton("⬅️ Назад к профилям", callback_data="view_profiles")
    
    markup.add(switch_btn).add(edit_data_btn).add(back_btn)
    
    return markup


def generate_profile_data_management_keyboard(profile_id):
    """Генерирует клавиатуру управления данными профиля"""
    markup = InlineKeyboardMarkup()
    
    # Кнопка для редактирования профиля
    edit_btn = InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_profile_{profile_id}")
    
    # Кнопка для удаления профиля
    delete_btn = InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_profile_{profile_id}")
    
    # Кнопка назад к управлению профилем
    back_btn = InlineKeyboardButton("⬅️ Назад", callback_data=f"select_profile_{profile_id}")
    
    markup.add(edit_btn).add(delete_btn).add(back_btn)
    
    return markup


def generate_profile_creation_keyboard():
    """Генерирует клавиатуру для создания профиля"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("🏫 Школа", callback_data="profile_education_school")
    btn2 = InlineKeyboardButton("🎓 ВУЗ", callback_data="profile_education_university")
    markup.add(btn1, btn2)
    
    # Кнопка назад
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="profiles_menu"))
    
    return markup


def generate_profile_university_courses_keyboard():
    """Генерирует клавиатуру курсов для профиля"""
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("1 курс", callback_data="profile_course_1")
    btn2 = InlineKeyboardButton("2 курс", callback_data="profile_course_2")
    btn3 = InlineKeyboardButton("3 курс", callback_data="profile_course_3")
    btn4 = InlineKeyboardButton("4 курс", callback_data="profile_course_4")
    btn5 = InlineKeyboardButton("5 курс", callback_data="profile_course_5")
    btn6 = InlineKeyboardButton("6 курс", callback_data="profile_course_6")
    markup.add(btn1, btn2, btn3).add(btn4, btn5, btn6)
    
    # Кнопка назад
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="create_profile"))
    
    return markup


def generate_profile_school_classes_keyboard():
    """Генерирует клавиатуру классов для профиля"""
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("5 класс", callback_data="profile_class_5")
    btn2 = InlineKeyboardButton("6 класс", callback_data="profile_class_6")
    btn3 = InlineKeyboardButton("7 класс", callback_data="profile_class_7")
    btn4 = InlineKeyboardButton("8 класс", callback_data="profile_class_8")
    btn5 = InlineKeyboardButton("9 класс (ОГЭ)", callback_data="profile_class_9")
    btn6 = InlineKeyboardButton("10 класс", callback_data="profile_class_10")
    btn7 = InlineKeyboardButton("11 класс (ЕГЭ)", callback_data="profile_class_11")
    markup.add(btn1, btn2, btn3).add(btn4, btn5).add(btn6, btn7)
    
    # Кнопка назад
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data="create_profile"))
    
    return markup


def generate_profile_confirmation_keyboard():
    """Генерирует клавиатуру подтверждения создания профиля"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("✅ Создать профиль", callback_data="confirm_profile_creation")
    btn2 = InlineKeyboardButton("❌ Отменить", callback_data="profiles_menu")
    
    markup.add(btn1).add(btn2)
    
    return markup


def generate_profile_deletion_confirmation_keyboard(profile_id):
    """Генерирует клавиатуру первого подтверждения удаления профиля"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("✅ Да, я уверен", callback_data=f"confirm_delete_profile_{profile_id}")
    btn2 = InlineKeyboardButton("❌ Отменить", callback_data=f"select_profile_{profile_id}")
    
    markup.add(btn1).add(btn2)
    
    return markup


def generate_profile_deletion_final_confirmation_keyboard(profile_id):
    """Генерирует клавиатуру финального подтверждения удаления профиля"""
    markup = InlineKeyboardMarkup()
    
    btn1 = InlineKeyboardButton("🚨 УДАЛИТЬ НАВСЕГДА", callback_data=f"final_delete_profile_{profile_id}")
    btn2 = InlineKeyboardButton("❌ Отменить", callback_data=f"select_profile_{profile_id}")
    
    markup.add(btn1).add(btn2)
    
    return markup
