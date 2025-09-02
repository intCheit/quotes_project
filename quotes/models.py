from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Quote(models.Model):
    """
    Модель цитаты с текстом, источником, типом источника, весом,
    счетчиками просмотров, лайков и дизлайков.
    """
    TYPE_CHOICES = (
        ('film', 'Фильм'),
        ('book', 'Книга'),
        ('game', 'Игра'),
        ('series', 'Сериал'),
        ('comic', 'Комикс'),
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes'
    )

    text = models.TextField(unique=True)
    source = models.CharField(max_length=255)
    type_of_source = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='film'
    )
    weight = models.PositiveIntegerField(default=1)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Проверяет, что для одного источника не больше трёх цитат.
        """
        if (
            Quote.objects
            .filter(source=self.source)
            .exclude(id=self.id)
            .count() >= 3
        ):
            raise ValidationError(
                f"Для источника '{self.source}' уже есть 3 цитаты."
            )

    def __str__(self):
        """
        Возвращает первые 50 символов текста цитаты и источник.
        """
        return f"{self.text[:50]}... ({self.source})"


class QuoteVote(models.Model):
    """
    Модель голосования пользователя за цитату.
    Один пользователь может проголосовать за одну цитату только один раз.
    """
    VOTE_CHOICES = (
        ('like', 'Лайк'),
        ('dislike', 'Дизлайк'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    vote_type = models.CharField(max_length=7, choices=VOTE_CHOICES)

    class Meta:
        unique_together = ('user', 'quote')
