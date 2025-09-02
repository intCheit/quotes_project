from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Quote(models.Model):
    TYPE_CHOICES = (
        ('film', 'Фильм'),
        ('book', 'Книга'),
        ('game', 'Игра'),
        ('series', 'Сериал'),
        ('comic', 'Комикс'),
    )

    text = models.TextField(unique=True)
    source = models.CharField(max_length=255)
    type_of_source = models.CharField(max_length=20, choices=TYPE_CHOICES, default='film')
    weight = models.PositiveIntegerField(default=1)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    dislikes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Ограничение по 3 цитаты на источник
        if Quote.objects.filter(source=self.source).exclude(id=self.id).count() >= 3:
            raise ValidationError(f"Для источника '{self.source}' уже есть 3 цитаты.")

    def __str__(self):
        return f"{self.text[:50]}... ({self.source})"


class QuoteVote(models.Model):
    VOTE_CHOICES = (
        ('like', 'Лайк'),
        ('dislike', 'Дизлайк'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='votes'  # ← добавлено related_name
    )
    vote_type = models.CharField(max_length=7, choices=VOTE_CHOICES)

    class Meta:
        unique_together = ('user', 'quote')
