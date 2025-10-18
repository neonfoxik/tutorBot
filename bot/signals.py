from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from bot.models import ComplexHomework, StudentProfile

@receiver(post_save, sender=ComplexHomework)
def assign_student_to_complex_homework(sender, instance, created, **kwargs):
    if created:  # Проверяем, создано ли новое объект
        if instance.group != None and instance.student is None:
            for student in StudentProfile.objects.filter(group=instance.group):
                chw = ComplexHomework.objects.filter(group=instance.group, lesson=instance.lesson).update(student=student)
                chw.save()
        
                    