from django import forms

from .models import Task, TaskFile, TaskImage


class TaskForm(forms.ModelForm):
    """Форма создания задания с возможностью загрузки файлов и изображений."""

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "answer",
            "group",
            "lesson",
        ]


class ComposeTaskForm(forms.ModelForm):
    """Форма конструктора комплексного задания: выбираем подзадания."""

    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        required=True,
        widget=forms.SelectMultiple(attrs={"size": 12})
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "group",
            "lesson",
        ]


class StudentAnswerForm(forms.Form):
    """Форма ответа ученика на задание (MVP: текстовый ответ)."""

    answer_text = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Ваш ответ..."})
    )


