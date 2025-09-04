from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Quote


class QuoteForm(forms.ModelForm):
    """
    Форма для добавления цитаты с полями текста, источника, веса и
    типа источника.
    """
    TYPE_CHOICES = (
        ('film', 'Фильм'),
        ('book', 'Книга'),
        ('game', 'Игра'),
        ('series', 'Сериал'),
        ('comic', 'Комикс'),
    )

    type_of_source = forms.ChoiceField(
        choices=TYPE_CHOICES,
        label="Тип источника",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    source = forms.CharField(
        label='Источник (фильм, книга и т.д.) '
              '(в формате "Произведение (год выпуска)")',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Quote
        fields = ['text', 'source', 'weight', 'type_of_source']

    movie_link = forms.URLField(
        label="Ссылка на произведение (необязательно)",
        required=False,
        widget=forms.URLInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'https://...'
            }
        )
    )

    def clean(self):
        """
        Проверяет, чтобы для одного источника не было более трёх цитат.
        """
        cleaned_data = super().clean()
        source = cleaned_data.get("source")
        if source and Quote.objects.filter(source=source).count() >= 3:
            raise forms.ValidationError(
                "Упс, вас уже опередили. Для данного произведения добавлено "
                "максимальное количество цитат."
            )
        return cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """
    Кастомная форма регистрации пользователя с переопределением полей
    username, password1 и password2.
    """
    username = forms.CharField(
        label="Логин",
        max_length=150,
        help_text=_(
            "Обязательное поле. До 150 символов. Используйте буквы, цифры "
            "и @/./+/-/_ только."
        )
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput,
        help_text=_(
            "Пароль должен содержать минимум 8 символов, не быть слишком "
            "простым и не полностью состоять из цифр."
        )
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput,
        help_text=_("Введите тот же пароль для подтверждения.")
    )

    class Meta:
        model = User
        fields = ("username",)
