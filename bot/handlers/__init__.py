from .common import show_main_menu, menu_call
from .admin.admin import (
    admin_menu,
    admin_menu_callback,
    handle_view_students,
    handle_students_page,
    handle_select_student,
    handle_view_payment_history,
    handle_mark_payment_for_student,
    handle_admin_payment_method_selection,
    handle_admin_text_input,
    handle_mark_student_payment,
    handle_admin_mark_payment
)
from .registration import start_registration, handle_registration_message, handle_class_choice
from .payments import (
    start_payment,
    payment_method,
    select_payment_method,
    select_payment_month,
    select_balance_payment_month,
    check_payment,
    payment_history,
    notify_payment_success,
    notify_admins_about_payment
)
from .profiles import (
    profiles_menu,
    view_profiles,
    create_profile,
    handle_profile_creation_message,
    handle_profile_class_choice,
    confirm_profile_creation,
    select_profile,
    switch_to_profile,
    edit_profile_data,
    delete_profile,
    confirm_delete_profile,
    final_delete_profile,
    is_user_creating_profile
)
from .student_menu import (
    education,
    education_show,
    education_studentprofiles_handler,
    education_show_handler,
    show_lessons
)