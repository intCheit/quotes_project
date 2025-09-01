import random

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from .forms import QuoteForm, CustomUserCreationForm
from .models import Quote, QuoteVote


def random_quote(request):
    quotes = list(Quote.objects.all())
    if not quotes:
        return render(request, 'quotes/quote.html', {'quote': None})

    # Случайный выбор с весом
    total_weight = sum(q.weight for q in quotes)
    r = random.uniform(0, total_weight)
    upto = 0
    for q in quotes:
        if upto + q.weight >= r:
            selected = q
            break
        upto += q.weight

    # Увеличиваем просмотры
    selected.views += 1
    selected.save()

    # Проверяем, голосовал ли текущий пользователь
    user_vote = None
    if request.user.is_authenticated:
        try:
            vote_obj = QuoteVote.objects.get(user=request.user, quote=selected)
            user_vote = vote_obj.vote_type
        except QuoteVote.DoesNotExist:
            pass

    return render(request, 'quotes/quote.html', {
        'quote': selected,
        'user_vote': user_vote,
    })


@login_required
def vote(request, quote_id, vote_type):
    quote = get_object_or_404(Quote, id=quote_id)

    if vote_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Неверный тип голосования'}, status=400)

    try:
        vote_obj, created = QuoteVote.objects.get_or_create(
            user=request.user,
            quote=quote,
            defaults={'vote_type': vote_type}
        )
        if not created:
            if vote_obj.vote_type == vote_type:
                return JsonResponse({'error': 'Вы уже голосовали этим способом'}, status=400)
            else:
                # меняем голос
                if vote_obj.vote_type == 'like':
                    quote.likes -= 1
                    quote.dislikes += 1
                else:
                    quote.dislikes -= 1
                    quote.likes += 1
                vote_obj.vote_type = vote_type
                vote_obj.save()
        else:
            # новый голос
            if vote_type == 'like':
                quote.likes += 1
            else:
                quote.dislikes += 1
        quote.save()
        return JsonResponse({'likes': quote.likes, 'dislikes': quote.dislikes})
    except IntegrityError:
        return JsonResponse({'error': 'Ошибка при сохранении голосования'}, status=400)


def top_quotes(request):
    quotes = Quote.objects.order_by('-likes')[:10]
    return render(request, 'quotes/top_quotes.html', {'quotes': quotes})


def add_quote(request):
    if request.method == 'POST':
        form = QuoteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('random_quote')
    else:
        form = QuoteForm()
    return render(request, 'quotes/add_quote.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'quotes/register.html', {'form': form})
