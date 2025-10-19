from datetime import datetime
from django.conf import settings
from telebot.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot
from bot.models import StudentProfile, User, Lesson, ComplexHomework


def education(message: Message):
    """Функция, обрабатывающая команду /education"""
    # Получаем id и User
    user_id = message.chat.id
    user = User.objects.get(telegram_id=user_id)

    # Получаем все профили пользователя
    student_profiles = user.student_profiles

    is_some = True if student_profiles.count() > 1 else False

    # Если профилей > 1, даем пользователю выбрать
    if is_some:
        markup = InlineKeyboardMarkup()
        for student_profile in student_profiles:
            markup.add(InlineKeyboardButton(text=f"{student_profile.profile_name} | {student_profile.class_number}", callback_data=f"education_{student_profile_id}"))

        bot.send_message(
            chat_id=user_id,
            text="Выберите профиль для просмотра",
            reply_markup=markup
        )
    
    else:
        education_show(student_profiles.first().id, message.id, message.chat.id)


def education_show(studentprofile_id, message_id, chat_id):
    """Отображение информации о учебе: Уроки, Домашние Задания"""
    # Получаем профиль ученика
    studentprofile = StudentProfile.objects.get(pk=studentprofile_id)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(text="Уроки", callback_data=f"lessons_{studentprofile_id}"),
        InlineKeyboardButton(text="Домашние задания", callback_data=f"homeworks_{studentprofile_id}")     
    )
    
    bot.send_message(
        chat_id=chat_id,
        text=f"""
📋 Информация о профиле

👩‍🎓 Имя: {studentprofile.profile_name}
""",
        reply_markup=markup
    )


def education_studentprofiles_handler(call: CallbackQuery):
    """Обработчик выбора профила в education()"""
    _, studentprofile_id = call.data.split("_")
    education_show(studentprofile_id, call.message.id, call.message.chat.id)


def education_show_handler(call: CallbackQuery):
    """Обработчик кнопок в education_show()"""
    type_ = call.data.split("_")
    studentprofile = StudentProfile.objects.get(pk=type_[1])
    lessons_markup = False
    homeworks_markup = False

    if type_[0] == "lessons":
        text="К сожалению, у вас нет доступных для просмотра уроков"
        if studentprofile.group is not None:
            lessons = studentprofile.group.lessons
            if lessons is not None:
                lessons_markup = InlineKeyboardMarkup()
                lessons_markup.add(
                    InlineKeyboardButton(text="Прошедшие уроки", callback_data=f"lessons-_past_{studentprofile.id}"),
                    InlineKeyboardButton(text="Будущие уроки", callback_data=f"lessons-_future_{studentprofile.id}")
                )
                text="Выберите какие уроки вы хотите посмотреть"
                

        bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=text,
                reply_markup=lessons_markup if lessons_markup else None
            )    

    else:
        homeworks = ComplexHomework.objects.filter(student=studentprofile, lesson__date__gte=datetime.now().date())
        text = "У вас нет доступных домашних работ"
        if homeworks.exists():
            homeworks_markup = InlineKeyboardMarkup()
            for homework in homeworks:
                homeworks_markup.add(InlineKeyboardButton(text=f"{homework}", url=f"{settings.HOOK if settings.HOOK[-1] == '/' else settings.HOOK+'/'}bot/tasks/{homework.id}/answer/{studentprofile.id}/"))
            text="Вот ваши заданные домашние работы"

        bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.id,
                text=text,
                reply_markup=homeworks_markup if homeworks_markup else None
            )    
        

def show_lessons(call: CallbackQuery):
    """Обработчик кнопок уроков в education_show_handler()"""
    _, time, studentprofile_id = call.data.split()
    studentprofile = StudentProfile.objects.get(pk=studentprofile_id)
    group = studentprofile
    text = "У вас нет доступных уроков"
    markup = False

    if time == "past":
        lessons = Lesson.objects.filter(date__lt=datetime.now().date(), group=group)
    else:
        lessons = Lesson.objects.filter(date__gte=datetime.now().date(), group=group)

    if lessons.exists():
        markup = InlineKeyboardMarkup()
        for lesson in lessons:
            markup.add(InlineKeyboardButton(text=f"{lesson}", callback_data=f"lesson_{lesson.id}"))
        text="Выберите урок для просмотра"

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=text,
        reply_markup = markup if markup else None
    )
